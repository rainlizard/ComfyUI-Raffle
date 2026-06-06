from . import raffle
from . import preview_history  # Import the renamed module
from . import tag_category_strength  # Import the new module
from . import curved_rescale_cfg  # Import the curved rescale cfg module
from . import sort_tags_by_popularity  # Import the sort tags by popularity module
from .raffle import Raffle
from .preview_history import PreviewHistory # Import the renamed class
from .tag_category_strength import TagCategoryStrength # Import the new class
from .curved_rescale_cfg import CurvedRescaleCFG # Import the curved rescale cfg class
from .sort_tags_by_popularity import SortTagsByPopularity # Import the sort tags by popularity class

NODE_CLASS_MAPPINGS = {
    "Raffle": Raffle,
    "PreviewHistory": PreviewHistory,  # Add the renamed mapping
    "TagCategoryStrength": TagCategoryStrength,  # Add the new mapping
    "CurvedRescaleCFG": CurvedRescaleCFG,  # Add the curved rescale cfg mapping
    "SortTagsByPopularity": SortTagsByPopularity  # Add the sort tags by popularity mapping
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Raffle": "Raffle",
    "PreviewHistory": "Preview History (Raffle)",  # Add the renamed display name
    "TagCategoryStrength": "Tag Category Strength (Raffle)",  # Add the new display name
    "CurvedRescaleCFG": "Curved Rescale CFG (Raffle)",  # Add the curved rescale cfg display name
    "SortTagsByPopularity": "Sort Tags By Popularity (Raffle)"  # Add the sort tags by popularity display name
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
