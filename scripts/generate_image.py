import argparse
import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate an image with gpt-image-1")
    parser.add_argument("prompt", help="Image prompt")
    parser.add_argument("--model", default=os.getenv("DEFAULT_IMAGE_MODEL", "gpt-image-1"))
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--output-format", default="png")
    parser.add_argument("--background", default=None)
    parser.add_argument("--out", default=None, help="Output file path")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    base_url = os.getenv("OPENAI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)

    result = client.images.generate(
        model=args.model,
        prompt=args.prompt,
        size=args.size,
        quality=args.quality,
        output_format=args.output_format,
        background=args.background,
    )

    if not result.data or not getattr(result.data[0], "b64_json", None):
        raise RuntimeError("No image data returned")

    output = Path(args.out) if args.out else Path(f"generated.{args.output_format}")
    output.write_bytes(base64.b64decode(result.data[0].b64_json))
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
