import base64
import io

from PIL import Image, ImageOps

from . import injection_scanner
from .common import finding, snippet

TINY_BOX_HEIGHT = 16.0
LOW_CONTRAST_DIFF = 25.0

_engine = None
_engine_checked = False


def _get_ocr():
    global _engine, _engine_checked
    if _engine_checked:
        return _engine
    _engine_checked = True
    try:
        from rapidocr import RapidOCR

        _engine = RapidOCR()
    except ImportError:
        try:
            from rapidocr_onnxruntime import RapidOCR

            _engine = RapidOCR()
        except ImportError:
            _engine = None
    return _engine


def _normalize_result(result) -> list:
    words = []
    if result is None:
        return words

    if hasattr(result, "boxes") and hasattr(result, "txts"):
        boxes = getattr(result, "boxes")
        txts = getattr(result, "txts")
        scores = getattr(result, "scores", None)
        for i, text in enumerate(txts):
            text = str(text or "").strip()
            if not text:
                continue
            pts = boxes[i].tolist()
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            score = scores[i] if scores is not None and i < len(scores) else 0.0
            words.append(
                {
                    "bbox": (min(xs), min(ys), max(xs), max(ys)),
                    "text": text,
                    "score": float(score),
                }
            )
        return words

    for item in result:
        if isinstance(item, dict):
            box = item.get("box")
            text = item.get("text")
            score = item.get("score")
        else:
            box, text, score = item
        if not box or not text:
            continue
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        words.append(
            {
                "bbox": (min(xs), min(ys), max(xs), max(ys)),
                "text": str(text),
                "score": float(score or 0),
            }
        )
    return words


def _local_contrast(img: Image.Image, bbox: tuple) -> float:
    x0, y0, x1, y1 = (int(round(v)) for v in bbox)
    w, h = img.size
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return 255.0
    crop = img.crop((x0, y0, x1, y1)).convert("L")
    px = crop.load()
    interior = []
    border = []
    cw, ch = crop.size
    for yy in range(ch):
        for xx in range(cw):
            val = px[xx, yy]
            if yy < max(1, ch // 6) or yy >= ch - max(1, ch // 6) or xx < max(1, cw // 6) or xx >= cw - max(1, cw // 6):
                border.append(val)
            else:
                interior.append(val)
    if not border or not interior:
        return 255.0
    mean_border = sum(border) / len(border)
    mean_inner = sum(interior) / len(interior)
    return abs(mean_border - mean_inner)


def _annotate(img: Image.Image, words: list[dict]) -> str:
    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)
    for w_ in words:
        x0, y0, x1, y1 = w_["bbox"]
        color = "#d43a2f" if w_.get("suspicious") else "#2f9e44"
        draw.rectangle([x0, y0, x1, y1], outline=color, width=2)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _run_engine(engine, variant):
    out = engine(variant)
    if isinstance(out, tuple) and len(out) == 2 and isinstance(out[0], (list, tuple)):
        return out[0]
    return out


def scan_image(filename: str, data: bytes) -> dict:
    img = Image.open(io.BytesIO(data))
    if img.mode != "RGB":
        img = img.convert("RGB")

    engine = _get_ocr()
    findings: list[dict] = []
    matches: list[str] = []
    word_records: list[dict] = []

    if engine is None:
        findings.append(
            finding(
                "low",
                "ocr_small",
                "OCR não disponível",
                "Pacote de OCR (rapidocr) não instalado — não foi possível ler o texto da imagem.",
            )
        )
        return {
            "format": "image",
            "findings": findings,
            "hidden_text": "",
            "annotated_image": None,
            "injection_matches": [],
            "summary": {"width": img.width, "height": img.height, "ocr": False},
        }

    variants = {}
    try:
        import numpy as np

        variants["original"] = np.array(img)
        gray = img.convert("L")
        variants["autocontrast"] = np.array(ImageOps.autocontrast(gray).convert("RGB"))
        variants["inverted"] = np.array(ImageOps.invert(img))
    except Exception:
        variants = {"original": img}

    seen = set()
    for name, variant in variants.items():
        try:
            result = _run_engine(engine, variant)
        except Exception:
            continue
        for w_ in _normalize_result(result):
            key = (round(w_["bbox"][0], 0), round(w_["bbox"][1], 0), w_["text"])
            if key in seen:
                continue
            seen.add(key)
            word_records.append(w_)

    full_text = " ".join(w_["text"] for w_ in word_records)
    matches.extend(injection_scanner.scan_injection(full_text))

    for w_ in word_records:
        bbox = w_["bbox"]
        height = bbox[3] - bbox[1]
        contrast = _local_contrast(img, bbox)
        suspicious = False
        loc = f"x:{int(bbox[0])},y:{int(bbox[1])}"

        if height < TINY_BOX_HEIGHT:
            findings.append(
                finding(
                    "medium",
                    "ocr_small",
                    "Texto muito pequeno (microtexto)",
                    f"Trecho '{w_['text']}' tem apenas {height:.0f}px de altura.",
                    loc,
                    snippet(w_["text"]),
                    list(bbox),
                )
            )
            suspicious = True

        if contrast < LOW_CONTRAST_DIFF:
            findings.append(
                finding(
                    "high",
                    "ocr_low_contrast",
                    "Texto de baixo contraste com o fundo",
                    f"Contraste local de apenas {contrast:.0f} — difícil de ver a olho nu.",
                    loc,
                    snippet(w_["text"]),
                    list(bbox),
                )
            )
            suspicious = True

        w_["suspicious"] = suspicious

    hidden_parts = [w_["text"] for w_ in word_records if w_["suspicious"]]
    annotated = _annotate(img.copy(), word_records)

    return {
        "format": "image",
        "findings": findings,
        "hidden_text": " ".join(hidden_parts),
        "annotated_image": annotated,
        "injection_matches": sorted(set(matches)),
        "summary": {"width": img.width, "height": img.height, "words": len(word_records), "ocr": True},
    }
