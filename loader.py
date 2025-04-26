import torch
import torchvision.transforms as T
from torchvision import models
from pathlib import Path

__all__ = ["load_model"]

LABELS = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']
MODEL_PATH = Path(__file__).parent / "best.pt"


def load_model(device="cpu"):
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
