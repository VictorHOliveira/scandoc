import re
from typing import Callable, Optional

from bs4 import BeautifulSoup

from . import injection_scanner, unicode_scanner
from .common import finding, snippet

_TINY_PX = 6.0
_TINY_EM = 0.2

NAMED_COLORS = {
    "white": (255, 255, 255),
    "whitesmoke": (245, 245, 245),
    "snow": (255, 250, 250),
    "gainsboro": (220, 220, 220),
    "lightgray": (211, 211, 211),
    "lightgrey": (211, 211, 211),
    "silver": (192, 192, 192),
    "black": (0, 0, 0),
}


def parse_color(raw: str | None):
    if not raw:
        return None
    s = raw.strip().lower()
    if not s:
        return None
    if s == "transparent":
        return "transparent"
    m = re.match(r"^#([0-9a-f]{3})$", s)
    if m:
        h = m.group(1)
        return tuple(int(c * 2, 16) for c in h)
    m = re.match(r"^#([0-9a-f]{6})$", s)
    if m:
        h = m.group(1)
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"^rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\)$", s)
    if m:
        alpha = float(m.group(4) or 1)
        if alpha <= 0.05:
            return "transparent"
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"^rgb\(\s*([\d.]+)%\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*\)$", s)
    if m:
        return tuple(round(float(g) * 2.55) for g in (m.group(1), m.group(2), m.group(3)))
    if s in NAMED_COLORS:
        return NAMED_COLORS[s]
    return None


def _is_light(c) -> bool:
    if isinstance(c, str):
        return False
    return all(v > 235 for v in c)


def _is_dark(c) -> bool:
    if isinstance(c, str):
        return False
    return all(v < 40 for v in c)


def parse_style(style: str) -> dict:
    props = {}
    for decl in style.split(";"):
        if ":" not in decl:
            continue
        key, _, val = decl.partition(":")
        props[key.strip().lower()] = val.strip().lower()
    return props


def _num_px(val: str) -> float | None:
    m = re.match(r"^(-?[\d.]+)\s*px$", val)
    if m:
        return float(m.group(1))
    return None


def _num_em(val: str) -> float | None:
    m = re.match(r"^(-?[\d.]+)\s*em$", val)
    if m:
        return float(m.group(1))
    return None


