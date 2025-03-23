import os
import folder_paths
import random

# Default values for Raffle node
DEFAULT_FILTER_OUT_TAGS = """monochrome, greyscale,
anus, anus_peek, spread_anus, spreading_own_anus, spread_anus_under_clothes,
anal, anal_only, after_anal, anal_fluid,
anal_object_insertion, butt_plug, jewel_butt_plug, anal_beads,
gaping, extreme_gaping,
prolapse, anal_prolapse, fisting, anal_fisting,
cross-section, cervix, cervical_penetration, uterus, internal_cumshot, x-ray,
lactation, forced_lactation, male_lactation, projectile_lactation, lactation_through_clothes, breast_milk,
female_pubic_hair, pubic_hair, pubic_hair_peek,
male_focus, male_penetrated, interracial, dark-skinned_male,
condom, used_condom, condom_wrapper, condom_in_mouth, holding_condom, condom_on_penis, multiple_condoms, condom_packet_strip, pointless_condom, condom_belt, condom_box, used_condom_on_penis, condom_left_inside, colored_condom, okamoto_condoms, condom_wrapper_in_clothes, condom_thigh_strap, buying_condoms, broken_condom, used_condom_in_clothes"""

DEFAULT_EXCLUDE_TAGLISTS = "comic, 4koma, multiple_girls, multiple_boys, multiple_views, reference_sheet, 2girls, 3girls, 4girls, 5girls, 6+girls, 2boys, 3boys, 4boys, 5boys, 6+boys, gangbang, threesome, mmf_threesome, ffm_threesome, group_sex, cooperative_fellatio, cooperative_paizuri, double_handjob, surrounded_by_penises, furry, obese, yaoi, yuri, otoko_no_ko, strap-on, futa_with_female, futa_without_pussy, implied_futanari, futanari, diaper, fart, pee, peeing, pee_puddle, pee_stain, peeing_self, golden_shower, scat, guro, ero_guro, intestines, vore, horse_penis"

DEFAULT_EXCLUDE_CATEGORIES = "clothes_and_accessories, female_physical_descriptors, named_garment_exposure, specific_garment_interactions, speech_and_text, standard_physical_descriptors, metadata_and_attribution, intentional_design_exposure, two_handed_character_items, holding_large_items, content_censorship_methods"

class Raffle:
    @classmethod
    def INPUT_TYPES(s):
        extension_path = os.path.normpath(os.path.dirname(__file__))
        
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
                    "tooltip": "<taglists_must_include> Only selects taglists that contain ALL of these tags. WARNING: Each tag added here severely reduces the available pool of taglists. Check the 'Debug info' output to see how many taglists remain available."
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "forceInput": True,
                    "default": "",
                    "tooltip": "<negative_prompt> Removes specific tags from the final output without affecting taglist selection. Tags listed here will be filtered out after a taglist is chosen, making this safer to use than 'exclude_taglists_containing'."
                }),
                "filter_out_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_FILTER_OUT_TAGS,
                    "tooltip": "<filter_out_tags> Additional tags to filter out from the final output. Use this to exclude more tags without needing to modify your main negative prompt."
                }),
                "exclude_taglists_containing": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_EXCLUDE_TAGLISTS,
                    "tooltip": "<exclude_taglists_containing> If ANY of these tags appear in the taglist, the entire taglist is removed from the pool of available taglists. Use with caution as each tag listed here can significantly reduce options. For removing individual tags without reducing the pool, use 'filter_out_tags' instead."
                }),
                "exclude_tag_categories": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_EXCLUDE_CATEGORIES,
                    "tooltip": "<exclude_tag_categories> Exclude entire categories of tags from the final output. Each category contains related tags (e.g., 'poses' contains all pose-related tags). View the complete category list and their tags in the 'Debug info' output. Separate multiple categories with commas."
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
        extension_path = os.path.normpath(os.path.dirname(__file__))
        filepath = os.path.join(extension_path, "lists", filename)
        
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
            raise
        
        return []

    def normalize_tags(self, tag_string):
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
                    negative_prompt="", filter_out_tags="",
                    use_general=True, use_questionable=False, use_sensitive=False, use_explicit=False,
                    exclude_tag_categories=""):
        
        # Add directory existence check
        extension_path = os.path.normpath(os.path.dirname(__file__))
        lists_path = os.path.join(extension_path, "lists")
        
        if not os.path.exists(lists_path):
            raise ValueError(f"Lists directory not found at {lists_path}")

        # Check for categorized tags file
        categorized_tags_file_path = os.path.join(lists_path, "categorized_tags.txt")
        
        if not os.path.exists(categorized_tags_file_path):
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
        if exclude_tag_categories.strip():
            excluded_categories = self.normalize_tags(exclude_tag_categories)
            
            # Check if all excluded categories are valid
            invalid_categories = [c for c in excluded_categories if c not in all_categories]
            if invalid_categories:
                error_msg = (f"Error: Invalid category names: {', '.join(invalid_categories)}. "
                            f"Please check the Debug info output for a complete list of valid categories. "
                            f"Category names may have changed in a new version.")
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
            raise

        # Parse exclude and include lists
        excluded_tags = set(self.normalize_tags(exclude_taglists_containing))
        included_tags = set(self.normalize_tags(taglists_must_include))

        # Collect all valid taglists from all enabled files
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

        # Split the taglist into individual tags and normalize them
        individual_tags = self.normalize_tags(unfiltered_taglist)

        # Filter tags using allowed_tags and maintain order
        allowed_tags_set = set(allowed_tags)  # For faster lookup
        filtered_tags = [tag for tag in individual_tags if tag in allowed_tags_set]
        
        try:
            filtered_tags.sort(key=lambda x: allowed_tags.index(x) if x in allowed_tags else len(allowed_tags))
        except Exception as e:
            raise

        # Remove excluded tags
        filtered_tags = [tag for tag in filtered_tags if tag not in excluded_tags]
        
        # Process negative prompt tags
        negative_tags = set(self.normalize_tags(negative_prompt))
        filtered_tags = [tag for tag in filtered_tags if tag not in negative_tags]

        # Process negative prompt 2 tags
        filter_out_tags_set = set(self.normalize_tags(filter_out_tags))
        filtered_tags = [tag for tag in filtered_tags if tag not in filter_out_tags_set]

        debug_info = f"Taglist pool size: {len(all_valid_taglists)}\n\n{categories_debug}"
        return_values = (
            ', '.join(filtered_tags),
            unfiltered_taglist,
            debug_info
        )
        
        return return_values