import requests
import json
import time
import os

# Constants
OUTPUT_DIR = "tag_lists"
CATEGORY_FILES = {
    0: "general.txt",    # General tags
    1: "artist.txt",     # Artist tags
    3: "copyright.txt",  # Copyright tags
    4: "character.txt",  # Character tags
    5: "meta.txt",       # Meta tags
    'all': "all_tags.txt" # All tags combined
}
BASE_URL = "https://danbooru.donmai.us/tags.json"
LIMIT = 200  # Maximum limit per request
MIN_COUNT = 100  # Minimum post count

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def get_output_path(filename):
    """Get full path for output file"""
    return os.path.join(OUTPUT_DIR, filename)

def get_tags_with_count_over(min_count):
    """
    Retrieve all tags that have a post count higher than min_count
    """
    all_tags = []
    page = 1
    more_results = True
    
    print(f"Fetching tags with count over {min_count}...")
    
    while more_results:
        # Parameters for the API request
        params = {
            "search[post_count]": f">{min_count}",
            "search[order]": "count",  # Order by post count (highest first)
            "limit": LIMIT,
            "page": page
        }
        
        try:
            print(f"Fetching page {page}...")
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            tags = response.json()
            
            if not tags:
                more_results = False
            else:
                all_tags.extend(tags)
                page += 1
                
            # Be nice to the API and avoid rate limiting
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            break
    
    return all_tags

def save_tags_to_files(tags, append=False):
    """
    Save the tags to separate files based on their category and to all_tags.txt
    append: If True, append to files; if False, overwrite files
    """
    try:
        # Group tags by category
        categorized_tags = {}
        for tag in tags:
            category = tag['category']
            if category in CATEGORY_FILES:
                if category not in categorized_tags:
                    categorized_tags[category] = []
                categorized_tags[category].append(tag)
        
        # Save each category to its respective file
        for category, category_tags in categorized_tags.items():
            filename = get_output_path(CATEGORY_FILES[category])
            mode = 'a' if append else 'w'
            
            with open(filename, mode, encoding='utf-8') as f:
                # Sort by post_count in descending order
                sorted_tags = sorted(category_tags, key=lambda x: x['post_count'], reverse=True)
                for tag in sorted_tags:
                    f.write(f"{tag['name']}, {tag['post_count']}\n")
            
            print(f"Saved {len(category_tags)} {CATEGORY_FILES[category]} tags")
        
        # Save to all_tags.txt
        filename = get_output_path(CATEGORY_FILES['all'])
        mode = 'a' if append else 'w'
        
        with open(filename, mode, encoding='utf-8') as f:
            # Sort all tags by post_count
            sorted_tags = sorted(tags, key=lambda x: x['post_count'], reverse=True)
            for tag in sorted_tags:
                f.write(f"{tag['name']}, {tag['post_count']}\n")
        
        print(f"Saved {len(tags)} tags to {CATEGORY_FILES['all']}")
            
    except IOError as e:
        print(f"Error saving to files: {e}")

def get_last_saved_page():
    """
    Determine the last page that was processed by counting lines in all_tags.txt
    """
    try:
        filepath = get_output_path(CATEGORY_FILES['all'])
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                total_lines = sum(1 for _ in f)
                # Calculate the last completed page based on LIMIT tags per page
                last_page = (total_lines + LIMIT - 1) // LIMIT
                return last_page
        except FileNotFoundError:
            return 0
                
    except Exception as e:
        print(f"Error reading files: {e}")
        return 0

def clear_output_files():
    """Clear all category files"""
    for filename in CATEGORY_FILES.values():
        filepath = get_output_path(filename)
        open(filepath, 'w').close()

def main():
    ensure_output_dir()
    
    # Get the last processed page
    start_page = get_last_saved_page()
    page = start_page + 1 if start_page > 0 else 1
    more_results = True
    total_tags = 0
    
    print(f"Fetching tags with count over {MIN_COUNT}...")
    print(f"Resuming from page {page}...")
    
    # Clear files if starting from beginning
    if page == 1:
        clear_output_files()
    
    while more_results:
        # Parameters for the API request
        params = {
            "search[post_count]": f">{MIN_COUNT}",
            "search[order]": "count",  # Order by post count (highest first)
            "limit": LIMIT,
            "page": page
        }
        
        try:
            print(f"Fetching page {page}...")
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            
            tags = response.json()
            
            if not tags:
                more_results = False
            else:
                # Save this batch immediately
                save_tags_to_files(tags, append=(page != 1))
                total_tags += len(tags)
                page += 1
                
            # Be nice to the API and avoid rate limiting
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            break
    
    print(f"Finished! Found {total_tags} tags with count over {MIN_COUNT}")

if __name__ == "__main__":
    main()
