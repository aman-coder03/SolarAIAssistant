import numpy as np
import torch
import os
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

MODEL_PATH = os.getenv("SAM_MODEL_PATH", "models/sam_vit_h.pth")

def load_sam_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"SAM model not found at {MODEL_PATH}. "
            "Set SAM_MODEL_PATH or place model file correctly."
        )

    sam = sam_model_registry["vit_h"](checkpoint=MODEL_PATH)
    sam.to(device="cuda" if torch.cuda.is_available() else "cpu")
    return sam


def get_rooftop_mask(image_pil, sam):
    image_np = np.array(image_pil)
    generator = SamAutomaticMaskGenerator(sam)
    masks = generator.generate(image_np)

    if not masks:
        return None

    largest = max(masks, key=lambda x: x["area"])
    return largest["segmentation"]
