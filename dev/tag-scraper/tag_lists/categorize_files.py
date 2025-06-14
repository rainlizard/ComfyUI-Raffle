import os

def load_reference_file(filename):
    """Load a reference file into a set of tags."""
    with open(filename, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip()}

def main():
    # Load all reference files
    artist_tags = load_reference_file('artist.txt')
    character_tags = load_reference_file('character.txt')
    copyright_tags = load_reference_file('copyright.txt')
    meta_tags = load_reference_file('meta.txt')

    # Process the final.txt file
    with open('final.txt', 'r', encoding='utf-8') as infile, \
         open('output.txt', 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            line = line.strip()
            if not line:
                continue

            # Check if this is an UNCATEGORIZED tag
            if line.startswith('[UNCATEGORIZED]'):
                tag = line[15:].strip()  # Remove '[UNCATEGORIZED] ' prefix
                
                # Determine the new category
                if tag in artist_tags:
                    new_line = f'[artist] {tag}'
                elif tag in character_tags:
                    new_line = f'[character] {tag}'
                elif tag in copyright_tags:
                    new_line = f'[copyright] {tag}'
                elif tag in meta_tags:
                    new_line = f'[meta] {tag}'
                else:
                    # Keep as UNCATEGORIZED if not found in any reference file
                    new_line = line
                
                outfile.write(new_line + '\n')
            else:
                # Write the line unchanged if it's not an UNCATEGORIZED tag
                outfile.write(line + '\n')

if __name__ == '__main__':
    main()
