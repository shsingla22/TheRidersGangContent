#!/usr/bin/env python3
"""
Nano Banana Pro Image Generator for The Rider's Gang
=====================================================
Generates article hero and inline images using Google's Nano Banana Pro
(Gemini image generation). Downloads reference images from the web,
then generates original images with old money, strength, and heritage aesthetics.

Usage:
    pip install google-genai Pillow requests
    export GEMINI_API_KEY="your-api-key-here"
    python generate-article-images.py

This will generate images in assets/images/articles/ and update the article
HTML files to reference the local images instead of Unsplash URLs.
"""

import os
import sys
import time
import base64
import requests
from pathlib import Path
from io import BytesIO

try:
    from google import genai
    from google.genai import types
    from PIL import Image
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-genai Pillow requests")
    sys.exit(1)

# === Configuration ===
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAQdYkBdS7h60FOzlp-frSmVgH5vA2i5Y8")
MODEL = "gemini-2.0-flash-exp"  # Supports image generation
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "images" / "articles"

# === Style directives (old money, strength, happiness) ===
STYLE_DIRECTIVE = """
Style requirements for every image:
- OLD MONEY aesthetic: understated luxury, heritage, timeless elegance
- Colors should feel warm, muted, and rich — deep greens, aged brass, saddle browns, cream
- Lighting should be warm and natural — golden hour, soft window light, or overcast British countryside
- Composition should feel editorial and confident — like a spread in a premium heritage magazine
- Convey STRENGTH and quiet HAPPINESS — not forced smiles, but the contentment of someone who belongs
- The image should feel AUTHENTIC — real textures, real materials, real settings
- Avoid anything flashy, neon, trendy, or modern-corporate
- Think: Barbour catalogues, Country Life magazine, Ralph Lauren heritage campaigns
"""


def download_reference_image(url, timeout=10):
    """Download a reference image from the web."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content))
    except Exception as e:
        print(f"  Warning: Could not download {url}: {e}")
        return None


def generate_image(client, prompt, reference_urls, output_path, size="1024x768"):
    """
    Generate an image using Nano Banana Pro with reference images.
    Downloads 5 reference images, then generates a new original image.
    """
    print(f"\n  Generating: {output_path.name}")
    print(f"  Downloading {len(reference_urls)} reference images...")

    # Download reference images
    ref_images = []
    for i, url in enumerate(reference_urls):
        img = download_reference_image(url)
        if img:
            # Resize references to reasonable size
            img.thumbnail((512, 512))
            ref_images.append(img)
            print(f"    Reference {i+1}: downloaded")
        else:
            print(f"    Reference {i+1}: skipped")

    # Build the generation request with references
    full_prompt = f"""
{prompt}

{STYLE_DIRECTIVE}

