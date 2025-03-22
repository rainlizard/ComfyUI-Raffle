import requests
import json
import time
from datetime import datetime
import os

# Add this rating map before the functions
rating_map = {
    'g': 'general',
    's': 'sensitive',
    'q': 'questionable',
    'e': 'explicit'
}

def get_filtered_posts(username, api_key, rating, score_range):
    """
    Fetch posts from Danbooru with specific filters using random ordering
    """
    base_url = "https://danbooru.donmai.us"
    endpoint = f"{base_url}/posts.json"
    
    min_score, max_score = score_range
    params = {
        'tags': f'score:>={min_score} score:<={max_score} rating:{rating} order:random -animated',
        'limit': 200
    }
    
    auth = (username, api_key)
    
    print(f"\nRequesting 200 random posts from {rating_map[rating]}")
    print(f"Using score range: {min_score} to {max_score}")
    try:
        response = requests.get(endpoint, auth=auth, params=params)
        response.raise_for_status()
        posts = response.json()
        print(f"API returned {len(posts)} posts")
        return posts
    except requests.exceptions.RequestException as e:
        print(f"Error fetching filtered posts: {e}")
        return []

def get_existing_post_ids(rating):
    """
    Get set of existing post IDs for a rating
    """
    output_dir = "output_scraped"
    filename = os.path.join(output_dir, f"{rating_map[rating]}.txt")
    existing_ids = set()
    
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                post_id = line.split(',')[0].strip()
                existing_ids.add(post_id)
    
    return existing_ids

def save_new_posts(new_posts, rating):
    """
    Save batch of new posts to file
    """
    output_dir = "output_scraped"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{rating_map[rating]}.txt")
    
    with open(filename, 'a', encoding='utf-8') as f:
        for post in new_posts:
            post_id = post['id']
            score = post['score']
            tags = sorted(post['tag_string'].split())
            new_line = f"{post_id}, {score}, {', '.join(tags)}\n"
            f.write(new_line)
    
    print(f"Successfully added {len(new_posts)} new posts to {rating_map[rating]}.txt")

def get_line_counts():
    """
    Get the current number of lines in each rating file
    """
    output_dir = "output_scraped"
    counts = {}
    for rating in ['g', 's', 'q', 'e']:
        filename = os.path.join(output_dir, f"{rating_map[rating]}.txt")
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    counts[rating] = sum(1 for _ in f)
            else:
                counts[rating] = 0
        except IOError:
            counts[rating] = 0
    return counts

def main():
    USERNAME = ""
    API_KEY = ""
    
    ratings = ['g', 's', 'q', 'e']
    score_ranges = {rating: (1024, 2048) for rating in ratings}
    
    start_time = datetime.now()
    
    print("Starting to scrape images...")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            counts = get_line_counts()
            current_rating = min(counts.items(), key=lambda x: x[1])[0]
            print(f"\nProcessing {rating_map[current_rating]} - currently has {counts[current_rating]} entries (lowest)")
            
            min_score, max_score = score_ranges[current_rating]
            existing_ids = get_existing_post_ids(current_rating)
            
            # Fetch batch of random posts
            posts = get_filtered_posts(USERNAME, API_KEY, current_rating, score_ranges[current_rating])
            
            if posts:
                print("Checking for duplicates...")
                new_posts = [post for post in posts if str(post['id']) not in existing_ids]
                print(f"Found {len(new_posts)} new unique posts out of {len(posts)} total posts")
                
                if new_posts:
                    save_new_posts(new_posts, current_rating)
                    counts = get_line_counts()
                    print("\nUpdated file counts:")
                    for r in ratings:
                        print(f"{rating_map[r]}: {counts[r]} posts (score range: {score_ranges[r][0]} to {score_ranges[r][1]})")
                else:
                    # If no new posts found after filtering duplicates, move to next score range
                    new_max = min_score
                    new_min = max(0, new_max // 2)
                    score_ranges[current_rating] = (new_min, new_max)
                    print(f"All posts were duplicates. Lowering score range to {new_min} - {new_max}")
            else:
                # If no posts returned at all, move to next score range
                new_max = min_score
                new_min = max(0, new_max // 2)
                score_ranges[current_rating] = (new_min, new_max)
                print(f"No posts found in current range. Lowering score range to {new_min} - {new_max}")
            
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n\nScraping stopped by user!")
        
    elapsed_time = datetime.now() - start_time
    print(f"\nTotal time elapsed: {elapsed_time}")
    print("\nFinal counts:")
    counts = get_line_counts()
    for rating in ratings:
        print(f"{rating_map[rating]}: {counts[rating]}")

if __name__ == "__main__":
    main()
