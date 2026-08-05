import base64
import io

import fitz

from . import injection_scanner, unicode_scanner
from .common import finding, snippet

LOW_CONTRAST_DIST = 100.0
LOW_CONTRAST_DIST_CRITICAL = 45.0
TINY_SIZE = 5.0
MAX_ANNOTATION_PAGES = 4


def _dist(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _span_rgb(color: int) -> tuple[int, int, int]:
    r, g, b = fitz.sRGB_to_rgb(color)
    return (round(r * 255), round(g * 255), round(b * 255))


def _page_background(page: fitz.Page) -> tuple[int, int, int]:
    best = None
    best_area = -1.0
    for d in page.get_drawings():
        fill = d.get("fill")
        rect = d.get("rect")
        if fill is not None and rect is not None:
            area = rect.get_area()
            if area > best_area:
                best_area = area
                best = tuple(round(v * 255) for v in fill[:3])
    return best if best is not None else (255, 255, 255)


def _annotate(doc: fitz.Document, flagged: dict[int, list[tuple[tuple[int, int, int, int], tuple[int, int, int]]]]) -> str | None:
    from PIL import Image, ImageDraw

    pages = sorted(flagged.keys())[:MAX_ANNOTATION_PAGES]
    if not pages:
        return None
    imgs = []
    scale = 2.0
    for pno in pages:
        page = doc[pno]
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        draw = ImageDraw.Draw(img)
        for bbox, _color in flagged[pno]:
            x0, y0, x1, y1 = bbox
            draw.rectangle(
                [x0 * scale, y0 * scale, x1 * scale, y1 * scale],
                outline="#d43a2f",
                width=3,
            )
        imgs.append(img)
    width = max(i.width for i in imgs)
    height = sum(i.height for i in imgs)
    canvas = Image.new("RGB", (width, height), "white")
    y = 0
    for img in imgs:
        canvas.paste(img, (0, y))
        y += img.height
    buf = io.BytesIO()
    canvas.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def scan_pdf(filename: str, data: bytes) -> dict:
    doc = fitz.open(stream=data, filetype="pdf")
    findings: list[dict] = []
    hidden_spans: list[str] = []
    hidden_boxes: list[tuple[int, tuple[float, float, float, float]]] = []
    full_text_parts: list[str] = []
    flagged: dict[int, list] = {}
    matches: list[str] = []

    try:
        for pno, page in enumerate(doc):
            bg = _page_background(page)
            image_boxes = [fitz.Rect(info["bbox"]) for info in page.get_image_info()]
            spans: list[dict] = []
            raw = page.get_text("dict")
            for block in raw.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        spans.append(span)

            overlap_checked: list[tuple[int, int]] = []
            for i, span in enumerate(spans):
                text = span.get("text") or ""
                if not text.strip():
                    continue
                full_text_parts.append(text)
                loc = f"página {pno + 1}"
                rect = fitz.Rect(span["bbox"])
                bbox = (rect.x0, rect.y0, rect.x1, rect.y1)
                rgb = _span_rgb(span["color"])
                size = float(span.get("size", 0))
                font = span.get("font", "?")
                span_suspicious = False

                for occ in unicode_scanner.find_invisible(text):
                    findings.append(
                        finding(
                            "high",
                            "zero_width",
                            "Caractere invisível encontrado",
                            f"'{occ['name']}' (U+{occ['index']:04X}) aparece {occ['count']}x no texto.",
                            loc,
                            snippet(text),
                            list(bbox),
                        )
                    )
                    span_suspicious = True

                dcol = _dist(rgb, bg)
                low_contrast = dcol < LOW_CONTRAST_DIST
                if low_contrast:
                    sev = "high" if dcol < LOW_CONTRAST_DIST_CRITICAL else "medium"
                    findings.append(
                        finding(
                            sev,
                            "low_contrast",
                            "Texto de baixo contraste (possível texto oculto)",
                            f"Cor do texto #{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X} quase igual ao fundo ({bg}). Distância de cor: {dcol:.0f}.",
                            loc,
                            snippet(text),
                            list(bbox),
                        )
                    )
                    span_suspicious = True
                    hidden_spans.append(text)
                    hidden_boxes.append((pno, bbox))
                    flagged.setdefault(pno, []).append((bbox, rgb))

                if size < TINY_SIZE:
                    findings.append(
                        finding(
                            "medium",
                            "tiny_text",
                            "Fonte minúscula (microtexto)",
                            f"Fonte '{font}' com {size:.1f}pt — pequena demais para leitura normal.",
                            loc,
                            snippet(text),
                            list(bbox),
                        )
                    )
                    span_suspicious = True
                    if not low_contrast:
                        hidden_spans.append(text)
                        hidden_boxes.append((pno, bbox))
                        flagged.setdefault(pno, []).append((bbox, rgb))

                if low_contrast and image_boxes:
                    for ib in image_boxes:
                        if rect.width > 2 and rect.height > 2 and rect.intersects(ib):
                            inter = rect & ib
                            if inter.is_empty:
                                continue
                            ratio = inter.get_area() / rect.get_area()
                            if ratio > 0.6:
                                findings.append(
                                    finding(
                                        "high",
                                        "overlap_covered",
                                        "Texto oculto sob imagem/objeto",
                                        "Texto de baixo contraste coberto por uma imagem/objeto na página.",
                                        loc,
                                        snippet(text),
                                        list(bbox),
                                    )
                                )
                                break

                if not span_suspicious:
                    for j in range(i + 1, len(spans)):
                        if (i, j) in overlap_checked:
                            continue
                        overlap_checked.append((i, j))
                        other = spans[j]
                        other_text = other.get("text") or ""
                        if not other_text.strip():
                            continue
                        orect = fitz.Rect(other["bbox"])
                        if rect.width < 2 or orect.width < 2:
                            continue
                        inter = rect & orect
                        if inter.is_empty:
                            continue
                        ratio = inter.get_area() / min(rect.get_area(), orect.get_area())
                        if ratio > 0.5:
                            other_rgb = _span_rgb(other["color"])
                            other_dcol = _dist(other_rgb, bg)
                            lower, higher = (span, other) if dcol < other_dcol else (other, span)
                            findings.append(
                                finding(
                                    "medium",
                                    "overlap_covered",
                                    "Texto sobreposto",
                                    "Dois trechos de texto ocupam a mesma região da página.",
                                    f"página {pno + 1}",
                                    snippet(lower.get("text") or ""),
                                    list(fitz.Rect(lower["bbox"])),
                                )
                            )
                            break

        hidden_joined = "\n".join(hidden_spans)
        full_text = "\n".join(full_text_parts)

        matches.extend(injection_scanner.scan_injection(full_text))
        for m in injection_scanner.scan_injection(hidden_joined):
            if m not in matches:
                matches.append(m)
                findings.append(
                    finding(
                        "critical",
                        "injection_hidden",
                        "Prompt injection em texto oculto",
                        "Instruções de manipulação de IA encontradas dentro de texto escondido.",
                        None,
                        m,
                    )
                )

        if matches and not any(f["kind"] == "injection_hidden" for f in findings):
            matches_visible = injection_scanner.scan_injection(full_text)
            for m in matches_visible:
                findings.append(
                    finding(
                        "medium",
                        "injection_visible",
                        "Frase de manipulação de IA encontrada",
                        "Texto visível contém padrão típico de prompt injection.",
                        None,
                        m,
                    )
                )

        annotated = _annotate(doc, flagged)
        return {
            "format": "pdf",
            "findings": findings,
            "hidden_text": hidden_joined.strip(),
            "annotated_image": annotated,
            "injection_matches": matches,
            "summary": {"pages": len(doc), "spans": sum(1 for p in doc for _ in p.get_text("dict")["blocks"])},
        }
    finally:
        doc.close()
