import os
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response, JSONResponse
from captcha.image import ImageCaptcha
from app.core.security import CaptchaHandler

router = APIRouter(prefix="/captcha", tags=["Captcha"])


@router.get("/image")
def get_captcha(text: str):
    """Return PNG image bytes for given captcha text.

    Produces a larger, higher-font-size image and attempts to use a
    clear system font when available to avoid blurring.
    """
    # Candidate system fonts (Windows/Linux common paths)
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\verdana.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    fonts = [p for p in candidates if os.path.exists(p)]

    try:
        # Larger image and font size for clarity
        image = ImageCaptcha(width=280, height=100, fonts=fonts or None, font_sizes=[42, 48])
        data = image.generate(text)
        return StreamingResponse(data, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate captcha image")


@router.get("/svg")
def get_captcha_svg(text: str):
    """Return an SVG captcha for crisper rendering in browsers."""
    try:
        # Render each character spaced out and slightly rotated for obfuscation
        chars = ''.join([c for c in text])
        x_start = 30
        per = 40
        parts = []
        parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="100">')
        parts.append('<rect width="100%" height="100%" fill="#fff"/>')
        import random
        for i, ch in enumerate(chars):
            x = x_start + i * per
            rotate = random.randint(-20, 20)
            parts.append(f'<text x="{x}" y="60" font-size="44" transform="rotate({rotate} {x} 60)" font-family="Arial,Helvetica,sans-serif" fill="#111">{ch}</text>')
        parts.append('</svg>')
        svg = '\n'.join(parts)
        return Response(content=svg, media_type="image/svg+xml")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate captcha SVG")


@router.get("/new")
def new_captcha():
    """Create a new captcha challenge and return token + image url."""
    try:
        question, token = CaptchaHandler.create_challenge()
        timestamp = int(time.time() * 1000)
        image_url = f"/captcha/svg?text={question}&_={timestamp}"
        return JSONResponse({"captcha_token": token, "captcha_text": question, "image_url": image_url})
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create captcha")
