import os
import sys
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory

class BaseGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # configure root window
        self.title("Bruker Conversion")
        self.main_frame = ttk.Frame(self, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # create variables
        self.folder_path = tk.StringVar()
        self.avg_project = tk.BooleanVar()
        self.avg_project.set(False)
        self.max_project = tk.BooleanVar()
        self.max_project.set(True)
        self.single_plane = tk.BooleanVar()
        self.single_plane.set(False)
        self.auto_metadata_extraction = tk.BooleanVar()
        self.auto_metadata_extraction.set(True)
        # No microscope type is set by default
        self.microscope_type = None

        # create LUT dictionary and variables
        self.lut_dict = self.create_lut()
        self.channel1_var = tk.StringVar(value='Red')
        self.channel2_var = tk.StringVar(value='Cyan')
        self.channel3_var = tk.StringVar(value='Blue')
        self.channel4_var = tk.StringVar(value='Magenta')

        # file path selection widget
        self.file_path_entry = ttk.Entry(self, textvariable = self.folder_path)
        self.file_path_entry.grid(row = 0, column = 0, padx = 10, sticky = 'W')
        self.file_path_button = ttk.Button(self, text = 'Select folder')
        # self.folder_path.set('/Users/domchom/Documents/GitHub/Bruker_to_ImageJ/tests/test_data')
        self.file_path_button['command'] = self.get_folder_path
        self.file_path_button.grid(row = 0, column = 1, padx = 10, sticky = 'W')

        # create max project button
        self.max_project_button = ttk.Checkbutton(
            self, variable = self.max_project, text = ' MAX Project z-stacks',
            command=lambda: self.update_checkboxes('max') if self.max_project.get() else None
        )
        self.max_project_button.grid(row = 1, column = 0, padx = 10, sticky = 'W')  

        # create avg project button
        self.avg_project_button = ttk.Checkbutton(
            self, variable=self.avg_project, text=' AVG Project z-stacks',
            command=lambda: self.update_checkboxes('avg') if self.avg_project.get() else None
        )
        self.avg_project_button.grid(row = 2, column = 0, padx = 10, sticky = 'W')  

        # create label to explain the checkboxes above
        self.help = ttk.Label(self, text = 'Select none of the above to save full hyperstack')
        self.help.grid(row=3, column=0, columnspan=2, padx=10, sticky='W')
        
        # create single-plane button
        self.single_plane_button = ttk.Checkbutton(
            self, variable=self.single_plane, text=' Must check if data is single plane',
            command=lambda: self.update_checkboxes('single') if self.single_plane.get() else None
        )
        self.single_plane_button.grid(row = 4, column = 0, padx = 10, sticky = 'W')  
        
        # create button to turn off metadata extraction
        self.no_metadata_button = ttk.Checkbutton(self, text=' Extract and save metadata', variable=self.auto_metadata_extraction)
        self.no_metadata_button.grid(row=5, column=0, padx=10, sticky='W')
        
        # create start button
        self.start_button = ttk.Button(self, text = 'Start conversion')
        self.start_button['command'] = self.start_analysis
        self.start_button.grid(row = 9, column = 0, padx = 10, sticky = 'E')

        # create cancel button
        self.cancel_button = ttk.Button(self, text = 'Cancel')
        self.cancel_button['command'] = self.cancel_analysis
        self.cancel_button.grid(row = 9, column = 1, padx = 10, sticky = 'W')
        
        # create button to launch rolling analysis gui
        self.flamingo_button = ttk.Button(self, text = 'Launch flamingo conversion')
        self.flamingo_button['command'] = self.launch_flamingo_conversion
        self.flamingo_button.grid(row = 9, column = 3, padx = 10, sticky = 'W')
        
        # create button to launch rolling analysis gui
        self.olympus_button = ttk.Button(self, text = 'Launch olympus conversion')
        self.olympus_button['command'] = self.launch_olympus_conversion
        self.olympus_button.grid(row = 10, column = 3, padx = 10, sticky = 'W')

        # create LUT selection widgets
        self.channel1_menu = ttk.Combobox(self, textvariable=self.channel1_var, values=list(self.lut_dict.keys()))
        self.channel2_menu = ttk.Combobox(self, textvariable=self.channel2_var, values=list(self.lut_dict.keys()))
        self.channel3_menu = ttk.Combobox(self, textvariable=self.channel3_var, values=list(self.lut_dict.keys()))
        self.channel4_menu = ttk.Combobox(self, textvariable=self.channel4_var, values=list(self.lut_dict.keys()))
        self.channel1_menu.grid(row=0, column=3)
        self.channel2_menu.grid(row=1, column=3)
        self.channel3_menu.grid(row=2, column=3)
        self.channel4_menu.grid(row=3, column=3)

        self.ch1_label = ttk.Label(self, text="Ch1 LUT")
        self.ch2_label = ttk.Label(self, text="Ch2 LUT")
        self.ch3_label = ttk.Label(self, text="Ch3 LUT")
        self.ch4_label = ttk.Label(self, text="Ch4 LUT")
        self.ch1_label.grid(row=0, column=2)
        self.ch2_label.grid(row=1, column=2)
        self.ch3_label.grid(row=2, column=2)
        self.ch4_label.grid(row=3, column=2)

    def update_checkboxes(self, selected):
        # Update the checkboxes based on the selected option
        if selected == 'max':
            self.avg_project.set(0)
            self.single_plane.set(0)
        elif selected == 'avg':
            self.max_project.set(0)
            self.single_plane.set(0)
        elif selected == 'single':
            self.max_project.set(0)
            self.avg_project.set(0)

    def get_folder_path(self):
        self.folder_path.set(askdirectory())
        
    def launch_flamingo_conversion(self):
        self.microscope_type = 'Flamingo'
        self.destroy()
        
    def launch_olympus_conversion(self):
        self.microscope_type = 'Olympus'
        self.destroy()

    def create_lut(self):
        # Define LUTs
        grays = np.tile(np.arange(256, dtype='uint8'), (3, 1))

        red = np.zeros((3, 256), dtype='uint8')
        red[0] = np.arange(256, dtype='uint8')

        green = np.zeros((3, 256), dtype='uint8')
        green[1] = np.arange(256, dtype='uint8')

        blue = np.zeros((3, 256), dtype='uint8')
        blue[2] = np.arange(256, dtype='uint8')

        magenta = np.zeros((3, 256), dtype='uint8')
        magenta[0] = np.arange(256, dtype='uint8')
        magenta[2] = np.arange(256, dtype='uint8')

        cyan = np.zeros((3, 256), dtype='uint8')
        cyan[1] = np.arange(256, dtype='uint8')
        cyan[2] = np.arange(256, dtype='uint8')

        yellow = np.zeros((3, 256), dtype='uint8')
        yellow[0] = np.arange(256, dtype='uint8')
        yellow[1] = np.arange(256, dtype='uint8')
        
        fiji_luts = {
            'Grays': grays,
            'Red': red,
            'Green': green,
            'Blue': blue,
            'Magenta': magenta,
            'Cyan': cyan,
            'Yellow': yellow,
        }
          
        # Load special Fiji LUTs into the dictionary

        # Compute the absolute path to the LUTs directory
        luts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'LUTs'))

        for lut_file in sorted(os.listdir(luts_dir)):
            if lut_file.endswith('.lut'):
                lut_name = lut_file.split('.')[0]
                lut_path = os.path.join(luts_dir, lut_file)
                fiji_luts[lut_name] = self.load_fiji_lut(lut_path)

        return fiji_luts
        
    def load_fiji_lut(self, filepath):
        with open(filepath, 'rb') as f:
            raw = np.frombuffer(f.read(), dtype=np.uint8)

        # If 768 or 800 bytes, assume single LUT and trim header if needed
        if raw.size in [768, 800]:
            lut_data = raw[-768:]  # Trim to last 768 bytes
            r = lut_data[0:256]
            g = lut_data[256:512]
            b = lut_data[512:768]
            return np.stack((r, g, b))

        # If size is larger than 800, assume it's a concatenated or category LUT (like Glasbey or unionjack)
        # We'll try to extract the first RGB triplet only
        if raw.size >= 768 and raw.size % 3 == 0:
            num_colors = raw.size // 3
            r = raw[0:num_colors]
            g = raw[num_colors:2*num_colors]
            b = raw[2*num_colors:3*num_colors]
            max_len = min(256, len(r), len(g), len(b))
            return np.stack((r[:max_len], g[:max_len], b[:max_len]))

    def cancel_analysis(self):
        sys.exit('You have cancelled the analysis')
    
    def start_analysis(self):
        self.folder_path = self.folder_path.get()
        self.max_project = self.max_project.get()
        self.avg_project = self.avg_project.get()
        self.single_plane = self.single_plane.get()
        self.auto_metadata_extraction = self.auto_metadata_extraction.get()
        self.channel1_var = self.lut_dict[self.channel1_var.get()]
        self.channel2_var = self.lut_dict[self.channel2_var.get()]
        self.channel3_var = self.lut_dict[self.channel3_var.get()]
        self.channel4_var = self.lut_dict[self.channel4_var.get()]
        self.microscope_type = 'Bruker'
        
        # destroy the widget
        self.destroy()
        

class FlamingoGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # configure root window
        self.title("Flamingo Conversion")
        self.main_frame = ttk.Frame(self, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.folder_path = tk.StringVar()
        self.avg_project = tk.BooleanVar()
        self.avg_project.set(False)
        self.max_project = tk.BooleanVar()
        self.max_project.set(True)
        self.folder_of_folders = tk.BooleanVar()
        self.folder_of_folders.set(True)
        self.microscope_type = 'Flamingo'

        # create LUT dictionary and variables
        self.lut_dict = self.create_lut()
        self.channel1_var = tk.StringVar(value='Red')
        self.channel2_var = tk.StringVar(value='Cyan')
        self.channel3_var = tk.StringVar(value='Blue')
        self.channel4_var = tk.StringVar(value='Magenta')

        # file path selection widget
        self.file_path_entry = ttk.Entry(self, textvariable = self.folder_path)
        self.file_path_entry.grid(row = 0, column = 0, padx = 10, sticky = 'E')
        self.file_path_button = ttk.Button(self, text = 'Select folder')
        # self.folder_path.set('/Users/domchom/Desktop/lab/test_data_flamingo/20250418_121024_280DCE_c1647SPY_c2_488phall_417SPY_flourg_cell4')
        self.file_path_button['command'] = self.get_folder_path
        self.file_path_button.grid(row = 0, column = 1, padx = 10, sticky = 'W')

        # create max project button
        self.max_project_button = ttk.Checkbutton(
            self, variable = self.max_project, text = ' MAX Project z-stacks',
            command=lambda: self.update_checkboxes('max') if self.max_project.get() else None
        )
        self.max_project_button.grid(row = 1, column = 0, padx = 10, sticky = 'W')  

         # create avg project button
        self.avg_project_button = ttk.Checkbutton(
            self, variable=self.avg_project, text=' AVG Project z-stacks',
            command=lambda: self.update_checkboxes('avg') if self.avg_project.get() else None
        )
        self.avg_project_button.grid(row = 2, column = 0, padx = 10, sticky = 'W')  
        
         # create folder of folders button
        self.folder_of_folders_button = ttk.Checkbutton(
            self, variable = self.folder_of_folders, text = ' Folder of Folders',
            command=lambda: self.update_checkboxes('folder_of_folders') if self.folder_of_folders.get() else None
        )
        self.folder_of_folders_button.grid(row = 4, column = 0, padx = 10, sticky = 'W')  
        
        # create label to explain the checkboxes above
        self.help = ttk.Label(self, text = 'Select none of the above to save full hyperstack')
        self.help.grid(row=3, column=0, columnspan=2, padx=10, sticky='W')

        # create start button
        self.start_button = ttk.Button(self, text = 'Start conversion')
        self.start_button['command'] = self.start_analysis
        self.start_button.grid(row = 9, column = 0, padx = 10, sticky = 'E')

        # create cancel button
        self.cancel_button = ttk.Button(self, text = 'Cancel')
        self.cancel_button['command'] = self.cancel_analysis
        self.cancel_button.grid(row = 9, column = 1, padx = 10, sticky = 'W')
        
        # create label
        # self.help = ttk.Label(self, text = 'Flamingo conversion only works for a single image/movie at a time.\nIt does not currently support a folder containing multiple folders of images/movies')
        # self.help.grid(row=10, column=0, columnspan=4, padx=10, sticky='W')

        # create LUT selection widgets
        self.channel1_menu = ttk.Combobox(self, textvariable=self.channel1_var, values=list(self.lut_dict.keys()))
        self.channel2_menu = ttk.Combobox(self, textvariable=self.channel2_var, values=list(self.lut_dict.keys()))
        self.channel3_menu = ttk.Combobox(self, textvariable=self.channel3_var, values=list(self.lut_dict.keys()))
        self.channel4_menu = ttk.Combobox(self, textvariable=self.channel4_var, values=list(self.lut_dict.keys()))
        self.channel1_menu.grid(row=0, column=3)
        self.channel2_menu.grid(row=1, column=3)
        self.channel3_menu.grid(row=2, column=3)
        self.channel4_menu.grid(row=3, column=3)

        self.ch1_label = ttk.Label(self, text="Ch1 LUT")
        self.ch2_label = ttk.Label(self, text="Ch2 LUT")
        self.ch3_label = ttk.Label(self, text="Ch3 LUT")
        self.ch4_label = ttk.Label(self, text="Ch4 LUT")
        self.ch1_label.grid(row=0, column=2)
        self.ch2_label.grid(row=1, column=2)
        self.ch3_label.grid(row=2, column=2)
        self.ch4_label.grid(row=3, column=2)

    def update_checkboxes(self, selected):
        # Update the checkboxes based on the selected option
        if selected == 'max':
            self.avg_project.set(0)
        elif selected == 'avg':
            self.max_project.set(0)

    def get_folder_path(self):
        self.folder_path.set(askdirectory())

    def create_lut(self):
        # Define LUTs
        grays = np.tile(np.arange(256, dtype='uint8'), (3, 1))

        red = np.zeros((3, 256), dtype='uint8')
        red[0] = np.arange(256, dtype='uint8')

        green = np.zeros((3, 256), dtype='uint8')
        green[1] = np.arange(256, dtype='uint8')

        blue = np.zeros((3, 256), dtype='uint8')
        blue[2] = np.arange(256, dtype='uint8')

        magenta = np.zeros((3, 256), dtype='uint8')
        magenta[0] = np.arange(256, dtype='uint8')
        magenta[2] = np.arange(256, dtype='uint8')

        cyan = np.zeros((3, 256), dtype='uint8')
        cyan[1] = np.arange(256, dtype='uint8')
        cyan[2] = np.arange(256, dtype='uint8')

        yellow = np.zeros((3, 256), dtype='uint8')
        yellow[0] = np.arange(256, dtype='uint8')
        yellow[1] = np.arange(256, dtype='uint8')
        
        # add luts to dictionary
        fiji_luts = {
            'Grays': grays,
            'Red': red,
            'Green': green,
            'Blue': blue,
            'Magenta': magenta,
            'Cyan': cyan,
            'Yellow': yellow,
        }
        
        # Compute the absolute path to the LUTs directory
        luts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'LUTs'))

        for lut_file in sorted(os.listdir(luts_dir)):
            if lut_file.endswith('.lut'):
                lut_name = lut_file.split('.')[0]
                lut_path = os.path.join(luts_dir, lut_file)
                fiji_luts[lut_name] = self.load_fiji_lut(lut_path)

        return fiji_luts
        
    def load_fiji_lut(self, filepath):
        with open(filepath, 'rb') as f:
            raw = np.frombuffer(f.read(), dtype=np.uint8)

        # If 768 or 800 bytes, assume single LUT and trim header if needed
        if raw.size in [768, 800]:
            lut_data = raw[-768:]  # Trim to last 768 bytes
            r = lut_data[0:256]
            g = lut_data[256:512]
            b = lut_data[512:768]
            return np.stack((r, g, b))

        # If size is larger than 800, assume it's a concatenated or category LUT (like Glasbey or unionjack)
        # We'll try to extract the first RGB triplet only
        if raw.size >= 768 and raw.size % 3 == 0:
            num_colors = raw.size // 3
            r = raw[0:num_colors]
            g = raw[num_colors:2*num_colors]
            b = raw[2*num_colors:3*num_colors]
            max_len = min(256, len(r), len(g), len(b))
            return np.stack((r[:max_len], g[:max_len], b[:max_len]))

    def cancel_analysis(self):
        sys.exit('You have cancelled the analysis')
    
    def start_analysis(self):
        self.folder_path = self.folder_path.get()
        self.max_project = self.max_project.get()
        self.avg_project = self.avg_project.get()
        self.folder_of_folders = self.folder_of_folders.get()
        self.channel1_var = self.lut_dict[self.channel1_var.get()]
        self.channel2_var = self.lut_dict[self.channel2_var.get()]
        self.channel3_var = self.lut_dict[self.channel3_var.get()]
        self.channel4_var = self.lut_dict[self.channel4_var.get()]
        self.microscope_type = 'Flamingo'
        
        # destroy the widget
        self.destroy()
        

class OlympusGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # configure root window
        self.title("Olympus Conversion")
        self.main_frame = ttk.Frame(self, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # create variables
        self.folder_path = tk.StringVar()
        self.avg_project = tk.BooleanVar()
        self.avg_project.set(False)
        self.max_project = tk.BooleanVar()
        self.max_project.set(True)
        self.single_plane = tk.BooleanVar()
        self.single_plane.set(False)
        # No microscope type is set by default
        self.microscope_type = 'Olympus'

        # create LUT dictionary and variables
        self.lut_dict = self.create_lut()
        self.channel1_var = tk.StringVar(value='Red')
        self.channel2_var = tk.StringVar(value='Cyan')
        self.channel3_var = tk.StringVar(value='Blue')
        self.channel4_var = tk.StringVar(value='Magenta')

        # file path selection widget
        self.file_path_entry = ttk.Entry(self, textvariable = self.folder_path)
        self.file_path_entry.grid(row = 0, column = 0, padx = 10, sticky = 'W')
        self.file_path_button = ttk.Button(self, text = 'Select folder')
        # self.folder_path.set('/Users/domchom/Desktop/lab/new')
        self.file_path_button['command'] = self.get_folder_path
        self.file_path_button.grid(row = 0, column = 1, padx = 10, sticky = 'W')

        # create max project button
        self.max_project_button = ttk.Checkbutton(
            self, variable = self.max_project, text = ' MAX Project z-stacks',
            command=lambda: self.update_checkboxes('max') if self.max_project.get() else None
        )
        self.max_project_button.grid(row = 1, column = 0, padx = 10, sticky = 'W')  

        # create avg project button
        self.avg_project_button = ttk.Checkbutton(
            self, variable=self.avg_project, text=' AVG Project z-stacks',
            command=lambda: self.update_checkboxes('avg') if self.avg_project.get() else None
        )
        self.avg_project_button.grid(row = 2, column = 0, padx = 10, sticky = 'W')  

        # create label to explain the checkboxes above
        self.help = ttk.Label(self, text = 'Select none of the above to save full hyperstack')
        self.help.grid(row=3, column=0, columnspan=2, padx=10, sticky='W')
        
        # create label to explain the checkboxes above
        self.help2 = ttk.Label(self, text = 'No need to specify single plane data')
        self.help2.grid(row=4, column=0, columnspan=2, padx=10, sticky='W')
        
        # create start button
        self.start_button = ttk.Button(self, text = 'Start conversion')
        self.start_button['command'] = self.start_analysis
        self.start_button.grid(row = 9, column = 0, padx = 10, sticky = 'E')

        # create cancel button
        self.cancel_button = ttk.Button(self, text = 'Cancel')
        self.cancel_button['command'] = self.cancel_analysis
        self.cancel_button.grid(row = 9, column = 1, padx = 10, sticky = 'W')

        # create LUT selection widgets
        self.channel1_menu = ttk.Combobox(self, textvariable=self.channel1_var, values=list(self.lut_dict.keys()))
        self.channel2_menu = ttk.Combobox(self, textvariable=self.channel2_var, values=list(self.lut_dict.keys()))
        self.channel3_menu = ttk.Combobox(self, textvariable=self.channel3_var, values=list(self.lut_dict.keys()))
        self.channel4_menu = ttk.Combobox(self, textvariable=self.channel4_var, values=list(self.lut_dict.keys()))
        self.channel1_menu.grid(row=0, column=3)
        self.channel2_menu.grid(row=1, column=3)
        self.channel3_menu.grid(row=2, column=3)
        self.channel4_menu.grid(row=3, column=3)

        self.ch1_label = ttk.Label(self, text="Ch1 LUT")
        self.ch2_label = ttk.Label(self, text="Ch2 LUT")
        self.ch3_label = ttk.Label(self, text="Ch3 LUT")
        self.ch4_label = ttk.Label(self, text="Ch4 LUT")
        self.ch1_label.grid(row=0, column=2)
        self.ch2_label.grid(row=1, column=2)
        self.ch3_label.grid(row=2, column=2)
        self.ch4_label.grid(row=3, column=2)

    def update_checkboxes(self, selected):
        # Update the checkboxes based on the selected option
        if selected == 'max':
            self.avg_project.set(0)
            self.single_plane.set(0)
        elif selected == 'avg':
            self.max_project.set(0)
            self.single_plane.set(0)
        elif selected == 'single':
            self.max_project.set(0)
            self.avg_project.set(0)

    def get_folder_path(self):
        self.folder_path.set(askdirectory())

    def create_lut(self):
        # Define LUTs
        grays = np.tile(np.arange(256, dtype='uint8'), (3, 1))

        red = np.zeros((3, 256), dtype='uint8')
        red[0] = np.arange(256, dtype='uint8')

        green = np.zeros((3, 256), dtype='uint8')
        green[1] = np.arange(256, dtype='uint8')

        blue = np.zeros((3, 256), dtype='uint8')
        blue[2] = np.arange(256, dtype='uint8')

        magenta = np.zeros((3, 256), dtype='uint8')
        magenta[0] = np.arange(256, dtype='uint8')
        magenta[2] = np.arange(256, dtype='uint8')

        cyan = np.zeros((3, 256), dtype='uint8')
        cyan[1] = np.arange(256, dtype='uint8')
        cyan[2] = np.arange(256, dtype='uint8')

        yellow = np.zeros((3, 256), dtype='uint8')
        yellow[0] = np.arange(256, dtype='uint8')
        yellow[1] = np.arange(256, dtype='uint8')

        fiji_luts = {
            'Grays': grays,
            'Red': red,
            'Green': green,
            'Blue': blue,
            'Magenta': magenta,
            'Cyan': cyan,
            'Yellow': yellow,
        }
          
        # Compute the absolute path to the LUTs directory
        luts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'LUTs'))

        for lut_file in sorted(os.listdir(luts_dir)):
            if lut_file.endswith('.lut'):
                lut_name = lut_file.split('.')[0]
                lut_path = os.path.join(luts_dir, lut_file)
                fiji_luts[lut_name] = self.load_fiji_lut(lut_path)

        return fiji_luts
        
    def load_fiji_lut(self, filepath):
        with open(filepath, 'rb') as f:
            raw = np.frombuffer(f.read(), dtype=np.uint8)

        # If 768 or 800 bytes, assume single LUT and trim header if needed
        if raw.size in [768, 800]:
            lut_data = raw[-768:]  # Trim to last 768 bytes
            r = lut_data[0:256]
            g = lut_data[256:512]
            b = lut_data[512:768]
            return np.stack((r, g, b))

        # If size is larger than 800, assume it's a concatenated or category LUT (like Glasbey or unionjack)
        # We'll try to extract the first RGB triplet only
        if raw.size >= 768 and raw.size % 3 == 0:
            num_colors = raw.size // 3
            r = raw[0:num_colors]
            g = raw[num_colors:2*num_colors]
            b = raw[2*num_colors:3*num_colors]
            max_len = min(256, len(r), len(g), len(b))
            return np.stack((r[:max_len], g[:max_len], b[:max_len]))

    def cancel_analysis(self):
        sys.exit('You have cancelled the analysis')
    
    def start_analysis(self):
        self.folder_path = self.folder_path.get()
        self.max_project = self.max_project.get()
        self.avg_project = self.avg_project.get()
        self.single_plane = self.single_plane.get()
        self.channel1_var = self.lut_dict[self.channel1_var.get()]
        self.channel2_var = self.lut_dict[self.channel2_var.get()]
        self.channel3_var = self.lut_dict[self.channel3_var.get()]
        self.channel4_var = self.lut_dict[self.channel4_var.get()]
        self.microscope_type = 'Olympus'
        
        # destroy the widget
        self.destroy()
        