def scan_html(filename: str, data: bytes, on_progress: Callable[[int, str], None] | None = None) -> dict:
    if on_progress:
        on_progress(15, "Analisando estrutura HTML")
    text = data.decode("utf-8", errors="replace")
    soup = BeautifulSoup(text, "html.parser")

    findings: list[dict] = []
    hidden_parts: list[str] = []
    matches: list[str] = []
    body_bg = (255, 255, 255)

    root = soup.find("body") or soup.find("html") or soup
    body_style = parse_style(root.get("style", ""))
    bg = parse_color(body_style.get("background-color") or body_style.get("background"))
    if isinstance(bg, tuple):
        body_bg = bg

    style_blocks = " ".join(s.get_text() for s in soup.find_all("style"))
    m = re.search(r"body\s*\{([^}]*)\}", style_blocks)
    if m:
        bg2 = parse_color(parse_style(m.group(1)).get("background-color"))
        if isinstance(bg2, tuple):
            body_bg = bg2

    def flag_style(el, style, loc, text):
        props = parse_style(style)
        display = props.get("display")
        visibility = props.get("visibility")
        opacity = props.get("opacity")
        color = parse_color(props.get("color"))
        bgc = parse_color(props.get("background-color"))
        font_size = props.get("font-size")
        text_indent = props.get("text-indent")
        position = props.get("position")
        left = props.get("left")
        top = props.get("top")

        if display == "none" or visibility == "hidden":
            findings.append(
                finding(
                    "high",
                    "hidden_property",
                    "Elemento oculto (display:none / visibility:hidden)",
                    "O conteúdo existe na página, mas é invisível para o usuário.",
                    loc,
                    snippet(text),
                )
            )
            hidden_parts.append(text)
            return True

        if isinstance(opacity, str):
            try:
                if float(opacity) <= 0.05:
                    findings.append(
                        finding(
                            "high",
                            "opacity_zero",
                            "Elemento com opacidade ~0",
                            "O elemento está no documento, porém transparente.",
                            loc,
                            snippet(text),
                        )
                    )
                    hidden_parts.append(text)
                    return True
            except ValueError:
                pass

        suspicious = False
        if color == "transparent" or (color is not None and _is_light(color) and _is_light(body_bg)):
            findings.append(
                finding(
                    "high" if color == "transparent" else "medium",
                    "low_contrast",
                    "Texto invisível / de baixo contraste",
                    "Cor do texto igual ou muito próxima à cor do fundo.",
                    loc,
                    snippet(text),
                )
            )
            suspicious = True

        if isinstance(bgc, tuple) and isinstance(color, tuple) and bgc == color:
            findings.append(
                finding(
                    "medium",
                    "low_contrast",
                    "Texto da mesma cor do fundo",
                    "background-color igual à cor da fonte.",
                    loc,
                    snippet(text),
                )
            )
            suspicious = True

        if font_size:
            px = _num_px(font_size)
            em = _num_em(font_size)
            if font_size == "0" or (px is not None and px < _TINY_PX) or (em is not None and em < _TINY_EM):
                findings.append(
                    finding(
                        "medium",
                        "tiny_text",
                        "Fonte minúscula (microtexto)",
                        f"font-size {font_size} é pequeno demais para leitura normal.",
                        loc,
                        snippet(text),
                    )
                )
                suspicious = True

        indent_px = _num_px(text_indent) if text_indent else None
        if indent_px is not None and indent_px <= -1000:
            findings.append(
                finding(
                    "medium",
                    "offscreen",
                    "Texto deslocado para fora da tela",
                    f"text-indent de {indent_px}px empurra o conteúdo para fora da área visível.",
                    loc,
                    snippet(text),
                )
            )
            suspicious = True

        if position == "absolute":
            left_px = _num_px(left) if left else None
            top_px = _num_px(top) if top else None
            if (left_px is not None and left_px <= -1000) or (top_px is not None and top_px <= -1000):
                findings.append(
                    finding(
                        "medium",
                        "offscreen",
                        "Elemento posicionado fora da tela",
                        "position:absolute com coordenadas negativas enormes.",
                        loc,
                        snippet(text),
                    )
                )
                suspicious = True

        if suspicious:
            hidden_parts.append(text)
        return suspicious

    for el in soup.find_all(True):
        loc = f"<{el.name}>"
        style = el.get("style", "") or ""
        text = el.get_text(" ", strip=True)

        if el.has_attr("hidden") or (el.get("aria-hidden") or "").lower() == "true":
            findings.append(
                finding(
                    "high",
                    "hidden_property",
                    "Elemento oculto (atributo hidden/aria-hidden)",
                    "O elemento está marcado como oculto no HTML.",
                    loc,
                    snippet(text),
                )
            )
            if text:
                hidden_parts.append(text)

        for occ in unicode_scanner.find_invisible(text):
            findings.append(
                finding(
                    "high",
                    "zero_width",
                    "Caractere invisível encontrado",
                    f"'{occ['name']}' (U+{occ['index']:04X}) aparece {occ['count']}x.",
                    loc,
                    snippet(text),
                )
            )

        for attr_name in ("alt", "title"):
            attr_val = el.get(attr_name)
            if attr_val:
                found = injection_scanner.scan_injection(attr_val)
                for m in found:
                    findings.append(
                        finding(
                            "medium",
                            "injection_visible",
                            f"Prompt injection no atributo {attr_name}",
                            f"Atributo '{attr_name}' de <{el.name}> contém padrão suspeito.",
                            loc,
                            m,
                        )
                    )
                    matches.append(m)

        if style:
            flag_style(el, style, loc, text)

    meta_contents = []
    for meta in soup.find_all("meta"):
        content = meta.get("content")
        if content:
            meta_contents.append(content)
    for content in meta_contents:
        for m in injection_scanner.scan_injection(content):
            findings.append(
                finding(
                    "medium",
                    "injection_visible",
                    "Prompt injection em metatag",
                    "Conteúdo de <meta> contém padrão suspeito.",
                    "<meta>",
                    m,
                )
            )
            matches.append(m)

    visible_text = soup.get_text(" ", strip=True)
    matches.extend(injection_scanner.scan_injection(visible_text))
    hidden_joined = "\n".join(dict.fromkeys(hidden_parts))

    if on_progress:
        on_progress(90, "Finalizando análise")

    return {
        "format": "html",
        "findings": findings,
        "hidden_text": hidden_joined.strip(),
        "annotated_image": None,
        "injection_matches": sorted(set(matches)),
        "summary": {"elements": len(soup.find_all(True))},
    }
