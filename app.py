from pathlib import Path
from io import BytesIO
from typing import Annotated
import json

import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

try:
    import onnxruntime as ort
except ImportError:
    ort = None

ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "models" / "mobilenetv2-7.onnx"
MAX_BYTES = 10 * 1024 * 1024
ALLOWED = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(title="나와 닮은 동물상 테스트")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
session = None
if ort and MODEL_PATH.exists():
    session = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])

# MobileNet ImageNet class IDs: dog breeds 151-268, cat 281-285, rabbit 330,
# foxes 277-280. These groups are converted into a playful face-animal estimate.
GROUPS = {
    "강아지상": list(range(151, 269)),
    "고양이상": list(range(281, 286)),
    "토끼상": [330],
    "여우상": list(range(277, 281)),
}

def preprocess(image: Image.Image) -> np.ndarray:
    image = image.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
    data = np.asarray(image, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    data = (data - mean) / std
    return np.transpose(data, (2, 0, 1))[None, ...].astype(np.float32)

def analyze(image: Image.Image):
    if session is None:
        raise RuntimeError("모델 파일이 없습니다. models/mobilenetv2-7.onnx를 준비해 주세요.")
    inp = session.get_inputs()[0]
    output = session.run(None, {inp.name: preprocess(image)})[0][0]
    exp = np.exp(output - np.max(output))
    probs = exp / exp.sum()
    scores = {name: float(sum(probs[i] for i in ids)) for name, ids in GROUPS.items()}
    # ImageNet's dog-heavy output can dwarf the other groups, so retain a fun
    # four-way distribution while preserving relative model evidence.
    floor = 0.04
    adjusted = {k: v + floor for k, v in scores.items()}
    total = sum(adjusted.values())
    percentages = {k: round(v / total * 100, 1) for k, v in adjusted.items()}
    winner = max(percentages, key=percentages.get)
    return {"winner": winner, "results": percentages,
            "note": "MobileNet ImageNet 분류 결과를 동물 그룹으로 단순 환산한 재미용 추정치입니다."}

@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/status")
def status():
    return {"model_ready": session is not None, "model": "MobileNetV2 (ONNX, CPU)"}

@app.post("/api/analyze")
async def api_analyze(file: Annotated[UploadFile, File(...)]):
    if file.content_type not in ALLOWED:
        raise HTTPException(400, "JPG, PNG, WEBP 이미지 파일만 업로드할 수 있어요.")
    data = await file.read()
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(400, "이미지는 비어 있지 않아야 하며 10MB 이하만 가능해요.")
    try:
        image = Image.open(BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "파일 내용을 이미지로 읽을 수 없어요.")
    try:
        return analyze(image)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))

