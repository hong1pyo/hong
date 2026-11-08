FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
ARG MODEL_VERSION=mobilev2-preprocess-v2
ENV MODEL_VERSION=${MODEL_VERSION} PREPROCESS_VARIANT=center-crop

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY static ./static

# Keep the large model out of Git and fetch the pinned, verified artifact at build time.
RUN mkdir -p models \
 && python -c "from urllib.request import urlretrieve; urlretrieve('https://github.com/onnx/models/raw/main/validated/vision/classification/mobilenet/model/mobilenetv2-7.onnx', 'models/mobilenetv2-7.onnx')" \
 && echo 'C1C513582D56AFCEFF8516C73804E484C81C6A830712AB6D682253F4A3CD042F  models/mobilenetv2-7.onnx' | sha256sum -c -

# Build-time smoke test: imports the app, loads ONNX Runtime and runs one CPU inference.
RUN python -c "from io import BytesIO; import numpy as np; from PIL import Image; import app; assert app.session is not None, 'MobileNet model did not load'; x=Image.new('RGB',(224,224),'white'); result=app.analyze(x); assert abs(sum(result['results'].values())-100.0) < 0.2; print('model smoke test passed:', result['winner'])"

EXPOSE 8765
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8765"]
