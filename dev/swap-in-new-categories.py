def read_tag_mappings(filename):
    """Read file and return dictionary of tag -> category mappings"""
    mappings = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                # Split on first occurrence of '] ' to handle tags with spaces
                parts = line.split('] ', 1)
                if len(parts) == 2:
                    category = parts[0][1:]  # Remove leading '['
                    tag = parts[1]
                    mappings[tag] = category
    return mappings

def update_categories(source_file, reference_file, output_file):
    """Update categories in source file based on reference file mappings"""
    # Read both files
    reference_mappings = read_tag_mappings(reference_file)
    
    # Read and process source file
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update categories
    updated_lines = []
    for line in lines:
        line = line.strip()
        if line:
            parts = line.split('] ', 1)
            if len(parts) == 2:
                tag = parts[1]
                if tag in reference_mappings:
                    # Use new category from reference file
                    new_category = reference_mappings[tag]
                    updated_lines.append(f'[{new_category}] {tag}')
                else:
                    # Keep original line if tag not found in reference file
                    updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Write updated content to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(updated_lines))

if __name__ == '__main__':
    source_file = 'categorized_tags.txt'  # File to update
    reference_file = 'new_categories_reference.txt'  # File with new categories
    output_file = 'new_categories_output.txt'  # Output file with updated categories
    
    update_categories(source_file, reference_file, output_file)
    print(f'Categories updated and saved to {output_file}')