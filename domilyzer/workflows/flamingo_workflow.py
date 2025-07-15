import os 
import tqdm

from domilyzer.functions_gui.flamingo_functions import (
    getNumChannelsFlamingo,
    getNumFramesFlamingo,
    getNumIlluminationSidesFlamingo,
    convertImagesToNumpyArraysAndProjectFlamingo,
    mergeNumpyArrayIlluminationSidesFlamingo
)

from domilyzer.functions_gui.general_functions import (
    saveImageJHyperstack
)

def processFlamingoImages(parent_folder_path: str,
                          projection_type: str,
                          processed_images_path: str,
                          imagej_tags: dict,
                          image_folders: list = None
                          ) -> None:
    """
    Process Flamingo images by reading TIF files, generating projections, and saving them as hyperstacks.
    
    Parameters:
    - parent_folder_path (str): Path to the parent folder containing the TIF files.
    - projection_type (str): Type of projection to be used ('max', 'avg', or None).
    - imagej_tags (dict): Tags to be used for saving the images in ImageJ format.
    """
    if image_folders is not None:
        for folder_index in tqdm.tqdm(range(len(image_folders)), desc="Processing movies"):
            folder_name = image_folders[folder_index]
            print('******'*10)
            try:
                print(f'Processing folder: {folder_name}')
                # Get the list of all TIF files in the directory
                folder_path = os.path.join(parent_folder_path, folder_name)
                tif_filenames = [f for f in os.listdir(folder_path) if f.endswith('.tif') and f.startswith('S')]
                # for reference filename structure: S000_t000000_V000_R0000_X000_Y000_C00_I0_D0_P00366
                # S: unsure, t: time point, V: unsure, R: rotation, X: x position, 
                # Y: y position, C: channel, I: illumination side, D: unsure, P: Z-planes

                # Get the number of channels and frames
                num_channels, channel_names = getNumChannelsFlamingo(tif_filenames)
                num_frames = getNumFramesFlamingo(tif_filenames)
                num_illumination_sides = getNumIlluminationSidesFlamingo(tif_filenames)
                print(f"Number of channels: {num_channels}")
                print(f"Number of frames: {num_frames}")
                print(f"Number of illumination sides: {num_illumination_sides}")

                # Read all TIF files and Z-project them (if desired)
                image_arrays = convertImagesToNumpyArraysAndProjectFlamingo(folder_path, tif_filenames, projection_type)

                # Create the final hyperstack that will hold all frames
                final_hyperstack = mergeNumpyArrayIlluminationSidesFlamingo(image_arrays, 
                                                                        tif_filenames, 
                                                                        num_frames, 
                                                                        num_channels, 
                                                                        channel_names, 
                                                                        projection_type
                                                                        )

                # Create output path for the final hyperstack
                name_suffix = 'MAX' if projection_type == 'max' else 'AVG' if projection_type == 'avg' else 'hyperstack'
                hyperstack_output_path = f'{processed_images_path}/{folder_name}_{name_suffix}.tif'

                # Check if the output file already exists
                if os.path.exists(hyperstack_output_path):
                    print(f"Output file {hyperstack_output_path} already exists. Overwriting...")
                    # Remove the existing file
                    os.remove(hyperstack_output_path)

                # Create axes metadata for the hyperstack
                imageJ_axes = 'TCYX' if projection_type == 'max' or projection_type == 'avg' else 'TZCYX'
                    
                # Calculate the size of the final hyperstack in bytes, and warn if it's too large
                # 1 GB = 1024^3 bytes
                final_hyperstack_size = final_hyperstack.nbytes
                if final_hyperstack_size > (1024 ** 3):
                    print(f"Warning: The final hyperstack is {final_hyperstack_size / (1024 ** 3):.2f} GB. It may take a while to save.")
                    print("Consider splitting the data into smaller chunks.")
                    
                print(f"Saving hyperstack to {hyperstack_output_path}...")

                # Save the hyperstack
                saveImageJHyperstack(final_hyperstack, 
                                imageJ_axes,
                                metadata = None, # for now, flamingo data doesn't have metadata
                                image_output_name = hyperstack_output_path, 
                                imagej_tags = imagej_tags
                                ) 

                print(f'Successfully saved hyperstack to {hyperstack_output_path}')
                
            except Exception as e:
                print(f"Error processing {folder_name}!: {e}")
                pass
    else:
        tif_filenames = [f for f in os.listdir(parent_folder_path) if f.endswith('.tif') and f.startswith('S')]
        # for reference filename structure: S000_t000000_V000_R0000_X000_Y000_C00_I0_D0_P00366
        # S: unsure, t: time point, V: unsure, R: rotation, X: x position, 
        # Y: y position, C: channel, I: illumination side, D: unsure, P: Z-planes

        # Get the number of channels and frames
        num_channels, channel_names = getNumChannelsFlamingo(tif_filenames)
        num_frames = getNumFramesFlamingo(tif_filenames)
        num_illumination_sides = getNumIlluminationSidesFlamingo(tif_filenames)
        print(f"Number of channels: {num_channels}")
        print(f"Number of frames: {num_frames}")
        print(f"Number of illumination sides: {num_illumination_sides}")

        # Read all TIF files and Z-project them (if desired)
        image_arrays = convertImagesToNumpyArraysAndProjectFlamingo(parent_folder_path, tif_filenames, projection_type)

        # Create the final hyperstack that will hold all frames
        final_hyperstack = mergeNumpyArrayIlluminationSidesFlamingo(image_arrays, 
                                                                tif_filenames, 
                                                                num_frames, 
                                                                num_channels, 
                                                                channel_names, 
                                                                projection_type
                                                                )

        # Create output path for the final hyperstack
        image_folder = os.path.basename(parent_folder_path)
        name_suffix = 'MAX' if projection_type == 'max' else 'AVG' if projection_type == 'avg' else 'hyperstack'
        hyperstack_output_path = f'{parent_folder_path}/{image_folder}_{name_suffix}.tif'

        # Check if the output file already exists
        if os.path.exists(hyperstack_output_path):
            print(f"Output file {hyperstack_output_path} already exists. Overwriting...")
            # Remove the existing file
            os.remove(hyperstack_output_path)

        # Create axes metadata for the hyperstack
        imageJ_axes = 'TCYX' if projection_type == 'max' or projection_type == 'avg' else 'TZCYX'
            
        # Calculate the size of the final hyperstack in bytes, and warn if it's too large
        # 1 GB = 1024^3 bytes
        final_hyperstack_size = final_hyperstack.nbytes
        if final_hyperstack_size > (1024 ** 3):
            print(f"Warning: The final hyperstack is {final_hyperstack_size / (1024 ** 3):.2f} GB. It may take a while to save.")
            print("Consider splitting the data into smaller chunks.")
            
        print(f"Saving hyperstack to {hyperstack_output_path}...")

        # Save the hyperstack
        saveImageJHyperstack(final_hyperstack, 
                        imageJ_axes,
                        metadata = None, # for now, flamingo data doesn't have metadata
                        image_output_name = hyperstack_output_path, 
                        imagej_tags = imagej_tags
                        ) 

        print(f'Successfully saved hyperstack to {hyperstack_output_path}')