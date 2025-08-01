import file_handling
import grid_info as grid_i
import user_interface
import sys
from process_input import process_input
from datetime import datetime
import extractor

user_input = user_interface.MainWindow()
if (user_input.cancelled):
    sys.exit(0)

# Check if we're in answer key extraction mode
if user_input.extract_answer_key_mode and user_input.extract_answer_key_image:
    # Create extraction window
    extraction_window = user_input.create_extraction_window()
    
    extraction_window.set_status("Starting answer key extraction...")
    extraction_window.start_progress()
    
    # Extract answer key from the selected image
    form_variant = grid_i.form_150q if user_input.form_variant == user_interface.FormVariantSelection.VARIANT_150_Q else grid_i.form_75q
    files_timestamp = datetime.now().replace(microsecond=0)
    
    try:
        extracted_key_path = extractor.extract_answer_key_from_image(
            user_input.extract_answer_key_image,
            user_input.output_folder,
            user_input.multi_answers_as_f,
            user_input.empty_answers_as_g,
            form_variant,
            files_timestamp,
            user_input.debug_mode
        )
        
        if extracted_key_path:
            extraction_window.set_status(f"✔️ Answer key successfully extracted and saved to:\n{extracted_key_path.name}\n\nYou can now use this file as an answer key for processing other sheets.")
            # Set the extracted key as the keys file for processing
            user_input.keys_file = extracted_key_path
        else:
            extraction_window.set_status("❌ Failed to extract answer key from the selected image.\nPlease check the image quality and try again.")
    except Exception as e:
        extraction_window.set_status(f"❌ Error during answer key extraction:\n{str(e)}")
    
    extraction_window.stop_progress()
    extraction_window.wait_for_close()
    
    if extraction_window.cancelled:
        sys.exit(0)

# Continue with normal processing if there are other images to process
input_folder = user_input.input_folder
image_paths = file_handling.filter_images(
    file_handling.list_file_paths(input_folder))

# If we extracted an answer key, remove that image from processing list
if user_input.extract_answer_key_mode and user_input.extract_answer_key_image:
    image_paths = [path for path in image_paths if path != user_input.extract_answer_key_image]

# Check if there are any images left to process
if len(image_paths) == 0:
    # No images to process, we're done
    sys.exit(0)

output_folder = user_input.output_folder
multi_answers_as_f = user_input.multi_answers_as_f
empty_answers_as_g = user_input.empty_answers_as_g
keys_file = user_input.keys_file
arrangement_file = user_input.arrangement_map
sort_results = user_input.sort_results
output_mcta = user_input.output_mcta
debug_mode_on = user_input.debug_mode
form_variant = grid_i.form_150q if user_input.form_variant == user_interface.FormVariantSelection.VARIANT_150_Q else grid_i.form_75q
progress_tracker = user_input.create_and_pack_progress(maximum=len(image_paths))
files_timestamp = datetime.now().replace(microsecond=0)

process_input(image_paths,
              output_folder,
              multi_answers_as_f,
              empty_answers_as_g,
              keys_file,
              arrangement_file,
              sort_results,
              output_mcta,
              debug_mode_on,
              form_variant,
              progress_tracker,
              files_timestamp)
