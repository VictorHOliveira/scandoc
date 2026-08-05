INVISIBLE_CHARS = {
    "\u200b": "ZERO WIDTH SPACE",
    "\u200c": "ZERO WIDTH NON-JOINER",
    "\u200d": "ZERO WIDTH JOINER",
    "\u200e": "LEFT-TO-RIGHT MARK",
    "\u200f": "RIGHT-TO-LEFT MARK",
    "\u2060": "WORD JOINER",
    "\u2061": "FUNCTION APPLICATION",
    "\u2062": "INVISIBLE TIMES",
    "\u2063": "INVISIBLE SEPARATOR",
    "\u2064": "INVISIBLE PLUS",
    "\u2066": "LRI (BIDI)",
    "\u2067": "RLI (BIDI)",
    "\u2068": "FSI (BIDI)",
    "\u2069": "PDI (BIDI)",
    "\ufeff": "ZERO WIDTH NO-BREAK SPACE (BOM)",
    "\u00ad": "SOFT HYPHEN",
    "\u202a": "LEFT-TO-RIGHT EMBEDDING",
    "\u202b": "RIGHT-TO-LEFT EMBEDDING",
    "\u202c": "POP DIRECTIONAL FORMATTING",
    "\u202d": "LEFT-TO-RIGHT OVERRIDE",
    "\u202e": "RIGHT-TO-LEFT OVERRIDE",
}

INVISIBLE_ORDS = {ord(c) for c in INVISIBLE_CHARS}


def strip_invisible(text: str) -> str:
    return "".join(ch for ch in text if ord(ch) not in INVISIBLE_ORDS)


def find_invisible(text: str) -> list[dict]:
    found: list[dict] = {}
    for i, ch in enumerate(text):
        code = ord(ch)
        if code in INVISIBLE_ORDS:
            found.setdefault(code, {"count": 0, "name": INVISIBLE_CHARS[ch], "index": i})
            found[code]["count"] += 1
    return sorted(found.values(), key=lambda f: f["count"], reverse=True)


def has_invisible(text: str) -> bool:
    return any(ord(ch) in INVISIBLE_ORDS for ch in text)
