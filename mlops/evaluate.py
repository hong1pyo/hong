"""Deterministic 30/70 evaluation against a public Hugging Face cat/dog split."""
import json
import sys
from pathlib import Path
from io import BytesIO
from urllib.parse import urlencode
from urllib.request import urlopen
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

DATASET = "Pratheesh99/animal-faces-raw"
SPLIT = "val"
N_TUNE, N_TEST = 30, 70

def load_rows():
    query = urlencode({"dataset": DATASET, "config": "default", "split": SPLIT, "offset": 0, "length": 100})
    with urlopen("https://datasets-server.huggingface.co/first-rows?" + query, timeout=60) as response:
        rows = json.load(response)["rows"]
    if len(rows) != 100:
        raise RuntimeError(f"Expected 100 rows, got {len(rows)}")
    images = []
    for item in rows:
        with urlopen(item["row"]["image"]["src"], timeout=60) as response:
            images.append((Image.open(BytesIO(response.read())).convert("RGB"), int(item["row"]["label"])))
    return images

def tensor(image, variant):
    if variant == "center-crop":
        side = min(image.size)
        left, top = (image.width - side) // 2, (image.height - side) // 2
        image = image.crop((left, top, left + side, top + side))
    image = image.resize((224, 224), Image.Resampling.BILINEAR)
    data = np.asarray(image, dtype=np.float32) / 255.0
    data = (data - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array([0.229, 0.224, 0.225], dtype=np.float32)
    return np.transpose(data, (2, 0, 1))[None].astype(np.float32)

def predict(image, variant):
    inp = app.session.get_inputs()[0]
    output = app.session.run(None, {inp.name: tensor(image, variant)})[0][0]
    exp = np.exp(output - np.max(output))
    probs = exp / exp.sum()
    cat = float(probs[281:286].sum())
    dog = float(probs[151:269].sum())
    return 0 if cat >= dog else 1

def score(items, variant):
    correct = sum(predict(image, variant) == label for image, label in items)
    return {"correct": correct, "total": len(items), "accuracy": round(correct / len(items), 4)}

def main():
    if app.session is None:
        raise RuntimeError("ONNX model is not loaded")
    items = load_rows()
    tune, test = items[:N_TUNE], items[N_TUNE:N_TUNE + N_TEST]
    baseline_tune = score(tune, "resize")
    improved_tune = score(tune, "center-crop")
    # Deterministic tie-break selects the deployable candidate; final accuracy is
    # still reported against the unchanged baseline on the untouched 70 rows.
    chosen = "center-crop" if improved_tune["accuracy"] >= baseline_tune["accuracy"] else "resize"
    result = {"dataset": DATASET, "split": SPLIT, "rows": 100, "tuning_rows": 30,
              "evaluation_rows": 70, "baseline_tuning": baseline_tune,
              "candidate_tuning": improved_tune, "selected_preprocess": chosen,
              "baseline_final": score(test, "resize"), "selected_final": score(test, chosen)}
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
