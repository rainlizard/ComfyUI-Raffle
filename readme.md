# Raffle

A semi-random prompt generator for danbooru tags that works alongside your character prompt, allowing you to put your waifu in many scenarios. Made for Illustrious/NoobAI/Pony, or any models supporting tag prompting.

## Quick Start

1. From within ComfyUI Manager, search for Raffle and install it
2. Add the Raffle node to your workflow
3. Connect your Negative Prompt to the "negative_prompt" input (you may need to convert it to a `text` node first)
4. Use the "Filtered tags" output in your Positive Prompt (merge it with a `text concat` or `string concat` node)

Download the workflow example for detailed implementation: [Raffle Example.json](https://raw.githubusercontent.com/rainlizard/ComfyUI-Raffle/main/Raffle%20Example.json)

## How It Works

For offline use 400,000 taglists have been scraped from danbooru. Raffle randomly selects one of these taglists and filters it according to your preferences. A taglist is a collection of tags that have been applied to one image on danbooru, by using taglists we can be certain that the tags have good synergy with each other.

### Selection Process
1. Raffle first filters the pool of available taglists based on:
   - `use_general`, `use_questionable`, `use_sensitive`, `use_explicit`
   - `exclude_taglists_containing`
   - `taglists_must_include`
   - `exclude_tag_categories`
2. It randomly selects one taglist from this filtered pool using your provided seed
3. That selected taglist is then filtered by:
   - `negative_prompt`
   - `filter_out_tags`
   - if the tag isn't even in `categorized_tags.txt` then it's also filtered
4. The final result is the `Filtered tags` output. You can use this in your Positive Prompt.

## Node Options
- **use_general**: Enable selection from general.txt which contains 100,000 general taglists
- **use_questionable**: Enable selection from questionable.txt which contains 100,000 questionable taglists
- **use_sensitive**: Enable selection from sensitive.txt which contains 100,000 sensitive taglists
- **use_explicit**: Enable selection from explicit.txt which contains 100,000 explicit taglists
- **seed**: Controls which taglist is randomly selected from the filtered pool
- **taglists_must_include**: Only selects taglists that contain ALL of these tags. Use sparingly as each tag added severely reduces the available pool of taglists.
- **negative_prompt**: Connect your existing negative prompt here to ensure none of those tags appear in the output
- **filter_out_tags**: Additional tags to filter out from the final output without modifying your main negative prompt
- **exclude_taglists_containing**: If ANY of these tags appear in a taglist, the entire taglist is removed from consideration. Use with caution as this can significantly reduce options.
- **exclude_tag_categories**: Exclude entire categories of tags (e.g., "clothes_and_accessories", "standard_physical_descriptors") from the final output

## Node Outputs
- **Filtered tags**: The final list of tags ready to use in your prompt
- **Unfiltered tags**: The complete original taglist before filtering (for debugging)
- **Debug info**: Information about the selection process, including available taglist count

## Categories

I've used AI to help categorize 20,000 tags in `categorized_tags.txt`, this includes any tag with more than 100 entries on danbooru. The categorization method isn't perfect, but it's what I've ended up with:

- `abstract_symbols`
- `actions`
- `artstyle_technique`
- `background_objects`
- `bodily_fluids`
- `camera_angle_perspective`
- `camera_focus_subject`
- `camera_framing_composition`
- `character_count`
- `clothes_and_accessories`
- `color_scheme`
- `content_censorship_methods`
- `expressions_and_mental_state`
- `female_intimate_anatomy`
- `female_physical_descriptors`
- `format_and_presentation`
- `gaze_direction_and_eye_contact`
- `general_clothing_exposure`
- `generic_clothing_interactions`
- `holding_large_items`
- `holding_small_items`
- `intentional_design_exposure`
- `lighting_and_vfx`
- `male_intimate_anatomy`
- `male_physical_descriptors`
- `metadata_and_attribution`
- `named_garment_exposure`
- `nudity_and_absence_of_clothing`
- `one_handed_character_items`
- `physical_locations`
- `poses`
- `publicly_visible_anatomy`
- `relationships`
- `sex_acts`
- `sfw_clothed_anatomy`
- `special_backgrounds`
- `specific_garment_interactions`
- `speech_and_text`
- `standard_physical_descriptors`
- `thematic_settings`
- `two_handed_character_items`
