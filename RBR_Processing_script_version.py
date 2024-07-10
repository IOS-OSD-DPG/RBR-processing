from RBR_CTD_IOS_2024 import *

#  This is how the code is run via the Jupyter Notebook

# Set Parameters

year = "2024"
cruise_number = "017"
# dest_dir = f"C:\\Users\\huntingtons\\Desktop\\RBR_Processing\\CURRENT_PROCESSING\\{year}-{cruise_number}\\Suggested\\"
dest_dir = "C:\\Users\\huntingtons\\\Desktop\\RBR_Processing\\Github_June2024_test\\"
skipcasts = 0
rsk_start_end_times_file = None
rsk_time1, rsk_time2 = [None, None]
rsk_file = dest_dir + "232531_20240206_1745.rsk"  # "232531_20240223_1125.rsk"]
sample_rate = 8
left_lon, right_lon, bot_lat, top_lat = [None, None, None, None]
start_time_correction_file = None
verbose = True
shift_recs_conductivity: int = 2
shift_recs_oxygen = -11
drop_vars_file = "2024_017_vars_to_drop.csv"
processing_report_name = f"{year}-{cruise_number}_RBR_Processing_Report.docx"
# 5 lines of processing comments are added here and included in the write_comments function.  If more lines are needed, adjust the function.
processing_comments1 = "       " + "Cast 18 stopped at 20m and was brought to the surface and re-started."
processing_comments2 = None  # format is "       " + "Your text here"
processing_comments3 = None
processing_comments4 = None
processing_comments5 = None

# Global Variables are listed above already, no need to repeat here
# Create meta data dict

meta_dict = CREATE_META_DICT(dest_dir, rsk_file, year, cruise_number, rsk_time1, rsk_time2)

# First read of rsk without making any corrections

zoh = False
fix_spk = False
fill_action = None
fill_type = None
spk_window = None
spk_std = None
spk_var = None
READ_RSK(dest_dir, year, cruise_number,
         skipcasts, meta_dict, zoh, fill_action,
         fill_type, spk_window, spk_std, spk_var, fix_spk,
         rsk_start_end_times_file, rsk_time1, rsk_time2)
# first steps are just in a cell in the notebook, not wrapped in a function

MERGE_FILES(dest_dir=dest_dir, year=year, cruise_number=cruise_number)
ADD_6LINEHEADER_2(dest_dir, year, cruise_number, output_ext="_CTD_DATA-6linehdr.csv")
plot_track_location(dest_dir, year, cruise_number, left_lon, right_lon, bot_lat, top_lat)
PLOT_PRESSURE_DIFF(dest_dir, year, cruise_number, input_ext='_CTD_DATA-6linehdr.csv')
zoh = check_for_zoh(dest_dir, year, cruise_number, float(meta_dict["Sampling_Interval"]))
print("zoh,", zoh)

# quickly check the profiles and look for spikes

check_profiles(dest_dir, year, cruise_number, name1="Pre_Processing_", name2="Pre_Processing_")

# Make the first corrections

fill_action = "interp"
fill_type = "interpolated value"
spk_window = 11
spk_std = 3
spk_var = "Fluorescence:URU"
input_ext = first_corrections(dest_dir, year, cruise_number,
                              skipcasts, meta_dict, verbose,
                              rsk_file, fill_action, fill_type,
                              spk_window, spk_std, spk_var,
                              rsk_start_end_times_file, rsk_time1, rsk_time2)

# Create cast variables and make first plots

cast, cast_d, cast_u = CREATE_CAST_VARIABLES(
    year, cruise_number, dest_dir, input_ext
)
for cast_i in cast_d.keys():
    have_oxy = True if "Oxygen" in cast_d[cast_i].columns else False
    have_fluor = True if "Fluorescence" in cast_d[cast_i].columns else False

    # if verbose:

    print(f"have_oxy: {have_oxy}, have_fluor: {have_fluor}")
    break
first_plots(year, cruise_number, dest_dir, input_ext)

# Start data processing, correct pressure and time if needed, clip casts

pd_correction_value = 0
limit_pressure_change = 0.02

# correct time
if start_time_correction_file is not None:
    cast_correct_t, cast_d_correct_t, cast_u_correct_t = CORRECT_TIME_OFFSET(
        dest_dir, cast, cast_d, cast_u, metadata_dict, start_time_correction_file
    )
    if verbose:
        print("Time offset(s) corrected")
else:
    cast_correct_t, cast_d_correct_t, cast_u_correct_t = cast, cast_d, cast_u
# correct pressure depth
if pd_correction_value != 0:
    cast_pc, cast_d_pc, cast_u_pc = CALIB(
        cast_correct_t, cast_d_correct_t, cast_u_correct_t, meta_dict,
        pd_correction_value
    )  # 0 if no neg pressures
    if verbose:
        print(
            "The following correction value has been applied to Pressure and Depth:",
            pd_correction_value,
            sep="\n",
        )
else:
    cast_pc, cast_d_pc, cast_u_pc = cast_correct_t, cast_d_correct_t, cast_u_correct_t

# Clip casts
cast_d_clip = CLIP_CAST(
    cast_d_pc, meta_dict, limit_pressure_change=0.02, cast_direction="down"
)
cast_u_clip = CLIP_CAST(
    cast_u_pc, meta_dict, limit_pressure_change=-0.02, cast_direction="up"
)

