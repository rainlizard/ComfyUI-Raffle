from . import raffle
from . import preview_history  # Import the renamed module
from . import tag_category_strength  # Import the new module
from .raffle import Raffle
from .preview_history import PreviewHistory # Import the renamed class
from .tag_category_strength import TagCategoryStrength # Import the new class

NODE_CLASS_MAPPINGS = {
    "Raffle": Raffle,
    "PreviewHistory": PreviewHistory,  # Add the renamed mapping
    "TagCategoryStrength": TagCategoryStrength  # Add the new mapping
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Raffle": "Raffle",
    "PreviewHistory": "Preview History (Raffle)",  # Add the renamed display name
    "TagCategoryStrength": "Tag Category Strength (Raffle)"  # Add the new display name
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
