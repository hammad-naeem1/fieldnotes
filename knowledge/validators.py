from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils.text import get_valid_filename
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_SIZE = 15 * 1024 * 1024
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
FILE_EXTENSIONS = IMAGE_EXTENSIONS | {".pdf", ".txt", ".md", ".csv", ".zip"}
IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def validate_cover_image(upload):
    suffix = Path(get_valid_filename(upload.name)).suffix.lower()
    if suffix not in IMAGE_EXTENSIONS:
        raise ValidationError("Use a JPG, PNG, or WebP image.")
    if upload.size > MAX_UPLOAD_SIZE:
        raise ValidationError("Images must be 15 MB or smaller.")
    try:
        image = Image.open(upload)
        if image.format != IMAGE_FORMATS[suffix]:
            raise ValidationError("The image format is not allowed.")
        if image.width * image.height > 25_000_000:
            raise ValidationError("Images must be 25 megapixels or smaller.")
        image.verify()
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError):
        raise ValidationError("This file is not a valid image.") from None
    finally:
        upload.seek(0)


def validate_attachment(upload):
    suffix = Path(get_valid_filename(upload.name)).suffix.lower()
    if suffix not in FILE_EXTENSIONS:
        raise ValidationError("Allowed files: JPG, PNG, WebP, PDF, TXT, MD, CSV, and ZIP.")
    if upload.size > MAX_UPLOAD_SIZE:
        raise ValidationError("Files must be 15 MB or smaller.")
    if suffix in IMAGE_EXTENSIONS:
        validate_cover_image(upload)
    elif suffix == ".pdf":
        header = upload.read(5)
        upload.seek(0)
        if header != b"%PDF-":
            raise ValidationError("This file is not a valid PDF.")
    elif suffix == ".zip":
        header = upload.read(4)
        upload.seek(0)
        if header[:2] != b"PK":
            raise ValidationError("This file is not a valid ZIP archive.")
