SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

KIND_WEIGHTS = {
    "injection_hidden": 40,
    "injection_visible": 20,
    "zero_width": 25,
    "low_contrast": 30,
    "opacity_zero": 30,
    "hidden_property": 25,
    "overlap_covered": 20,
    "offscreen": 15,
    "tiny_text": 15,
    "ocr_small": 15,
    "ocr_low_contrast": 30,
    "watermark": 5,
}


def finding(severity, kind, title, description, location=None, snippet=None, bbox=None) -> dict:
    return {
        "severity": severity,
        "kind": kind,
        "title": title,
        "description": description,
        "location": location,
        "snippet": (snippet or "")[:500],
        "bbox": [round(float(v), 2) for v in bbox] if bbox else None,
    }


def compute_score(findings: list[dict]) -> int:
    kinds = set()
    for f in findings:
        kinds.add(f.get("kind", ""))
    total = sum(KIND_WEIGHTS.get(k, 10) for k in kinds if k)
    return min(100, total)


def snippet(text: str, max_len: int = 120) -> str:
    text = " ".join(text.split())
    return text[:max_len]
