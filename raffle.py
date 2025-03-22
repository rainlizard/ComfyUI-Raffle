import os
import folder_paths
import random

class Raffle:
    @classmethod
    def INPUT_TYPES(s):
        print("Initializing Raffle INPUT_TYPES")
        extension_path = os.path.normpath(os.path.dirname(__file__))
        print(f"Extension path: {extension_path}")
        
        return {
            "required": {
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Seed value used to randomly select a taglist from the filtered pool of available taglists"
                }),
                "use_general": ("BOOLEAN", {"default": False, "tooltip": "Enable selection from general.txt which contains 100,000 SFW taglists"}),
                "use_questionable": ("BOOLEAN", {"default": False, "tooltip": "Enable selection from questionable.txt which contains 100,000 questionable taglists"}),
                "use_sensitive": ("BOOLEAN", {"default": True, "tooltip": "Enable selection from sensitive.txt which contains 100,000 sensitive taglists"}),
                "use_explicit": ("BOOLEAN", {"default": True, "tooltip": "Enable selection from explicit.txt which contains 100,000 explicit taglists"}),
                "taglists_must_include": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Drastically reduces the pool of available taglists. Only taglists containing ALL these tags will be considered for selection. Use sparingly as this can quickly limit options."
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "forceInput": True,
                    "default": "",
                    "tooltip": "Filters individual tags from the selected taglist (doesn't exclude entire taglists). Tags listed here won't appear in the 'Filtered tags' output."
                }),
                "negative_prompt_2": ("STRING", {
                    "multiline": True,
                    "default": "censored, mosaic_censoring, bar_censor",
                    "tooltip": "Additional tags to filter from the final output. Combined with negative_prompt tags to avoid having to put all filtering tags in your main negative prompt."
                }),
                "exclude_taglists_containing": ("STRING", {
                    "multiline": True,
                    "default": "comic, 4koma, multiple_girls, multiple_boys, multiple_views, reference_sheet, 2girls, 3girls, 4girls, 5girls, 6+girls, 2boys, 3boys, 4boys, 5boys, 6+boys, gangbang, furry, obese, yaoi, yuri, otoko_no_ko, strap-on, futa_with_female, futa_without_pussy, implied_futanari, futanari, diaper, fart, pee, peeing, scat, guro, vore, horse_penis, prolapse, anal_prolapse",
                    "tooltip": "Eliminates entire taglists containing any of these tags from the selection pool. Use for tags that make the whole taglist unusable rather than just removing individual tags."
                }),
                # Replace all individual category booleans with a single text field for excluded categories
                "exclude_categories": ("STRING", {
                    "multiline": True,
                    "default": "clothes_and_accessories, female_physical_descriptors, named_garment_exposure, specific_garment_interactions, speech_and_text, standard_physical_descriptors, metadata_and_attribution, intentional_design_exposure, two_handed_character_items, holding_large_items, color_scheme",
                    "tooltip": "Enter category names to exclude, separated by commas. The complete list of available categories can be seen in the 'Debug info' output."
                })
            },
        } 

    CATEGORY = "Raffle"
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("Filtered tags", "Unfiltered tags", "Debug info")
    OUTPUT_TOOLTIPS = (
        "The final filtered list of tags that match your selected categories with negative prompt tags removed, ready to use in your prompt",
        "The complete original taglist that was randomly selected from the pool before any filtering was applied (for debugging purposes)",
        "Information about the selection process, including the size of the available pool of taglists after applying your filters"
    )
    OUTPUT_NODE = True
    FUNCTION = "process_tags"

    # Add class variable to cache tag lists
    _tag_cache = {}
    
    def _load_taglist(self, filename, taglists_must_include_tags=None, exclude_tags=None, seed=0):
        """Load a line from a file, finding taglists that match required tags"""
        print(f"Attempting to load taglist: {filename}")
        extension_path = os.path.normpath(os.path.dirname(__file__))
        filepath = os.path.join(extension_path, "lists", filename)
        print(f"Loading from filepath: {filepath}")
        
        try:
            valid_taglists = []
            
            # Pre-compute sets for faster lookups - no need to normalize these
            exclude_tags_set = set(exclude_tags) if exclude_tags else None
            taglists_must_include_set = set(taglists_must_include_tags) if taglists_must_include_tags else None
            
            # First pass: find taglists that match our criteria
            with open(filepath, 'r', encoding='utf-8') as f:
                for taglist_num, taglist in enumerate(f):
                    taglist = taglist.strip()
                    if not taglist:
                        continue
                    
                    # Split on comma since file is already normalized
                    taglist_tags = frozenset(tag.strip() for tag in taglist.split(','))
                    
                    # Check for excluded tags first (using set intersection for speed)
                    if exclude_tags_set and not taglist_tags.isdisjoint(exclude_tags_set):
                        continue
                    
                    # If we have required tags, check if they're all in this taglist
                    if taglists_must_include_set:
                        if taglists_must_include_set.issubset(taglist_tags):
                            valid_taglists.append((filename, taglist))
                    else:
                        valid_taglists.append((filename, taglist))
            
            return valid_taglists
                    
        except Exception as e:
            print(f"Error loading {filename}: {str(e)}")
            raise
        
        return []

    def normalize_tags(self, tag_string):
        print(f"Normalizing tag string of length: {len(tag_string)}")
        """
        Normalize a string of tags to a consistent format:
        - Convert spaces to underscores within tags
        - Handle both comma-space and comma separators
        - Handle newlines as separators
        - Remove duplicate separators and spaces
        - Strip whitespace
        
        Examples:
            "red hair, blue hair"     -> ["red_hair", "blue_hair"]
            "red_hair,blue hair"      -> ["red_hair", "blue_hair"]
            "red hair\nblue_hair"     -> ["red_hair", "blue_hair"]
            "red hair,\nblue_hair"    -> ["red_hair", "blue_hair"]
            "red hair,,blue_hair"     -> ["red_hair", "blue_hair"]
            "red   hair,blue  hair"   -> ["red_hair", "blue_hair"]
        """
        # Replace newlines with commas
        tag_string = tag_string.replace('\r\n', '\n')  # Normalize line endings
        tag_string = tag_string.replace('\n', ',')
        
        # Remove multiple consecutive spaces
        while '  ' in tag_string:
            tag_string = tag_string.replace('  ', ' ')
            
        # Remove multiple consecutive commas
        while ',,' in tag_string:
            tag_string = tag_string.replace(',,', ',')
        
        # Then split on commas (handling both ", " and "," cases)
        tags = tag_string.replace(', ', ',').split(',')
        
        # Then normalize each tag
        return [
            tag.strip().replace(' ', '_')
            for tag in tags
            if tag.strip()
        ]

    def process_tags(self, exclude_taglists_containing, taglists_must_include, seed,
                    negative_prompt="", negative_prompt_2="",
                    use_general=True, use_questionable=False, use_sensitive=False, use_explicit=False,
                    exclude_categories=""):
        
        print("\n=== Starting Raffle Process ===")
        print(f"Process ID: {os.getpid()}")
        print(f"Current working directory: {os.getcwd()}")

        # Add directory existence check
        extension_path = os.path.normpath(os.path.dirname(__file__))
        lists_path = os.path.join(extension_path, "lists")
        print(f"Extension path: {extension_path}")
        print(f"Lists directory path: {lists_path}")
        
        if not os.path.exists(lists_path):
            print(f"ERROR: Lists directory not found at {lists_path}")
            raise ValueError(f"Lists directory not found at {lists_path}")

        # Check for categorized tags file
        categorized_tags_file_path = os.path.join(lists_path, "categorized_tags.txt")
        print(f"Checking categorized tags file: {categorized_tags_file_path}")
        
        if not os.path.exists(categorized_tags_file_path):
            print(f"ERROR: Categorized tags file not found at {categorized_tags_file_path}")
            raise ValueError(f"Categorized tags file not found at {categorized_tags_file_path}")

        # Define all available categories and handle exclusions
        all_categories = [
            'abstract_symbols',
            'actions',
            'artstyle_technique',
            'background_objects',
            'bodily_fluids',
            'camera_angle_perspective',
            'camera_focus_subject',
            'camera_framing_composition',
            'character_count',
            'clothes_and_accessories',
            'color_scheme',
            'content_censorship_methods',
            'expressions_and_mental_state',
            'female_intimate_anatomy',
            'female_physical_descriptors',
            'format_and_presentation',
            'gaze_direction_and_eye_contact',
            'general_clothing_exposure',
            'generic_clothing_interactions',
            'holding_large_items',
            'holding_small_items',
            'intentional_design_exposure',
            'lighting_and_vfx',
            'male_intimate_anatomy',
            'male_physical_descriptors',
            'metadata_and_attribution',
            'named_garment_exposure',
            'nudity_and_absence_of_clothing',
            'one_handed_character_items',
            'physical_locations',
            'poses',
            'publicly_visible_anatomy',
            'relationships',
            'sex_acts',
            'sfw_clothed_anatomy',
            'special_backgrounds',
            'specific_garment_interactions',
            'speech_and_text',
            'standard_physical_descriptors',
            'thematic_settings',
            'two_handed_character_items'
        ]
        
        # Process excluded categories
        excluded_categories = []
        if exclude_categories.strip():
            excluded_categories = self.normalize_tags(exclude_categories)
            
            # Check if all excluded categories are valid
            invalid_categories = [c for c in excluded_categories if c not in all_categories]
            if invalid_categories:
                error_msg = (f"Error: Invalid category names: {', '.join(invalid_categories)}. "
                            f"Please check the Debug info output for a complete list of valid categories. "
                            f"Category names may have changed in a new version.")
                print(error_msg)
                raise ValueError(error_msg)
        
        # Set up categories dictionary - enable all categories except excluded ones
        categories = {category: (category not in excluded_categories) for category in all_categories}
        
        # Create the categories debug output
        categories_debug = "Available categories:\n" + "\n".join(all_categories)
        
        # Load categorized tags with error handling
        allowed_tags = []  # Changed from set to list to preserve order
        
        try:
            with open(categorized_tags_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Successfully read {len(content)} bytes from categorized tags file")
                
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('] ', 1)
                    if len(parts) != 2:
                        continue
                        
                    category = parts[0][1:]  # Remove the leading [
                    tag = parts[1]
                    
                    if categories.get(category):
                        allowed_tags.append(tag)  # Add the complete tag
                    
        except Exception as e:
            print(f"ERROR reading categorized tags file: {str(e)}")
            raise

        print(f"Loaded {len(allowed_tags)} allowed tags")

        # Parse exclude and include lists
        print("Processing exclude/include lists...")
        excluded_tags = set(self.normalize_tags(exclude_taglists_containing))
        included_tags = set(self.normalize_tags(taglists_must_include))
        print(f"Excluded tags count: {len(excluded_tags)}")
        print(f"Included tags count: {len(included_tags)}")

        # Collect all valid taglists from all enabled files
        print("Loading tag lists...")
        all_valid_taglists = []
        
        if use_general:
            all_valid_taglists.extend(self._load_taglist("taglists-general.txt", included_tags, excluded_tags, seed))
        if use_questionable:
            all_valid_taglists.extend(self._load_taglist("taglists-questionable.txt", included_tags, excluded_tags, seed))
        if use_sensitive:
            all_valid_taglists.extend(self._load_taglist("taglists-sensitive.txt", included_tags, excluded_tags, seed))
        if use_explicit:
            all_valid_taglists.extend(self._load_taglist("taglists-explicit.txt", included_tags, excluded_tags, seed))

        if not all_valid_taglists:
            print("No valid taglists found in any enabled category!")
            raise ValueError("No tags available - no matching taglists found")

        # Use seed to shuffle and select from all valid taglists
        rng = random.Random(seed)
        rng.shuffle(all_valid_taglists)
        
        # Take just 1 taglist based on seed
        selected_index = seed % len(all_valid_taglists)
        selected_taglist = all_valid_taglists[selected_index]
        
        # Extract just the taglist (without filename)
        _, unfiltered_taglist = selected_taglist
        # Normalize the unfiltered taglist for consistency in output
        unfiltered_taglist = ', '.join(self.normalize_tags(unfiltered_taglist))
        print(f"Selected taglist: {unfiltered_taglist}")
        print(f"Selected from {len(all_valid_taglists)} total valid taglists")

        # Split the taglist into individual tags and normalize them
        individual_tags = self.normalize_tags(unfiltered_taglist)

        # Filter tags using allowed_tags and maintain order
        print("Filtering tags...")
        allowed_tags_set = set(allowed_tags)  # For faster lookup
        filtered_tags = [tag for tag in individual_tags if tag in allowed_tags_set]
        print(f"Tags after allowed filter: {len(filtered_tags)}")
        
        try:
            filtered_tags.sort(key=lambda x: allowed_tags.index(x) if x in allowed_tags else len(allowed_tags))
        except Exception as e:
            print(f"Error during sorting: {e}")
            raise

        # Remove excluded tags
        filtered_tags = [tag for tag in filtered_tags if tag not in excluded_tags]
        print(f"Tags after exclusion filter: {len(filtered_tags)}")
        
        # Process negative prompt tags
        print("Processing negative prompt...")
        negative_tags = set(self.normalize_tags(negative_prompt))
        filtered_tags = [tag for tag in filtered_tags if tag not in negative_tags]
        print(f"Final tag count: {len(filtered_tags)}")

        # Process negative prompt 2 tags
        print("Processing negative prompt 2...")
        negative_tags_2 = set(self.normalize_tags(negative_prompt_2))
        filtered_tags = [tag for tag in filtered_tags if tag not in negative_tags_2]
        print(f"Final tag count after negative prompt 2: {len(filtered_tags)}")

        print("Preparing return values...")
        debug_info = f"Pool of Taglists size: {len(all_valid_taglists)}\n\n{categories_debug}"
        return_values = (
            ', '.join(filtered_tags),
            unfiltered_taglist,
            debug_info
        )
        print("Process complete")
        
        return return_values