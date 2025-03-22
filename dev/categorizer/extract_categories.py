import sys
import pyperclip
import time
import os

def get_categories(file_path):
    """
    Extract unique categories from a text file where categories are marked with square brackets.
    
    Args:
        file_path (str): Path to the input text file
        
    Returns:
        list: Sorted list of unique categories
    """
    categories = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Find text between square brackets
                if '[' in line and ']' in line:
                    category = line[line.find('[')+1:line.find(']')]
                    categories.add(category)
                    
        return sorted(list(categories))
    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return []

def main():
    try:
        # Debug: Command line arguments
        print("\n=== COMMAND LINE DEBUGGING ===")
        print(f"Number of arguments: {len(sys.argv)}")
        print(f"Full arguments list: {sys.argv}")
        print(f"Program name: {sys.argv[0]}")
        if len(sys.argv) > 1:
            print(f"First argument: {sys.argv[1]}")
        
        # Debug: Working directory
        print("\n=== DIRECTORY DEBUGGING ===")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")
        
        # Check if a file was dragged onto the script
        if len(sys.argv) < 2:
            print("Error: No file provided")
            print("Please drag a text file onto the batch file.")
            input("Press Enter to exit...")
            return

        file_path = sys.argv[1].strip('"')
        print("\n=== FILE PATH DEBUGGING ===")
        print(f"Raw file path: {sys.argv[1]}")
        print(f"Processed file path: {file_path}")
        print(f"Absolute path: {os.path.abspath(file_path)}")
        print(f"Path exists check: {os.path.exists(file_path)}")
        
        # Debug: Check if file exists and print full path
        if os.path.exists(file_path):
            print(f"File exists at: {file_path}")
        else:
            print(f"File does not exist at: {file_path}")
            print(f"Current working directory is: {os.getcwd()}")
        
        categories = get_categories(file_path)
        
        if categories:
            # Create a string with all categories
            categories_text = '\n'.join(categories)
            
            # Copy to clipboard
            try:
                pyperclip.copy(categories_text)
                print("\nFound categories (copied to clipboard):")
            except Exception as e:
                print(f"\nCould not copy to clipboard. Error: {str(e)}")
                print("Found categories:")
            
            print(categories_text)
        else:
            print("No categories found or error occurred.")
    
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    
    finally:
        print("\nPress Enter to exit...")
        input()

if __name__ == "__main__":
    main()