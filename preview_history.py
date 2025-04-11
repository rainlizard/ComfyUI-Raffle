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

# Placeholder generation function (creates a base image, will be resized later if needed by UI)
def create_placeholder(size=(128, 128), text="?"):
    """Creates a simple placeholder PIL image."""
    img = Image.new('RGB', size, color = (40, 40, 40))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default() # Keep it simple for placeholders
    try:
        # Basic centering for default font
        tw, th = d.textsize(text, font=font) if hasattr(d, 'textsize') else (10, 10)
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

        # Use the default history folder path directly
        history_folder = DEFAULT_HISTORY_FOLDER

        # Ensure target directory exists
        if not os.path.exists(history_folder):
            try:
                os.makedirs(history_folder, exist_ok=True)
                print(f"[PreviewHistory] Created history directory: {history_folder}")
            except OSError as e:
                 print(f"[PreviewHistory] Error creating directory {history_folder}: {e}. Cannot proceed.")
                 return {"ui": {"images": []}}

        # --- Save New Image (if provided) ---
        if image is not None and image.nelement() > 0:
            new_pil_image = tensor2pil(image)
            with PreviewHistory._dir_lock: # Lock specifically for saving
                try:
                    now = datetime.now()
                    timestamp_final = now.strftime("%d-%m-%Y_%H-%M-%S")
                    new_filename = f"history_{timestamp_final}.png"
                    new_path = os.path.join(history_folder, new_filename)
                    new_pil_image.save(new_path, "PNG", compress_level=1)
                    # print(f"[PreviewHistory] Saved new file: {new_path}") # Debug
                except Exception as e:
                    print(f"[PreviewHistory] Error saving new image to '{history_folder}': {e}")
                    # Continue even if saving fails, try to show existing history


        # --- Cleanup Old Files & Load Images for Preview ---
        preview_images_pil = []
        sorted_history_files = []
        with PreviewHistory._dir_lock: # Lock for listing, cleanup, and getting paths
             try:
                # Get all .png files with modification times for cleanup and loading
                all_files = []
                for filename in os.listdir(history_folder):
                     if filename.lower().endswith(".png"):
                        full_path = os.path.join(history_folder, filename)
                        try:
                             if os.path.isfile(full_path):
                                mod_time = os.path.getmtime(full_path)
                                all_files.append((mod_time, full_path))
                        except OSError:
                             print(f"[PreviewHistory] Warning: Could not access file {full_path} during scan.")
                             continue # Skip file if cannot get mod_time

                # Sort by modification time, newest first
                all_files.sort(key=lambda x: x[0], reverse=True)

                # Cleanup: Remove files exceeding the current history_size
                if len(all_files) > history_size:
                    files_to_remove = all_files[history_size:] # Get the oldest ones
                    # print(f"[PreviewHistory] Found {len(all_files)} files, keeping {history_size}, removing {len(files_to_remove)}.") # Debug
                    for mod_time, path_to_remove in files_to_remove:
                        try:
                            # print(f"[PreviewHistory] Removing old file: {path_to_remove}") # Debug
                            os.remove(path_to_remove)
                        except OSError as e:
                            print(f"[PreviewHistory] Error removing old file {path_to_remove}: {e}")
                    # Keep only the files that were not removed
                    files_to_keep = all_files[:history_size]
                else:
                    files_to_keep = all_files # Keep all if within limit

                # Get the paths for the files we are keeping for the preview
                sorted_history_files = [f[1] for f in files_to_keep]

             except Exception as e:
                  print(f"[PreviewHistory] Error listing/cleaning files in {history_folder} for preview: {e}")
                  # Fall through with empty list if error during file operations


        # Determine a consistent size for placeholders if needed
        placeholder_size = (128, 128) # Default
        if sorted_history_files: # Check if we have any files paths left after potential cleanup
            try:
                # Try loading the first actual image (newest one)
                first_image_path = sorted_history_files[0]
                temp_img = Image.open(first_image_path)
                placeholder_size = temp_img.size
                temp_img.close()
            except Exception:
                 pass # Ignore if it fails, keep default size

        # Load images from the potentially cleaned-up list
        for i, fp in enumerate(sorted_history_files): # Iterate through the paths we collected
            try:
                img = Image.open(fp).convert('RGB')
                preview_images_pil.append(img)
            except Exception as e:
                print(f"[PreviewHistory] Error loading history image '{fp}' for preview: {e}")
                # Keep error placeholder for load failures, use index 'i' for label
                preview_images_pil.append(create_placeholder(placeholder_size, f"Err {i:02d}"))


        # --- Generate Preview Data for the UI ---
        previews = []
        preview_server = server.PromptServer.instance # Get server instance

        for i, pil_img in enumerate(preview_images_pil):
            if pil_img is None: continue # Should not happen with placeholder logic

            try:
                # Use numpy array for saving temporary preview file
                img_array = np.array(pil_img).astype(np.uint8)
                # Define a unique prefix for each temp preview file in the batch
                # Simplify prefix - just use the index 'i' from the preview loop
                filename_prefix = f"PreviewHistory_Item_{i:02d}_"

                # Get path for temporary preview file
                # Note: using dimensions from pil_img directly
                full_output_folder, fname, count, subfolder, _ = folder_paths.get_save_image_path(
                    filename_prefix, self.output_dir, pil_img.width, pil_img.height
                )
                file = f"{fname}_{count:05}_.png" # Temp preview is always png

                # Save the image (from history dir or placeholder) to the temporary location for UI preview
                pil_img.save(os.path.join(full_output_folder, file), quality=95) # Good quality for preview

                # Append preview info for this image
                previews.append({
                    "filename": file,
                    "subfolder": subfolder,
                    "type": self.type
                })

            except Exception as e:
                print(f"[PreviewHistory] Error generating UI preview for image {i}: {e}")
                # Optionally skip this preview or add an error indicator? For now, just skip.


        # Return the list of preview data dictionaries
        return {"ui": {"images": previews}}


NODE_CLASS_MAPPINGS = {
    "PreviewHistory": PreviewHistory
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PreviewHistory": "Preview History (Raffle)"
} 