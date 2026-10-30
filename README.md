# 나와 닮은 동물상 테스트

사진을 업로드하면 MobileNetV2 이미지 분류 결과를 강아지상·고양이상·토끼상·여우상으로 단순 환산해 보여주는 로컬 웹앱입니다. 결과는 실제 외모나 성격을 판단하지 않는 재미용 추정치입니다.

## 사용 환경

- Python 3.10 이상
- Windows PowerShell 또는 일반 터미널
- CPU만으로 실행 가능

## 설치

가상환경 없이도 실행할 수 있습니다.

```powershell
cd upload
python -m pip install -r requirements.txt
```

`python` 명령이 동작하지 않으면 설치된 Python의 실행 파일 경로를 사용하세요.

## 모델 준비

GitHub에 대용량 모델을 포함하지 않았으므로 아래 명령으로 모델 폴더를 만들고 MobileNetV2 ONNX 모델을 다운로드합니다.

```powershell
New-Item -ItemType Directory -Force models | Out-Null
Invoke-WebRequest `
  -Uri "https://github.com/onnx/models/raw/main/validated/vision/classification/mobilenet/model/mobilenetv2-7.onnx" `
  -OutFile "models/mobilenetv2-7.onnx"
```

## 실행

```powershell
uvicorn app:app --host 127.0.0.1 --port 8765
```

브라우저에서 http://127.0.0.1:8765 를 열고 JPG, PNG 또는 WEBP 사진을 업로드하세요.

## 구성

- `app.py`: FastAPI 서버 및 이미지 분석 API
- `static/`: HTML, CSS, JavaScript 사용자 화면
- `requirements.txt`: Python 의존성
- `models/`: 사용자가 별도로 준비하는 모델 폴더