Use the provided reference images for inspiration on composition, mood, and subject matter.
Create a COMPLETELY NEW and ORIGINAL image — do not copy the references directly.
The image should be photorealistic, high quality, and suitable for a premium editorial website.
Output dimensions: {size}
"""

    # Build content parts
    contents = []
    for img in ref_images:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        contents.append(types.Part.from_bytes(data=buf.read(), mime_type="image/jpeg"))

    contents.append(full_prompt)

    print("  Calling Nano Banana Pro API...")
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        # Extract and save the generated image
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img_data = base64.b64decode(part.inline_data.data)
                img = Image.open(BytesIO(img_data))

                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Save as high-quality JPEG
                img.save(output_path, format="JPEG", quality=92)
                print(f"  Saved: {output_path} ({img.size[0]}x{img.size[1]})")
                return True

        print("  Warning: No image in API response")
        return False

    except Exception as e:
        print(f"  Error generating image: {e}")
        return False


def main():
    print("=" * 60)
    print("The Rider's Gang — Nano Banana Pro Image Generator")
    print("=" * 60)

    client = genai.Client(api_key=API_KEY)

    # === Article 1: The Wax Jacket ===
    print("\n--- Article 1: The Wax Jacket ---")

    wax_jacket_images = [
        {
            "name": "wax-jacket-hero.jpg",
            "prompt": "A distinguished person wearing a classic olive-green Barbour wax jacket, walking through the misty British countryside with rolling green hills. A horse grazes in the background behind a dry stone wall. Golden autumn light. The person exudes quiet confidence and heritage wealth — like they've owned this land for generations.",
            "references": [
                "https://images.unsplash.com/photo-1544022613-e87ca75a784a?w=800",
                "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
                "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800",
                "https://images.unsplash.com/photo-1476611338391-6f395a0ebc7b?w=800",
                "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800",
            ],
            "size": "1200x600",
        },
        {
            "name": "wax-jacket-countryside.jpg",
            "prompt": "A moody British countryside landscape at dawn — rolling green fields, ancient stone walls, a narrow lane disappearing into mist. A Land Rover Defender is parked beside a gate. The scene feels timeless, like it could be 1960 or today. Warm golden light breaking through low clouds.",
            "references": [
                "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
                "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800",
                "https://images.unsplash.com/photo-1476611338391-6f395a0ebc7b?w=800",
                "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800",
                "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=800",
            ],
            "size": "1000x500",
        },
        {
            "name": "wax-jacket-motorcycle.jpg",
            "prompt": "A classic motorcycle (vintage Triumph or similar) parked outside a weathered English country pub. A wax jacket is draped over the seat. The scene is lit by warm afternoon sun. Stone walls, climbing ivy, a wooden pub sign. Heritage and motorcycle culture meeting in one frame.",
            "references": [
                "https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=800",
                "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=800",
                "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800",
                "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800",
                "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800",
            ],
            "size": "1000x500",
        },
    ]

    for img_config in wax_jacket_images:
        output_path = OUTPUT_DIR / img_config["name"]
        generate_image(
            client,
            img_config["prompt"],
            img_config["references"],
            output_path,
            img_config["size"],
        )
        time.sleep(2)  # Rate limiting

    # === Article 2: The Stirrup ===
    print("\n--- Article 2: The Stirrup ---")

    stirrup_images = [
        {
            "name": "stirrup-hero.jpg",
            "prompt": "A close-up of a polished steel stirrup on a beautiful leather saddle, with a rider's boot resting in it. The horse is a magnificent dark bay. Warm golden light. The image should feel both ancient and timeless — this simple invention that changed the world. Shot from a low angle looking up at the rider.",
            "references": [
                "https://images.unsplash.com/photo-1598974357801-cbca100e65d3?w=800",
                "https://images.unsplash.com/photo-1553284965-83fd3e82fa5a?w=800",
                "https://images.unsplash.com/photo-1722109283665-05e8a7db546e?w=800",
                "https://images.unsplash.com/photo-1516466723877-e4ec1d736c8a?w=800",
                "https://images.unsplash.com/photo-1534670007418-fbb7f6cf32c3?w=800",
            ],
            "size": "1200x600",
        },
        {
            "name": "stirrup-horse-golden.jpg",
            "prompt": "A majestic horse standing in a golden field at sunset, with tack and stirrups visible on the saddle. The horse is looking directly at the camera with noble bearing. The light is warm and rich, like an old painting. The scene conveys power, grace, and centuries of partnership between horse and human.",
            "references": [
                "https://images.unsplash.com/photo-1553284965-83fd3e82fa5a?w=800",
                "https://images.unsplash.com/photo-1534670007418-fbb7f6cf32c3?w=800",
                "https://images.unsplash.com/photo-1516466723877-e4ec1d736c8a?w=800",
                "https://images.unsplash.com/photo-1450052590821-8bf91254a353?w=800",
                "https://images.unsplash.com/photo-1496185106368-308ed96f204b?w=800",
            ],
            "size": "1000x500",
        },
        {
            "name": "stirrup-boot-detail.jpg",
            "prompt": "An artistic detail shot of a rider's tall leather boot in a brass stirrup, on a white horse. The leather is rich and well-worn. Dressage setting — formal, elegant, precise. The composition is tight and editorial. Warm, soft light with shallow depth of field.",
            "references": [
                "https://images.unsplash.com/photo-1722109283665-05e8a7db546e?w=800",
                "https://images.unsplash.com/photo-1598974357801-cbca100e65d3?w=800",
                "https://images.unsplash.com/photo-1534670007418-fbb7f6cf32c3?w=800",
                "https://images.unsplash.com/photo-1553284965-83fd3e82fa5a?w=800",
                "https://images.unsplash.com/photo-1516466723877-e4ec1d736c8a?w=800",
            ],
            "size": "1000x500",
        },
    ]

    for img_config in stirrup_images:
        output_path = OUTPUT_DIR / img_config["name"]
        generate_image(
            client,
            img_config["prompt"],
            img_config["references"],
            output_path,
            img_config["size"],
        )
        time.sleep(2)  # Rate limiting

    print("\n" + "=" * 60)
    print("Image generation complete!")
    print(f"Images saved to: {OUTPUT_DIR}")
    print("\nTo use these images, update the article HTML files to reference")
    print("the local paths instead of Unsplash URLs.")
    print("=" * 60)


if __name__ == "__main__":
    main()
