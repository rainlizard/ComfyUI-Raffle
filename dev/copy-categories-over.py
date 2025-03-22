#!/usr/bin/env python3

def main():
    # Load the categorized tags into a dictionary
    categorized_tags = {}
    with open('categorized_tags.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Extract category and tag
            parts = line.split('] ', 1)
            if len(parts) != 2:
                continue
                
            category = parts[0] + ']'  # Adding back the closing bracket
            tag = parts[1]
            
            categorized_tags[tag] = category
    
    # Process the general tags file
    general_tags = []
    with open('new-general.txt', 'r', encoding='utf-8') as f:
        for line in f:
            tag = line.strip()
            if not tag:
                continue
                
            # Find category for this tag
            category = categorized_tags.get(tag, '[UNCATEGORIZED]')
            general_tags.append(f"{category} {tag}")
    
    # Write the categorized general tags back to a file
    with open('new-general-categorized.txt', 'w', encoding='utf-8') as f:
        for line in general_tags:
            f.write(line + '\n')

if __name__ == "__main__":
    main()
