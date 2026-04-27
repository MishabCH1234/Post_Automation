import os
import base64
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")


class OpenAIImageError(RuntimeError):
    pass


def generate_image_bytes(prompt):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    payload = {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
    }

    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    if not response.ok:
        try:
            error_body = response.json()
        except ValueError:
            error_body = response.text
        raise OpenAIImageError(
            f"OpenAI image generation failed: {response.status_code} {error_body}"
        )

    data = response.json().get("data", [])
    if not data:
        raise RuntimeError("OpenAI image response did not include image data.")

    image_data = data[0]
    if image_data.get("b64_json"):
        return base64.b64decode(image_data["b64_json"])

    if image_data.get("url"):
        image_response = requests.get(image_data["url"], timeout=60)
        image_response.raise_for_status()
        return image_response.content

    raise RuntimeError("OpenAI image response did not include a URL or base64 image.")
