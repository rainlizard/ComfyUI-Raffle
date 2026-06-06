import os
import re


class SortTagsByPopularity:
    _allowed_tags_cache = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_tags": ("STRING", {
                    "multiline": True,
                    "forceInput": True,
                    "default": "",
                    "tooltip": "Input tags to sort by Raffle's categorized tag order (comma-separated)"
                }),
            },
            "optional": {
                "remove_duplicates": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Remove duplicate tags while sorting"
                }),
            }
        }

    CATEGORY = "Raffle"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("sorted_tags", "unsorted_tags")
    OUTPUT_TOOLTIPS = (
        "Tags found in categorized_tags.txt, sorted by Raffle's categorized tag order",
        "Tags not found in categorized_tags.txt, preserved separately"
    )
    FUNCTION = "sort_tags"

    def _load_allowed_tags(self):
        if SortTagsByPopularity._allowed_tags_cache is not None:
            return SortTagsByPopularity._allowed_tags_cache

        extension_path = os.path.normpath(os.path.dirname(__file__))
        categorized_tags_file_path = os.path.join(extension_path, "lists", "categorized_tags.txt")

        if not os.path.exists(categorized_tags_file_path):
            raise ValueError(f"Categorized tags file not found at {categorized_tags_file_path}")

        allowed_tags = []

        try:
            with open(categorized_tags_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split('] ', 1)
                    if len(parts) != 2:
                        continue

                    allowed_tags.append(parts[1])
        except Exception as e:
            raise ValueError(f"Error reading categorized tags file: {str(e)}")

        SortTagsByPopularity._allowed_tags_cache = allowed_tags
        return allowed_tags

    def _normalize_tags(self, tag_string):
        tag_string = tag_string.replace('\r\n', '\n')
        tag_string = tag_string.replace('\n', ',')

        while '  ' in tag_string:
            tag_string = tag_string.replace('  ', ' ')

        while ',,' in tag_string:
            tag_string = tag_string.replace(',,', ',')

        tags = tag_string.replace(', ', ',').split(',')
        return [
            tag.strip()
            for tag in tags
            if tag.strip()
        ]

    def _canonicalize_tag_name(self, tag_name):
        return tag_name.strip().replace(' ', '_')

    def _extract_tag_name(self, tag):
        weight_pattern = r'^\(([^:]+):([^)]+)\)$'
        match = re.match(weight_pattern, tag)

        if match:
            return match.group(1).strip()

        return tag

    def _deduplicate_tags(self, tags):
        seen = set()
        deduplicated_tags = []

        for tag in tags:
            tag_name = self._canonicalize_tag_name(self._extract_tag_name(tag))
            if tag_name in seen:
                continue

            seen.add(tag_name)
            deduplicated_tags.append(tag)

        return deduplicated_tags

    def sort_tags(self, input_tags, remove_duplicates=False):
        input_str = input_tags if isinstance(input_tags, str) else ""
        lora_pattern = r'<lora:[^>]+>'

        lora_tags = re.findall(lora_pattern, input_str)
        input_without_lora = re.sub(lora_pattern, '', input_str)
        regular_tags = self._normalize_tags(input_without_lora)

        if remove_duplicates:
            regular_tags = self._deduplicate_tags(regular_tags)
            lora_tags = self._deduplicate_tags(lora_tags)

        allowed_tags = self._load_allowed_tags()
        allowed_tag_indexes = {
            self._canonicalize_tag_name(tag): index
            for index, tag in enumerate(allowed_tags)
        }

        sorted_tags = [
            tag for tag in regular_tags
            if self._canonicalize_tag_name(self._extract_tag_name(tag)) in allowed_tag_indexes
        ]
        sorted_tags.sort(
            key=lambda tag: allowed_tag_indexes[
                self._canonicalize_tag_name(self._extract_tag_name(tag))
            ]
        )

        unsorted_tags = [
            tag for tag in regular_tags
            if self._canonicalize_tag_name(self._extract_tag_name(tag)) not in allowed_tag_indexes
        ]
        unsorted_tags.extend(lora_tags)

        if not sorted_tags and not unsorted_tags:
            return "", ""

        return ", ".join(sorted_tags), ", ".join(unsorted_tags)
