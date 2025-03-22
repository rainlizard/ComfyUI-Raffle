import re
from operator import itemgetter

def sort_lines_by_second_value(file_content):
    lines = file_content.strip().split('\n')
    parsed_lines = []
    
    for line in lines:
        # Split by comma and extract the first two values
        parts = line.split(',', 2)
        if len(parts) >= 2:
            try:
                first_value = int(parts[0].strip())
                second_value = int(parts[1].strip())
                remaining = parts[2] if len(parts) > 2 else ""
                parsed_lines.append((first_value, second_value, remaining, line))
            except ValueError:
                # Skip lines that don't have proper integer values
                continue
    
    # Sort by the second value (descending)
    sorted_lines = sorted(parsed_lines, key=itemgetter(1), reverse=True)
    
    # Return the original lines in the new order
    return [item[3] for item in sorted_lines]

def sort_lines_by_second_value_chunked(input_filename, output_filename, chunk_size=10000):
    from tempfile import NamedTemporaryFile
    import heapq
    
    def parse_line(line):
        parts = line.strip().split(',', 2)
        if len(parts) >= 2:
            try:
                first_value = int(parts[0].strip())
                second_value = int(parts[1].strip())
                return (second_value, line.strip())  # Only store what we need
            except ValueError:
                return None
        return None

    # Step 1: Split into sorted chunks
    temp_files = []
    
    with open(input_filename, 'r') as input_file:
        chunk = []
        for line in input_file:
            parsed = parse_line(line)
            if parsed:
                chunk.append(parsed)
            
            if len(chunk) >= chunk_size:
                chunk.sort(reverse=True)  # Sort by second_value
                temp_file = NamedTemporaryFile(mode='w+', delete=False)
                for _, original_line in chunk:
                    temp_file.write(original_line + '\n')
                temp_file.close()
                temp_files.append(temp_file.name)
                chunk = []
        
        # Handle the last chunk
        if chunk:
            chunk.sort(reverse=True)
            temp_file = NamedTemporaryFile(mode='w+', delete=False)
            for _, original_line in chunk:
                temp_file.write(original_line + '\n')
            temp_file.close()
            temp_files.append(temp_file.name)

    # Step 2: Merge sorted chunks
    with open(output_filename, 'w') as output_file:
        files = [open(f, 'r') for f in temp_files]
        parsed_lines = []
        
        # Get initial lines from each file
        for f in files:
            line = f.readline().strip()
            if line:
                parsed = parse_line(line)
                if parsed:
                    heapq.heappush(parsed_lines, (-parsed[0], parsed[1], f))  # Negative for max heap

        # Merge while maintaining sort order
        while parsed_lines:
            _, line, current_file = heapq.heappop(parsed_lines)
            output_file.write(line + '\n')
            
            # Get next line from the same file
            next_line = current_file.readline().strip()
            if next_line:
                parsed = parse_line(next_line)
                if parsed:
                    heapq.heappush(parsed_lines, (-parsed[0], parsed[1], current_file))

        # Clean up
        for f in files:
            f.close()
        
        import os
        for temp_file in temp_files:
            os.unlink(temp_file)

def main():
    import sys
    
    # Get input file from command line arguments
    if len(sys.argv) < 2:
        print("Usage: Drag a file onto this script or run: python rearranger.py input_file [output_file]")
        return
        
    input_file = sys.argv[1]
    # Generate output filename by adding '_sorted' before the extension
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        import os
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_sorted{ext}"
    
    print(f"Sorting {input_file}")
    print(f"Output will be saved to {output_file}")
    
    sort_lines_by_second_value_chunked(input_file, output_file)
    print("Sorting complete!")

if __name__ == "__main__":
    main()
