A semi-random prompt generator for danbooru tags, designed to work with your character prompts. (Illustrious/Pony)

Definitions

`taglist`: If you open an image on the danbooru website you will see a list of tags on the left-hand side that have been applied to that specific image, this is what we're calling the taglist - a grouping of multiple tags.

`pool of taglists`: Inside the `/lists/` directory you will find files called `general.txt`, `questionable.txt`, `sensitive.txt`, `explicit.txt`. Each one of these files contains 100,000 lines, and each line contains a list of tags. This 100,000 number is the entire pool of taglists and this pool is filtered by: `taglists_must_include` and `exclude_taglists_containing`.

The way this prompt generator works is it filters the pool of taglists and then filters the taglist itself.
Here's some instructions on how the fields work.

`taglists_must_include`: this will reduce the pool of taglists, as each word written here must be in the taglist. So if you write a bunch of tags here, the pool will become very small very quickly. You should leave this blank unless you're wanting a specific output.

`negative_prompt`: wire in your usual negative prompt here, so that we can be sure to that none of the tags in your negative prompt appear in the "Filtered Tags" output.

`negative_prompt_2`: This field is just for convenience and will be combined with your negative_prompt. You can filter out more tags here, instead of needing to fill up your main negative_prompt with hundreds of tags.

`exclude_taglists_containing`: The reason you would write tags here instead of negative_prompt_2 is because filtering the individual tag may not be enough, you may want to throw out the entire taglist instead, if you believe the presence of the tag ruins the whole taglist.

Note: this custom node's biggest limitation right now is it has only categorized 6568 tags, you can find this file in `/lists/categorized_tags.txt` and only tags in this list will appear in your output. More obscure tags will not appear in your outputs.