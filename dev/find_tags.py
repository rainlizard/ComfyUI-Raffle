import sys
import pyperclip

def read_tags_from_clipboard():
    # Get tags from clipboard and convert to a set for faster lookup
    clipboard_content = pyperclip.paste()
    return set(tag.strip() for tag in clipboard_content.split(','))

def check_file_for_tags(filepath, tags_to_find):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            found_tags = set()
            
            # Read the file line by line
            for line in file:
                # Extract the tag from the line (everything after the closing bracket)
                if ']' in line:
                    tag = line.split(']')[1].strip()
                    if tag in tags_to_find:
                        found_tags.add(tag)
            
            # Print results
            if found_tags:
                print(f"\nFound {len(found_tags)} matching tags:")
                print(', '.join(sorted(found_tags)))
            else:
                print("\nNo matching tags found.")
            
            # Print tags that weren't found
            missing_tags = tags_to_find - found_tags
            if missing_tags:
                print(f"\nTags from clipboard not found in file ({len(missing_tags)}):")
                print(', '.join(sorted(missing_tags)))

    except FileNotFoundError:
        print(f"Error: Could not find file '{filepath}'")
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    # Check if a file was dragged onto the script
    if len(sys.argv) != 2:
        print("Please drag a file onto this script to check it for tags.")
        input("Press Enter to exit...")
        return

    # Get the file path from command line arguments
    filepath = sys.argv[1]
    
    # Get tags from clipboard
    tags_to_find = read_tags_from_clipboard()
    
    if not tags_to_find:
        print("No tags found in clipboard. Please copy tags to clipboard first.")
        input("Press Enter to exit...")
        return

    # Process the file
    check_file_for_tags(filepath, tags_to_find)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
