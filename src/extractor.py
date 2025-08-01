"""Functions for extracting answer keys from single answer sheets."""

import typing as tp
from pathlib import Path
from datetime import datetime

import image_utils
import corner_finding
import grid_info as grid_i
import grid_reading as grid_r
import data_exporting


def extract_answer_key_from_image(
        image_path: Path,
        output_folder: Path,
        multi_answers_as_f: bool,
        empty_answers_as_g: bool,
        form_variant: grid_i.FormVariant,
        files_timestamp: tp.Optional[datetime],
        debug_mode_on: bool = False
) -> tp.Optional[Path]:
    """
    Extract answers from a single answer sheet image and save as CSV.
    
    Args:
        image_path: Path to the answer sheet image
        output_folder: Path to save the extracted answer key CSV
        multi_answers_as_f: Convert multiple answers to 'F'
        empty_answers_as_g: Save empty answers as 'G'
        form_variant: Form variant (75q or 150q)
        files_timestamp: Timestamp for file naming
        debug_mode_on: Enable debug mode for troubleshooting
        
    Returns:
        Path to the saved CSV file if successful, None if failed
    """
    
    # Create debug directory if needed
    debug_dir = None
    if debug_mode_on:
        debug_dir = output_folder / (
                data_exporting.format_timestamp_for_file(files_timestamp) + "debug_extractor")
        data_exporting.make_dir_if_not_exists(debug_dir)
        debug_path = debug_dir / image_path.stem
        data_exporting.make_dir_if_not_exists(debug_path)
    else:
        debug_path = None

    try:
        # Load and prepare the image
        image = image_utils.get_image(image_path, save_path=debug_path)
        prepared_image = image_utils.prepare_scan_for_processing(
            image, save_path=debug_path)

        # Find corners
        try:
            corners = corner_finding.find_corner_marks(prepared_image,
                                                   save_path=debug_path)
        except corner_finding.CornerFindingError as e:
            print(f"Error finding corners in {image_path.name}: {e}")
            return None

        # Process the image
        morphed_image = image_utils.dilate(prepared_image,
                                           save_path=debug_path)

        # Establish grid
        grid = grid_r.Grid(corners,
                           grid_i.GRID_HORIZONTAL_CELLS,
                           grid_i.GRID_VERTICAL_CELLS,
                           morphed_image,
                           save_path=debug_path)

        # Calculate fill percentages
        field_fill_percents = {
            key: grid_r.get_group_from_info(value,
                                            grid).get_all_fill_percents()
            for key, value in form_variant.fields.items() if value is not None
        }
        answer_fill_percents = [
            grid_r.get_group_from_info(question, grid).get_all_fill_percents()
            for question in form_variant.questions
        ]

        # Calculate threshold
        threshold = grid_r.calculate_bubble_fill_threshold(
            field_fill_percents,
            answer_fill_percents,
            save_path=debug_path,
            form_variant=form_variant)

        # Extract answers
        answers = [
            grid_r.read_answer_as_string(i, grid, multi_answers_as_f,
                                         threshold, form_variant,
                                         answer_fill_percents[i])
            for i in range(form_variant.num_questions)
        ]

        # Read test form code if available
        form_code = ""
        if grid_i.Field.TEST_FORM_CODE in field_fill_percents:
            form_code = grid_r.read_field_as_string(
                grid_i.Field.TEST_FORM_CODE, grid, threshold, form_variant,
                field_fill_percents[grid_i.Field.TEST_FORM_CODE]) or ""

        # Create output sheet for the answer key
        keys_results = data_exporting.OutputSheet(
            [grid_i.Field.TEST_FORM_CODE, grid_i.Field.IMAGE_FILE],
            form_variant.num_questions)

        # Add the extracted key data
        field_data: tp.Dict[grid_i.RealOrVirtualField, str] = {
            grid_i.Field.TEST_FORM_CODE: form_code,
            grid_i.Field.IMAGE_FILE: image_path.name
        }
        keys_results.add(field_data, answers)

        # Clean up the data
        keys_results.clean_up(
            replace_empty_with="G" if empty_answers_as_g else "")

        # Save the answer key
        output_path = keys_results.save(output_folder,
                                        "extracted_answer_key",
                                        sort=False,
                                        timestamp=files_timestamp)

        print(f"✔️ Answer key extracted from '{image_path.name}' and saved to '{output_path.name}'")
        return Path(output_path)

    except Exception as e:
        print(f"❌ Error extracting answer key from '{image_path.name}': {str(e)}")
        if debug_mode_on:
            raise
        return None


def extract_answer_key_from_image_gui(
        image_path: Path,
        output_folder: Path,
        multi_answers_as_f: bool,
        empty_answers_as_g: bool,
        form_variant: grid_i.FormVariant,
        files_timestamp: tp.Optional[datetime],
        progress_tracker: tp.Optional[tp.Any] = None,
        debug_mode_on: bool = False
) -> tp.Optional[Path]:
    """
    GUI version of extract_answer_key_from_image with progress tracking.
    
    Args:
        image_path: Path to the answer sheet image
        output_folder: Path to save the extracted answer key CSV
        multi_answers_as_f: Convert multiple answers to 'F'
        empty_answers_as_g: Save empty answers as 'G'
        form_variant: Form variant (75q or 150q)
        files_timestamp: Timestamp for file naming
        progress_tracker: GUI progress tracker widget
        debug_mode_on: Enable debug mode for troubleshooting
        
    Returns:
        Path to the saved CSV file if successful, None if failed
    """
    
    if progress_tracker:
        progress_tracker.set_status(f"Extracting answer key from '{image_path.name}'.", False)
    
    result = extract_answer_key_from_image(
        image_path, output_folder, multi_answers_as_f, empty_answers_as_g,
        form_variant, files_timestamp, debug_mode_on
    )
    
    if progress_tracker:
        if result:
            progress_tracker.set_status(f"✔️ Answer key extracted and saved to '{result.name}'", False)
        else:
            progress_tracker.set_status(f"❌ Failed to extract answer key from '{image_path.name}'", False)
    
    return result
