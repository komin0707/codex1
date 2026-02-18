import base64
import os
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI


load_dotenv()


def _create_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


app = FastAPI(title="GPT Image 1 Base API", version="0.1.0")


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Image generation prompt")
    model: str = Field(default_factory=lambda: os.getenv("DEFAULT_IMAGE_MODEL", "gpt-image-1"))
    size: str = Field(default="1024x1024", description="e.g. 1024x1024")
    quality: str = Field(default="high", description="low|medium|high")
    output_format: str = Field(default="png", description="png|jpeg|webp")
    background: Optional[str] = Field(default=None, description="transparent|opaque|auto")
    n: int = Field(default=1, ge=1, le=4)
    save_file: bool = Field(default=True, description="Save generated image under OUTPUT_DIR")


class GenerateImageResponse(BaseModel):
    created: int
    mime_type: str
    b64_json: str
    revised_prompt: Optional[str] = None
    saved_file: Optional[str] = None


@app.get("/health")
def health() -> dict:
    return {"ok": True, "model": os.getenv("DEFAULT_IMAGE_MODEL", "gpt-image-1")}


@app.post("/v1/images/generate", response_model=GenerateImageResponse)
def generate_image(req: GenerateImageRequest) -> GenerateImageResponse:
    try:
        client = _create_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        response = client.images.generate(
            model=req.model,
            prompt=req.prompt,
            size=req.size,
            quality=req.quality,
            output_format=req.output_format,
            background=req.background,
            n=req.n,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {exc}") from exc

    if not response.data:
        raise HTTPException(status_code=500, detail="No image data returned from API")

    first = response.data[0]
    b64_json = getattr(first, "b64_json", None)
    revised_prompt = getattr(first, "revised_prompt", None)

    if not b64_json:
        raise HTTPException(status_code=500, detail="No b64_json field in image response")

    mime_type = f"image/{req.output_format}"
    saved_file = None

    if req.save_file:
        output_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
        output_dir.mkdir(parents=True, exist_ok=True)
        now = int(time.time())
        path = output_dir / f"generated_{now}.{req.output_format}"
        path.write_bytes(base64.b64decode(b64_json))
        saved_file = str(path)

    return GenerateImageResponse(
        created=int(time.time()),
        mime_type=mime_type,
        b64_json=b64_json,
        revised_prompt=revised_prompt,
        saved_file=saved_file,
    )
