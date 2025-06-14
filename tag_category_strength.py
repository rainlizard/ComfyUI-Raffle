import os
import re

# Import the global categories list from raffle.py
from .raffle import ALL_CATEGORIES

class TagCategoryStrength:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_tags": ("STRING", {
                    "multiline": True,
                    "forceInput": True,
                    "default": "",
                    "tooltip": "Input tags to adjust (comma-separated)"
                }),
                "category_adjustments": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Category adjustments in format: (category_name:strength), e.g., (artist:1.4), (meta:0.5), (poses:1.2)"
                }),
            },
            "optional": {
                "preserve_existing_weights": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "If enabled, tags that already have weights like (tag:1.2) will keep their existing weights instead of being adjusted"
                }),
            }
        }

    CATEGORY = "Raffle"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("Adjusted tags", "Debug info")
    OUTPUT_TOOLTIPS = (
        "Tags with category-based strength adjustments applied",
        "Information about which tags were adjusted and their categories"
    )
    FUNCTION = "adjust_tag_categories"

    def __init__(self):
        self._tag_to_category_cache = None



    def _load_tag_categories(self):
        """Load the tag-to-category mapping from categorized_tags.txt"""
        if self._tag_to_category_cache is not None:
            return self._tag_to_category_cache

        extension_path = os.path.normpath(os.path.dirname(__file__))
        categorized_tags_file_path = os.path.join(extension_path, "lists", "categorized_tags.txt")
        
        if not os.path.exists(categorized_tags_file_path):
            raise ValueError(f"Categorized tags file not found at {categorized_tags_file_path}")

        tag_to_category = {}
        
        try:
            with open(categorized_tags_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse format: [category] tag
                    parts = line.split('] ', 1)
                    if len(parts) != 2:
                        continue
                        
                    category = parts[0][1:]  # Remove the leading [
                    tag = parts[1]
                    
                    tag_to_category[tag] = category
                    
        except Exception as e:
            raise ValueError(f"Error reading categorized tags file: {str(e)}")

        self._tag_to_category_cache = tag_to_category
        return tag_to_category

    def _parse_category_adjustments(self, adjustments_string):
        """Parse category adjustments from string format like (category:strength)"""
        adjustments = {}
        
        if not adjustments_string.strip():
            return adjustments
            
        # Get valid categories for validation
        valid_categories_set = set(ALL_CATEGORIES)
        
        # Split by commas and validate each part
        parts = [part.strip() for part in adjustments_string.split(',') if part.strip()]
        
        # Pattern for valid format: (category:strength)
        pattern = r'^\(([^:]+):([^)]+)\)$'
        
        for part in parts:
            match = re.match(pattern, part)
            
            if not match:
                # This part doesn't match the expected format
                raise ValueError(f"Invalid format '{part}'. Expected format: (category:strength), e.g., (artist:1.4)")
            
            category, strength = match.groups()
            category = category.strip()
            
            # Validate that the category exists in the valid categories
            if category not in valid_categories_set:
                valid_categories_str = ', '.join(sorted(ALL_CATEGORIES))
                raise ValueError(f"Invalid category '{category}'. Valid categories are: {valid_categories_str}")
            
            try:
                strength_value = float(strength.strip())
                adjustments[category] = strength_value
            except ValueError:
                raise ValueError(f"Invalid strength value '{strength}' for category '{category}'. Must be a number.")
                
        return adjustments

    def _normalize_tags(self, tag_string):
        """Normalize a string of tags to a consistent format"""
        # Replace newlines with commas
        tag_string = tag_string.replace('\r\n', '\n')
        tag_string = tag_string.replace('\n', ',')
        
        # Remove multiple consecutive spaces
        while '  ' in tag_string:
            tag_string = tag_string.replace('  ', ' ')
            
        # Remove multiple consecutive commas
        while ',,' in tag_string:
            tag_string = tag_string.replace(',,', ',')
        
        # Split on commas and normalize each tag
        tags = tag_string.replace(', ', ',').split(',')
        
        return [tag.strip() for tag in tags if tag.strip()]

    def _extract_tag_and_weight(self, tag):
        """Extract tag name and existing weight from a tag like 'tag' or '(tag:1.2)'"""
        tag = tag.strip()
        
        # Check if tag already has weight in format (tag:weight)
        weight_pattern = r'^\(([^:]+):([^)]+)\)$'
        match = re.match(weight_pattern, tag)
        
        if match:
            tag_name = match.group(1).strip()
            try:
                weight = float(match.group(2).strip())
                return tag_name, weight
            except ValueError:
                # If weight is invalid, treat as regular tag
                return tag, None
        else:
            return tag, None

    def _apply_weight_to_tag(self, tag_name, weight):
        """Apply weight to a tag, formatting it as (tag:weight)"""
        if weight == 1.0:
            return tag_name
        else:
            return f"({tag_name}:{weight})"

    def adjust_tag_categories(self, input_tags, category_adjustments, preserve_existing_weights=True):
        # Load tag-to-category mapping
        tag_to_category = self._load_tag_categories()
        
        # Parse category adjustments
        adjustments = self._parse_category_adjustments(category_adjustments)
        
        # Normalize input tags
        tags = self._normalize_tags(input_tags)
        
        if not tags:
            return "", "No input tags provided"
        
        adjusted_tags = []
        debug_info = []
        
        for tag in tags:
            # Extract tag name and existing weight
            tag_name, existing_weight = self._extract_tag_and_weight(tag)
            
            # Normalize tag name (replace spaces with underscores for lookup)
            normalized_tag_name = tag_name.replace(' ', '_')
            
            # Find category for this tag
            category = tag_to_category.get(normalized_tag_name)
            
            if category and category in adjustments:
                # This tag has a category adjustment
                adjustment_strength = adjustments[category]
                
                if preserve_existing_weights and existing_weight is not None:
                    # Keep existing weight
                    final_weight = existing_weight
                    adjusted_tags.append(self._apply_weight_to_tag(tag_name, final_weight))
                    debug_info.append(f"{tag_name} [{category}] - kept existing weight: {final_weight}")
                else:
                    # Apply category adjustment
                    if existing_weight is not None:
                        # Multiply existing weight by adjustment
                        final_weight = existing_weight * adjustment_strength
                    else:
                        # Apply adjustment to default weight of 1.0
                        final_weight = adjustment_strength
                    
                    adjusted_tags.append(self._apply_weight_to_tag(tag_name, final_weight))
                    debug_info.append(f"{tag_name} [{category}] - adjusted to: {final_weight}")
            else:
                # No adjustment for this tag
                adjusted_tags.append(tag)
                if category:
                    debug_info.append(f"{tag_name} [{category}] - no adjustment")
                else:
                    debug_info.append(f"{tag_name} [unknown category] - no adjustment")
        
        # Create debug output
        debug_output = f"Applied adjustments: {adjustments}\n\nTag adjustments:\n" + "\n".join(debug_info)
        
        return ", ".join(adjusted_tags), debug_output 