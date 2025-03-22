def read_tags_from_file(filename):
    tags = set()
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Split on first colon to ignore categories
            tag = line.split(':', 1)[0].strip()
            if tag:
                tags.add(tag)
    return tags

# File paths
file1 = 'lists/categorized_tags.txt'
file2 = 'dev/new-taglists-general-partially_categorized.txt'

# Read tags from both files
tags1 = read_tags_from_file(file1)
tags2 = read_tags_from_file(file2)

# Find tags that are in file1 but not in file2
missing_tags = tags1 - tags2

# Print results
print(f"\nTags present in {file1} but missing from {file2}:")
print("-" * 60)

# Print tags with a counter
for i, tag in enumerate(sorted(missing_tags), 1):
    print(f"{i}. {tag}")

print(f"\nTotal number of missing tags: {len(missing_tags)}")

# Add pause at the end
input("\nPress Enter to exit...") 