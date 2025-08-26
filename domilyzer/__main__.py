import os
import timeit
import shutil
import numpy as np
from domilyzer.functions_gui.gui import BaseGUI, FlamingoGUI, OlympusGUI
from domilyzer.functions_gui.general_functions import (
    initializeOutputFolders,
    initializeLogFile,
    saveLogFile,
    createImageJMetadataTags,
)
from domilyzer.workflows.bruker_workflow import processBrukerImages
from domilyzer.workflows.olympus_workflow import processOlympusImages
from domilyzer.workflows.flamingo_workflow import processFlamingoImages

def main():
    manual_test = False # Set to True for manual testing purposes, will skip GUI and use test data. Also will not move folders to processed images folder.
    
    if not manual_test:
        # Bruker GUI
        gui = BaseGUI()
        gui.mainloop()
        
        # Get GUI variables
        parent_folder_path = gui.folder_path
        avg_projection = gui.avg_project
        max_projection = gui.max_project
        single_plane = gui.single_plane
        ch1_lut = gui.channel1_var
        ch2_lut = gui.channel2_var
        ch3_lut = gui.channel3_var
        ch4_lut = gui.channel4_var
        microscope_type = gui.microscope_type
        auto_metadata_extract = gui.auto_metadata_extraction
        folder_of_folders = True # set to True because only needed for Flamingo workflow
        
        # If user specifies Flamingo workflow, run Flamingo GUI
        if microscope_type == 'Flamingo':
            gui = FlamingoGUI()
            gui.mainloop()
            
            # Get GUI variables
            parent_folder_path = gui.folder_path
            avg_projection = gui.avg_project
            max_projection = gui.max_project
            ch1_lut = gui.channel1_var
            ch2_lut = gui.channel2_var
            ch3_lut = gui.channel3_var
            ch4_lut = gui.channel4_var
            microscope_type = gui.microscope_type
            folder_of_folders = gui.folder_of_folders
            
        # If user specifies Olympus workflow, run Olympus GUI
        if microscope_type == 'Olympus':
            gui = OlympusGUI()
            gui.mainloop()

            # Get GUI variables
            parent_folder_path = gui.folder_path
            avg_projection = gui.avg_project
            max_projection = gui.max_project
            single_plane = gui.single_plane
            ch1_lut = gui.channel1_var
            ch2_lut = gui.channel2_var
            ch3_lut = gui.channel3_var
            ch4_lut = gui.channel4_var
            microscope_type = gui.microscope_type
            folder_of_folders = True # set to True because only needed for Flamingo workflow
            
    else: 
        # For testing purposes, set the parameters directly
        red = np.zeros((3, 256), dtype='uint8')
        red[0] = np.arange(256, dtype='uint8')

        green = np.zeros((3, 256), dtype='uint8')
        green[1] = np.arange(256, dtype='uint8')

        blue = np.zeros((3, 256), dtype='uint8')
        blue[2] = np.arange(256, dtype='uint8')

        magenta = np.zeros((3, 256), dtype='uint8')
        magenta[0] = np.arange(256, dtype='uint8')
        magenta[2] = np.arange(256, dtype='uint8')
        
        parent_folder_path = 'tests/test_data/olympus'
        #parent_folder_path = '/Users/domchom/Documents/GitHub/domilyzer/tests/test_data/bruker_multiplane'
        #parent_folder_path = '/Users/domchom/Desktop/lab/test_data_flamingo/20250418_133945_280DCE_c1647SPY_c2_488phall_417SPY_flourg_cell6'
        avg_projection = False
        max_projection = True
        single_plane = False
        ch1_lut = red
        ch2_lut = green
        ch3_lut = blue
        ch4_lut = magenta
        microscope_type = 'Olympus' # 'Flamingo' or 'Bruker'
        auto_metadata_extract = True
        
    # Performance tracker
    start_time = timeit.default_timer()

    # Check if neither max nor avg projection are selected, default to saving full hyperstacks
    if not avg_projection and not max_projection:
        print('Neither max nor avg projection selected. Saving full hyperstacks. This might take a while!')
        projection_type = None
    elif max_projection:
        print('Max projection selected. Saving max projections.')
        projection_type = 'max'
    elif avg_projection:
        print('Avg projection selected. Saving avg projections.')
        projection_type = 'avg'
        
    # Create a dictionary of imagej metadata tags, with the LUTs for each channel. Will be used for all workflows.
    imagej_tags = createImageJMetadataTags(LUTs = {'LUTs': [ch1_lut, ch2_lut, ch3_lut, ch4_lut]},
                                           byteorder = '>')
    
    # Get the Bruker image folders
    if folder_of_folders == True or microscope_type != 'Flamingo':
        image_folders = sorted([folder for folder in os.listdir(parent_folder_path) if os.path.isdir(os.path.join(parent_folder_path, folder))])
        if not manual_test:
            processed_images_path, scope_folders_path = initializeOutputFolders(parent_folder_path = parent_folder_path)
            metadata_csv_path = os.path.join(processed_images_path, "!image_metadata.csv")
        else:
            processed_images_path = parent_folder_path
            metadata_csv_path = None
        log_file_path, log_details = initializeLogFile(processed_images_path = processed_images_path)        
    
    # BRUKER WORKFLOW
    if microscope_type == 'Bruker':
        log_details, hyperstack_arrays = processBrukerImages(parent_folder_path = parent_folder_path,
                                           image_folders = image_folders,
                                           processed_images_path = processed_images_path,
                                           metadata_csv_path = metadata_csv_path,
                                           microscope_type = microscope_type,
                                           projection_type = projection_type,
                                           single_plane = single_plane,
                                           auto_metadata_extract = auto_metadata_extract,
                                           test = manual_test,
                                           imagej_tags = imagej_tags,
                                           log_details = log_details
                                           )
                                          
            
    # OLYMPUS WORKFLOW
    elif microscope_type == 'Olympus':
        hyperstack_arrays = processOlympusImages(parent_folder_path=parent_folder_path,
                                                processed_images_path=processed_images_path,
                                                microscope_type=microscope_type,
                                                projection_type=projection_type,
                                                imagej_tags=imagej_tags,
                                                image_folders=image_folders,
                                                test = manual_test
                                                )
                                    
    # FLAMINGO WORKFLOW
    elif microscope_type == 'Flamingo':
        processFlamingoImages(parent_folder_path=parent_folder_path,
                                projection_type=projection_type,
                                processed_images_path=processed_images_path,
                                imagej_tags=imagej_tags,
                                image_folders=image_folders if folder_of_folders else None
                                )
          
    if folder_of_folders == True and manual_test == False: # not doing olympus for testing for now  
        for folder_name in image_folders:
            shutil.move(os.path.join(parent_folder_path, folder_name), os.path.join(scope_folders_path, folder_name))
            # Move all .oif files if they exist to scope_folders
            oif_files = [file for file in os.listdir(parent_folder_path) if file.endswith('.oif')]
            for oif_file in oif_files:
                shutil.move(os.path.join(parent_folder_path, oif_file), os.path.join(scope_folders_path, oif_file))

            end_time = timeit.default_timer()
            log_details["Time Elapsed"] = f"{end_time - start_time:.2f} seconds"
            
            # Save the log file
            saveLogFile(log_file_path, log_details)    
    
    end_time = timeit.default_timer()
    print(f'Time elapsed: {end_time - start_time:.2f} seconds')    
              
if __name__ == '__main__':
    main()

print('Done with script!')
