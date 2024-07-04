# RBR CTD Processing
A python file containing code to process RBR data from a raw .rsk file <br>
A Jupyter Notebook to call the functions, edit as neeeded, and save the processing steps for each cruise. <br>
Example csv files to use along with the code. <br>
<br>
## Steps:
Read in the raw rsk files. <br>
Merge files. <br>
Create metadata dictionary. <br>
Add 6 line header to make a csv to store with the archived data. <br>
Plot track location. <br>
Check for Zero Order Holds. <br>
Check profile plots for spikes.<br>
Make first corrections based on user input for zero order holds and need for despiking. <br>
Create cast variables and format processing plots. <br>
Correct time if needed. <br>
Correct Pressure if needed. <br>
Clip casts.<br>
Filter T, C, P, F. <br>
Shift C, O. <br>
Delete PRessure Reversals. <br>
Drop Variables that are no longer needed. <br>
Bin Average. <br>
Final Edit. <br>
Write File. 


## Also need
The raw rsk file. <br>
Hakai Institute Oxygen conversion package
