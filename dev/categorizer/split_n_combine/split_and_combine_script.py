"""
Script to split a text file into multiple files of 150 lines each,
or combine previously split files back into a single file.
"""

import sys
import os
import time
from pathlib import Path

LINES_PER_FILE = 150
SPLIT_FILE_EXTENSION = ".txt"

def get_base_name_and_ext(filename: str) -> tuple[str, str]:
    """
    Extract the base name pattern and extension from a numbered filename.
    Example: '1_categorized.txt' -> ('categorized', '.txt')
    
    Args:
        filename: The filename to analyze
    Returns:
        tuple of (base_name, extension)
    """
    path = Path(filename)
    name = path.stem  # Get filename without extension
    ext = path.suffix
    
    # Check if filename starts with a number followed by underscore
    parts = name.split('_', 1)
    if len(parts) > 1 and parts[0].isdigit():
        base_name = parts[1]
    else:
        base_name = name
    
    return base_name, ext

def split_file(input_file: str) -> None:
    """
    Split the input file into multiple files of LINES_PER_FILE lines each.
    
    Args:
        input_file: Path to the input text file
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Strip empty lines from the end of the file
        while lines and not lines[-1].strip():
            lines.pop()
        
        total_files = (len(lines) + LINES_PER_FILE - 1) // LINES_PER_FILE
        
        for file_num in range(total_files):
            start_idx = file_num * LINES_PER_FILE
            end_idx = start_idx + LINES_PER_FILE
            output_filename = f"{file_num + 1}_uncategorized.txt"  # Simplified naming convention
            
            chunk = lines[start_idx:end_idx]
            if chunk:  # Ensure chunk is not empty
                # Strip empty lines from the end of each chunk
                while chunk and not chunk[-1].strip():
                    chunk.pop()
                
                with open(output_filename, "w", encoding="utf-8") as f:
                    for i, line in enumerate(chunk):
                        if i == len(chunk) - 1:
                            f.write(line.rstrip())  # Remove trailing whitespace on last line
                        else:
                            f.write(line.rstrip() + '\n')  # Normalize line endings
        
        print(f"Split into {total_files} files successfully.")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"Error occurred while splitting: {str(e)}")

def verify_line_counts(files: list[Path], expected_lines: int = LINES_PER_FILE) -> list[tuple[str, int]]:
    """
    Verify the line count of each file and return any inconsistencies.
    
    Args:
        files: List of Path objects for the files to check
        expected_lines: Expected number of lines (except for possibly the last file)
    
    Returns:
        List of tuples (filename, line_count) for files with unexpected line counts
    """
    inconsistencies = []
    if not files:
        return inconsistencies
        
    for i, file_path in enumerate(files):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            line_count = len(lines)
            
            # Last file can have fewer lines
            if i < len(files) - 1 and line_count != expected_lines:
                inconsistencies.append((str(file_path), line_count))
    
    return inconsistencies

def combine_files(input_file):
    """Combine split files back into a single file."""
    try:
        # Get the base name without the number
        base_name, ext = get_base_name_and_ext(input_file)
        directory = os.path.dirname(input_file) or '.'
        split_files = []
        
        # List all files in directory and find matching files
        for filename in os.listdir(directory):
            if not filename[0].isdigit():  # Skip files not starting with a number
                continue
            current_base, current_ext = get_base_name_and_ext(filename)
            if current_base == base_name and current_ext == ext:
                full_path = os.path.join(directory, filename)
                split_files.append(full_path)
        
        if not split_files:
            print(f"No split files found matching pattern: [number]_{base_name}{ext}")
            return
        
        # Sort split files numerically by their starting number
        def get_number(filepath):
            name = Path(filepath).stem
            parts = name.split('_', 1)
            return int(parts[0]) if parts[0].isdigit() else 0
            
        split_files.sort(key=get_number)
        
        # Verify line counts before combining
        split_files_paths = [Path(f) for f in split_files]
        inconsistencies = verify_line_counts(split_files_paths)
        
        print(f"Found {len(split_files)} split files to combine:")
        for f in split_files:
            print(f"  - {os.path.basename(f)}")
        
        # Report any line count inconsistencies
        if inconsistencies:
            print("\nWarning: The following files have inconsistent line counts:")
            for filename, line_count in inconsistencies:
                print(f"  - {os.path.basename(filename)}: {line_count} lines (expected {LINES_PER_FILE})")
        
        # Combine all files
        output_file = f"{base_name}_combined{ext}"
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for i, split_file in enumerate(split_files):
                with open(split_file, 'r', encoding='utf-8') as infile:
                    # Read content and strip trailing whitespace from each line
                    lines = [line.rstrip() for line in infile]
                    # Join lines with newlines
                    content = '\n'.join(lines)
                    outfile.write(content)
                    # Add newline between files (except for the last file)
                    if i < len(split_files) - 1:
                        outfile.write('\n')
        
        print(f"\nSuccessfully combined into: {output_file}")
    
    except Exception as e:
        print(f"Error occurred: {str(e)}")

def main():
    """Main function to handle command line arguments and execute appropriate action."""
    if len(sys.argv) != 2:
        print("Usage: Drag and drop a file onto this script")
        return
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        return
    
    # Check if the file starts with a number to determine if it's a split file
    filename = Path(input_file).stem
    is_numbered = filename.split('_')[0].isdigit()
    
    if is_numbered:
        combine_files(input_file)
    else:
        split_file(input_file)
    
    # Pause the console
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()
