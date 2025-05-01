import folder_paths
import os
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import server # Required for preview generation
import threading
import shutil # For potential file operations
from datetime import datetime # For timestamps

# --- Constants ---
# Determine the base path of the custom node
EXTENSION_PATH = os.path.normpath(os.path.dirname(__file__))
DEFAULT_HISTORY_FOLDER = os.path.join(EXTENSION_PATH, "history_folder")

# Tensor to PIL
def tensor2pil(image):
    if image.dim() > 3:
        image = image[0]
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

# Placeholder generation function (remains unused in the optimized path, keep for robustness?)
# Note: Placeholder generation is removed from the main optimized logic below.
# If an error occurs during copy, the image is simply skipped in the preview.
def create_placeholder(size=(128, 128), text="?"):
    """Creates a simple placeholder PIL image."""
    img = Image.new('RGB', size, color = (40, 40, 40))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default() # Keep it simple for placeholders
    try:
        # Basic centering for default font
        tw, th = d.textbbox((0,0), text, font=font)[2:] if hasattr(d, 'textbbox') else (10, 10) # Use textbbox if available
        d.text(((size[0]-tw)/2, (size[1]-th)/2), text, font=font, fill=(180, 180, 180))
    except Exception as e:
        print(f"[PreviewHistory] Error drawing placeholder text: {e}")
        d.text((10, 10), text, fill=(180, 180, 180)) # Fallback position
    return img


class PreviewHistory:
    # Lock for file system operations in the target directory
    _dir_lock = threading.Lock()

    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory() # For UI previews
        self.type = "temp"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "history_size": ("INT", {
                    "default": 9,
                    "min": 1,
                    "max": 1000000,
                    "step": 1,
                    "tooltip": "How many images to keep in the history folder."
                }),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "execute"
    OUTPUT_NODE = True
    CATEGORY = "Raffle/Previews"

    # --- Main Execution ---

    def execute(self, image, history_size):

        history_folder = DEFAULT_HISTORY_FOLDER

        # Ensure target directory exists
        if not os.path.exists(history_folder):
            try:
                os.makedirs(history_folder, exist_ok=True)
                print(f"[PreviewHistory] Created history directory: {history_folder}")
            except OSError as e:
                 print(f"[PreviewHistory] Error creating directory {history_folder}: {e}. Cannot proceed.")
                 # Return empty previews if directory creation fails
                 return {"ui": {"images": []}} # Return empty list

        # --- Save New Image (if provided) ---
        new_image_saved_path = None
        if image is not None and image.nelement() > 0:
            new_pil_image = tensor2pil(image)
            with PreviewHistory._dir_lock: # Lock specifically for saving
                try:
                    now = datetime.now()
                    timestamp_final = now.strftime("%d-%m-%Y_%H-%M-%S")
                    # Include milliseconds for higher uniqueness, preventing rare collisions
                    timestamp_final += f"_{now.microsecond // 1000:03d}"
                    new_filename = f"history_{timestamp_final}.png"
                    new_path = os.path.join(history_folder, new_filename)
                    new_pil_image.save(new_path, "PNG", compress_level=1) # Faster compression
                    new_image_saved_path = new_path # Keep track of the path if saved
                    # print(f"[PreviewHistory] Saved new file: {new_path}") # Debug
                except Exception as e:
                    print(f"[PreviewHistory] Error saving new image to '{history_folder}': {e}")
                    # Continue even if saving fails, try to show existing history

        # --- Cleanup Old Files & Get List for Preview ---
        sorted_history_files = [] # List to hold full paths of files to preview
        with PreviewHistory._dir_lock: # Lock for listing, cleanup
             try:
                # Get all .png files with modification times for cleanup
                all_files = []
                for filename in os.listdir(history_folder):
                     if filename.lower().endswith(".png"):
                        full_path = os.path.join(history_folder, filename)
                        try:
                             if os.path.isfile(full_path):
                                # Use creation time if available and potentially more stable, else modification time
                                # Note: ctime might be platform-dependent (inode change on Unix, creation on Win)
                                # Stick to mtime for broader consistency unless ctime is specifically desired
                                mod_time = os.path.getmtime(full_path)
                                all_files.append((mod_time, full_path))
                        except OSError:
                             print(f"[PreviewHistory] Warning: Could not access file {full_path} during scan.")
                             continue # Skip file if cannot get mod_time

                # Sort by modification time, newest first
                all_files.sort(key=lambda x: x[0], reverse=True)

                # Determine which files to keep based on history_size
                files_to_keep_info = all_files[:history_size]
                files_to_remove_info = all_files[history_size:]

                # Cleanup: Remove files exceeding the current history_size
                if files_to_remove_info:
                    # print(f"[PreviewHistory] Found {len(all_files)} files, keeping {history_size}, removing {len(files_to_remove_info)}.") # Debug
                    for mod_time, path_to_remove in files_to_remove_info:
                        try:
                            # print(f"[PreviewHistory] Removing old file: {path_to_remove}") # Debug
                            os.remove(path_to_remove)
                        except OSError as e:
                            print(f"[PreviewHistory] Error removing old file {path_to_remove}: {e}")

                # Get the final list of full paths for the files we are keeping for the preview
                sorted_history_files = [f[1] for f in files_to_keep_info]

             except Exception as e:
                  print(f"[PreviewHistory] Error listing/cleaning files in {history_folder}: {e}")
                  # Fall through with empty list if error during file operations


        # --- Generate Preview Data for the UI by Copying Files ---
        previews = []
        preview_server = server.PromptServer.instance # Get server instance

        # Process the sorted list of history files to generate previews
        for i, history_file_path in enumerate(sorted_history_files):
            if not os.path.exists(history_file_path):
                 print(f"[PreviewHistory] Warning: File {history_file_path} not found during preview generation (maybe removed?). Skipping.")
                 continue

            try:
                # 1. Get image dimensions efficiently
                # Use a context manager to ensure the file handle is closed
                # PIL often reads headers without loading the full image data
                with Image.open(history_file_path) as img:
                    width, height = img.size

                # 2. Determine temporary path information using dimensions
                # Use a distinct prefix based on the original filename hash or index to avoid collisions in temp dir
                # Using index 'i' is simple and effective here.
                filename_prefix = f"PreviewHistory_Item_{i:02d}_"
                full_output_folder, fname, count, subfolder, _ = folder_paths.get_save_image_path(
                    filename_prefix, self.output_dir, width, height
                )
                temp_filename = f"{fname}_{count:05}_.png" # Previews are always PNG
                temp_file_path = os.path.join(full_output_folder, temp_filename)

                # 3. Copy the file from history folder to temp folder
                # shutil.copy2 preserves more metadata (like mtime), copy is slightly faster if metadata isn't needed.
                # Using copy should be sufficient here.
                shutil.copy(history_file_path, temp_file_path)

                # 4. Append preview info for this image
                previews.append({
                    "filename": temp_filename,
                    "subfolder": subfolder,
                    "type": self.type
                })

            except Exception as e:
                print(f"[PreviewHistory] Error processing history image '{history_file_path}' for preview: {e}. Skipping this image.")
                # Optionally, could create and copy a placeholder image here, but skipping is simpler/faster.


        # Return the list of preview data dictionaries
        # print(f"[PreviewHistory] Generated {len(previews)} previews.") # Debug
        return {"ui": {"images": previews}}


NODE_CLASS_MAPPINGS = {
    "PreviewHistory": PreviewHistory
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PreviewHistory": "Preview History (Raffle)"
} 