# GPT Image 1 Base (for Open workflow)

`gpt-image-1` 모델을 빠르게 붙여 쓸 수 있는 최소 베이스 코드입니다.

## 준비

1. Python 3.10+
2. 의존성 설치

```bash
pip install -r requirements.txt
```

3. 환경변수 설정 (`.env`)

```bash
cp .env.example .env
# .env 파일에서 OPENAI_API_KEY 설정
```

## 실행

```bash
uvicorn app:app --reload --port 8000
```

## API

### 1) 이미지 생성

`POST /v1/images/generate`

```json
{
  "prompt": "A cinematic shot of Seoul at night, neon reflections on wet street",
  "size": "1024x1024",
  "quality": "high",
  "output_format": "png"
}
```

응답 예시:

```json
{
  "created": 1730000000,
  "mime_type": "image/png",
  "b64_json": "...",
  "revised_prompt": "...",
  "saved_file": "outputs/generated_1730000000.png"
}
```

### 2) 헬스체크

`GET /health`

## 참고

- 기본값은 `gpt-image-1`입니다.
- 응답의 `b64_json`은 이미지 바이너리를 base64로 담고 있습니다.
- 서버는 기본적으로 `outputs/` 폴더에 이미지를 저장합니다.
