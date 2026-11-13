"""
Generates synthetic, candidate-controlled text CAPTCHAs with known ground
truth, for the custom OCR/CV solving engine to be benchmarked against.

A hand-rolled PIL renderer is used instead of a third-party CAPTCHA library
so the distortion level is tunable: enough per-character rotation, spacing
jitter, and background noise to be a genuine recognition challenge (not
flat, un-rotated text), while deliberately avoiding the character-overlap
and full-width arc strokes that make fully adversarial, bot-blocking
CAPTCHA libraries close to unsolvable even for a careful OCR pipeline. The
goal here is to exercise and honestly benchmark the OCR/CV solving engine
(Section 2.B of the assignment), not to win an arms race against a
commercial anti-bot product.
"""
import base64
import io
import random
import string
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

_CHARSET = string.ascii_uppercase + string.digits
# Exclude visually ambiguous characters to keep ground-truth fair.
_CHARSET = "".join(c for c in _CHARSET if c not in "0O1IL5S2Z")

_WIDTH, _HEIGHT = 240, 100
_FONT_SIZE = 48

# A bold TTF font is bundled with the project (backend/app/assets/fonts/)
# so captcha rendering works identically on Windows/macOS/Linux, instead of
# depending on an OS-specific system font path (which previously caused
# /api/generate to 500 on Windows, where /usr/share/fonts/... doesn't exist).
_BUNDLED_FONT = Path(__file__).resolve().parent / "assets" / "fonts" / "DejaVuSans-Bold.ttf"

# Fallback locations to try if the bundled font is ever missing, so the
# tool still works rather than crashing outright.
_FALLBACK_FONT_CANDIDATES = [
    _BUNDLED_FONT,
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),  # common Linux
    Path("C:/Windows/Fonts/arialbd.ttf"),                           # common Windows
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),      # common macOS
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    last_error = None
    for candidate in _FALLBACK_FONT_CANDIDATES:
        try:
            if candidate.exists():
                return ImageFont.truetype(str(candidate), size)
        except Exception as exc:  # pragma: no cover - defensive
            last_error = exc
    # Last resort: PIL's built-in bitmap font (always available, ugly but
    # never crashes the API).
    try:
        return ImageFont.load_default()
    except Exception as exc:
        raise RuntimeError(
            f"Could not load any font for CAPTCHA rendering (last error: {last_error or exc})"
        )


_FONT = _load_font(_FONT_SIZE)

# In-memory store mapping captcha_id -> ground truth text.
# A real deployment would use Redis/DB with TTL; fine for this assignment.
_GROUND_TRUTH_STORE: dict[str, str] = {}


def _random_color(low=0, high=120):
    return (random.randint(low, high), random.randint(low, high), random.randint(low, high))


def _draw_noise(draw: ImageDraw.ImageDraw, w: int, h: int, n_lines: int = 2, n_dots: int = 25):
    for _ in range(n_lines):
        x1, y1 = random.randint(0, w // 4), random.randint(0, h)
        x2, y2 = random.randint(3 * w // 4, w), random.randint(0, h)
        draw.line((x1, y1, x2, y2), fill=_random_color(170, 220), width=1)
    for _ in range(n_dots):
        x, y = random.randint(0, w), random.randint(0, h)
        draw.ellipse((x, y, x + 1, y + 1), fill=_random_color(170, 220))


def _render_captcha(text: str) -> Image.Image:
    img = Image.new("RGB", (_WIDTH, _HEIGHT), color=(250, 250, 250))
    font = _FONT

    draw = ImageDraw.Draw(img)
    _draw_noise(draw, _WIDTH, _HEIGHT, n_lines=1, n_dots=18)

    n = len(text)
    slot_w = _WIDTH // n
    for i, ch in enumerate(text):
        # Render each character on its own small transparent canvas so it
        # can be rotated independently without clipping, then pasted.
        glyph_canvas = Image.new("RGBA", (slot_w, _HEIGHT), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glyph_canvas)
        color = _random_color(0, 90)
        bbox = gdraw.textbbox((0, 0), ch, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (slot_w - tw) // 2 - bbox[0]
        ty = (_HEIGHT - th) // 2 - bbox[1]
        gdraw.text((tx, ty), ch, font=font, fill=color + (255,))

        angle = random.uniform(-16, 16)
        rotated = glyph_canvas.rotate(angle, resample=Image.BICUBIC, expand=False)

        x_offset = i * slot_w + random.randint(-3, 3)
        y_offset = random.randint(-6, 6)
        img.paste(rotated, (x_offset, y_offset), rotated)

    img = img.filter(ImageFilter.SMOOTH)
    return img


def generate_captcha(length: int = 5) -> tuple[str, str, bytes]:
    """Returns (captcha_id, ground_truth_text, png_bytes)."""
    text = "".join(random.choices(_CHARSET, k=length))
    captcha_id = str(uuid.uuid4())
    img = _render_captcha(text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()
    _GROUND_TRUTH_STORE[captcha_id] = text
    return captcha_id, text, png_bytes


def generate_captcha_base64(length: int = 5) -> tuple[str, str]:
    captcha_id, _text, png_bytes = generate_captcha(length)
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return captcha_id, b64


def get_ground_truth(captcha_id: str) -> str | None:
    return _GROUND_TRUTH_STORE.get(captcha_id)


def pop_ground_truth(captcha_id: str) -> str | None:
    return _GROUND_TRUTH_STORE.pop(captcha_id, None)