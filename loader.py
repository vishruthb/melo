import torch
import torchvision.transforms as T
from torchvision import models
from pathlib import Path

__all__ = ["load_model"]

LABELS = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']
MODEL_PATH = Path(__file__).parent / "best.pt"


def load_model(device="cpu"):
    """Return (model, labels, transform).

    * **model** – EfficientNet‑B0 with a 7‑class head
    * **labels** – ordered label list
    * **transform** – torchvision transform for inference
    """
    model = models.efficientnet_b0()
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(LABELS))
    state = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(state)
    model.eval().to(device)

    transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize([0.5] * 3, [0.5] * 3),
    ])
    return model, LABELS, transform
