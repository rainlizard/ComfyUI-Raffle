from . import raffle
from .raffle import Raffle

NODE_CLASS_MAPPINGS = {
    "Raffle": Raffle
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Raffle": "Raffle"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
