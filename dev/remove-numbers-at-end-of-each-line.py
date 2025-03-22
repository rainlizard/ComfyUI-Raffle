import sys

def clean_text_file(input_path):
    # Create output path by adding '_cleaned' before the extension
    output_path = input_path.rsplit('.', 1)[0] + '_cleaned.' + input_path.rsplit('.', 1)[1]
    
    # Read and process the file
    with open(input_path, 'r', encoding='utf-8') as infile:
        # Read lines and remove numbers and commas
        cleaned_lines = [line.split(',')[0].strip() for line in infile]
    
    # Write the processed content to new file
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write('\n'.join(cleaned_lines))

if __name__ == "__main__":
    # Check if a file was dragged onto the script
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        try:
            clean_text_file(input_file)
            print(f"File processed successfully! Output saved with '_cleaned' suffix.")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Please drag a file onto the script to process it.")