plot_clip(cast_d_clip, cast_d_pc, dest_dir)

if verbose:
    print("Casts clipped")

# Filter and Shift the data, confirm parameters here, convert oxygen

filter_type = 1  # Moving average, 0 for FIR
sample_rate = 8  # from rsk file, could be 6Hz
time_constant = 1 / 8
window_width = 3

# Filter
sample_rate = int(np.round(1 / float(meta_dict["Sampling_Interval"])))
cast_d_filtered, cast_u_filtered = FILTER(
    cast_d_clip,
    cast_u_clip,
    meta_dict,
    have_fluor,
    window_width,
    sample_rate=sample_rate,
    time_constant=float(meta_dict["Sampling_Interval"]),
    filter_type=filter_type,
)  # n = 5 should be good.

# Plot the filtered data
plot_filter(
    cast_d_filtered, cast_u_filtered, cast_d_clip, cast_u_clip, dest_dir, have_fluor
)

if verbose:
    print(
        f"Casts filtered, assuming a sample rate of {sample_rate} records per second"
    )
# Shift C
cast_d_shift_c, cast_u_shift_c = SHIFT_CONDUCTIVITY(
    cast_d_filtered,
    cast_u_filtered,
    metadata_dict=meta_dict,
    shifted_scan_number=shift_recs_conductivity,
)

plot_shift_c(
    cast_d_shift_c, cast_u_shift_c, cast_d_filtered, cast_u_filtered, dest_dir
)

if verbose:
    print(f"Conductivity shifted {shift_recs_conductivity} scans")

# Shift O

if have_oxy:

    cast_d_shift_o, cast_u_shift_o = SHIFT_OXYGEN(
        cast_d_shift_c,
        cast_u_shift_c,
        metadata_dict=meta_dict,
        shifted_scan_number=shift_recs_oxygen,
    )

    plot_shift_o(
        cast_d_shift_o, cast_u_shift_o, cast_d_shift_c, cast_u_shift_c, dest_dir
    )

    if verbose:
        print(f"Oxygen shifted {shift_recs_oxygen} scans")

    # Derive Oxygen concentration
    cast_d_o_conc, cast_u_o_conc = DERIVE_OXYGEN_CONCENTRATION(
        cast_d_shift_o, cast_u_shift_o, meta_dict
    )

    if verbose:
        print("Oxygen concentration derived from oxygen saturation")
else:
    # Rename the variables
    cast_d_shift_o, cast_u_shift_o = cast_d_shift_c, cast_u_shift_c
    cast_d_o_conc, cast_u_o_conc = cast_d_shift_c, cast_u_shift_c

# Delete swells, drop variables, Bin Average

# delete
cast_d_wakeeffect, cast_u_wakeeffect = DELETE_PRESSURE_REVERSAL(
    cast_d_o_conc, cast_u_o_conc, metadata_dict=meta_dict
)

if verbose:
    print("Deleted pressure change reversals")

# Plot before and after comparisons of the delete step
plot_delete(cast_d_wakeeffect, cast_d_o_conc, dest_dir)

# remove channels
if drop_vars_file is not None:
    cast_d_dropvars = DROP_SELECT_VARS(
        dest_dir, cast_d_wakeeffect, drop_vars_file, meta_dict
    )
    if verbose:
        print("Select variables dropped from casts specified in", drop_vars_file)
else:
    cast_d_dropvars = cast_d_wakeeffect

# Binave

cast_d_binned = BINAVE(
    cast_d_dropvars, metadata_dict=meta_dict
)

figure_dir = os.path.join(dest_dir, "FIG")
if not os.path.exists(figure_dir):
    os.makedirs(figure_dir)

do_ts_plot(
    figure_dir, plot_title="T-S Plot (after bin average)",
    figure_filename="After_BINAVE_T-S.png", cast_d=cast_d_binned
)

if verbose:
    print("Records averaged into equal-width pressure bins")

# Final edits and plots

cast_d_final = FINAL_EDIT(cast_d_binned, meta_dict)
if verbose:
    print("Final edit completed")

plot_processed(cast_d_final, dest_dir)

# Write the files

cast_numbers = list(map(lambda x: int(x.split("cast")[-1]), cast_d_final.keys()))
for i in cast_numbers:
    # # Update have_fluor and have_oxy flags, since it could be different for different casts
    # have_fluor = True if "Fluorescence" in cast_d_final[f"cast{i}"].columns else False
    # have_oxy = True if "Oxygen" in cast_d_final[f"cast{i}"].columns else False
    channel_names = cast_d_final[f"cast{i}"].columns
    # print(channel_names)
    # Call the main header creation function
    main_header(
        dest_dir,
        i,
        meta_dict,
        cast,
        cast_d,
        cast_d_correct_t,
        cast_d_pc,
        cast_d_clip,
        cast_d_filtered,
        cast_d_shift_c,
        cast_d_shift_o,
        cast_d_o_conc,
        cast_d_wakeeffect,
        cast_d_binned,
        cast_d_dropvars,
        cast_d_final,
        channel_names,
        processing_report_name,
        processing_comments1,
        processing_comments2,
        processing_comments3,
        processing_comments4,
        processing_comments5
    )
