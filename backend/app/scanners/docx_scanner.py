import io

from docx import Document
from docx.oxml.ns import qn

from . import injection_scanner, unicode_scanner
from .common import finding, snippet

WHITE_COLORS = {"FFFFFF", "FFF", "FFFFFF00", "FFFFF", "FEFFFF", "FDFFFF"}
TINY_SIZE = 5.0


def _run_flags(r) -> dict:
    flags = {"vanish": False, "color": None, "size_pt": None, "hidden_char": False}
    rpr = r.find(qn("w:rPr"))
    if rpr is not None:
        if rpr.find(qn("w:vanish")) is not None:
            flags["vanish"] = True
        col = rpr.find(qn("w:color"))
        if col is not None:
            val = col.get(qn("w:val"))
            flags["color"] = val
        sz = rpr.find(qn("w:sz"))
        if sz is not None:
            try:
                flags["size_pt"] = int(sz.get(qn("w:val"))) / 2
            except (TypeError, ValueError):
                flags["size_pt"] = None
    return flags


def _collect_runs(root) -> list[tuple]:
    runs = []
    for p in root.iter(qn("w:p")):
        for r in p.iter(qn("w:r")):
            text = "".join(t.text or "" for t in r.iter(qn("w:t")))
            if not text:
                continue
            runs.append((p, r, text))
    return runs


def scan_docx(filename: str, data: bytes) -> dict:
    import zipfile

    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise ValueError("Arquivo não é um DOCX válido")

    doc = Document(io.BytesIO(data))
    findings: list[dict] = []
    hidden_parts: list[str] = []
    full_text_parts: list[str] = []
    matches: list[str] = []

    def process_runs(runs: list, location: str) -> None:
        for p, r, text in runs:
            flags = _run_flags(r)
            full_text_parts.append(text)
            suspicious = False

            for occ in unicode_scanner.find_invisible(text):
                findings.append(
                    finding(
                        "high",
                        "zero_width",
                        "Caractere invisível encontrado",
                        f"'{occ['name']}' (U+{occ['index']:04X}) aparece {occ['count']}x no texto.",
                        location,
                        snippet(text),
                    )
                )
                suspicious = True

            if flags["vanish"]:
                findings.append(
                    finding(
                        "high",
                        "hidden_property",
                        "Texto oculto nativo do Word (vanish)",
                        "A propriedade 'oculto' do Word (w:vanish) está ativa neste trecho.",
                        location,
                        snippet(text),
                    )
                )
                suspicious = True

            if flags["color"] and flags["color"].upper() in WHITE_COLORS:
                findings.append(
                    finding(
                        "high",
                        "low_contrast",
                        "Texto em cor branca",
                        "Fonte com cor branca (#FFFFFF) — invisível em fundo claro.",
                        location,
                        snippet(text),
                    )
                )
                suspicious = True

            if flags["size_pt"] is not None and flags["size_pt"] < TINY_SIZE:
                findings.append(
                    finding(
                        "medium",
                        "tiny_text",
                        "Fonte minúscula (microtexto)",
                        f"Fonte de {flags['size_pt']:.1f}pt — pequena demais para leitura normal.",
                        location,
                        snippet(text),
                    )
                )
                suspicious = True

            if suspicious:
                hidden_parts.append(text)

    body_runs = _collect_runs(doc.element)
    process_runs(body_runs, "corpo do documento")

    for idx, section in enumerate(doc.sections):
        for header in (section.header, section.footer):
            if header is not None and header.is_linked_to_previous is False:
                process_runs(_collect_runs(header._element), f"cabeçalho/rodapé #{idx + 1}")

    hidden_joined = "\n".join(hidden_parts)
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

    return {
        "format": "docx",
        "findings": findings,
        "hidden_text": hidden_joined.strip(),
        "annotated_image": None,
        "injection_matches": matches,
        "summary": {"paragraphs": len(list(doc.element.iter(qn("w:p"))))},
    }
