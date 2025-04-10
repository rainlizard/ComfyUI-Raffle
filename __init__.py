from . import raffle
from . import preview_history  # Import the renamed module
from .raffle import Raffle
from .preview_history import PreviewHistory # Import the renamed class

NODE_CLASS_MAPPINGS = {
    "Raffle": Raffle,
    "PreviewHistory": PreviewHistory  # Add the renamed mapping
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Raffle": "Raffle",
    "PreviewHistory": "Preview History (Raffle)" # Add the renamed display name
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
