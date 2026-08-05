import re

PATTERNS = [
    (r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions|prompts|messages|context)", "tentar ignorar instruções anteriores"),
    (r"ignore\s+(everything|all)\s+(else\s+)?(you\s+)?(were\s+)?(told|said|given)", "tentar ignorar instruções anteriores"),
    (r"disregard\s+(the\s+)?(previous|above|prior|all)", "tentar desconsiderar instruções anteriores"),
    (r"forget\s+(everything|all)\s+(you\s+)?(know|learned|were told|read)", "tentar apagar instruções anteriores"),
    (r"forget\s+(the\s+)?(previous|prior|above)", "tentar apagar instruções anteriores"),
    (r"you\s+(are|are now)\s+(a|an)\b", "tentar redefinir o papel da IA"),
    (r"you\s+are\s+(now\s+)?(my|the|an?)\s*(assistant|agent|model|ai|gpt|bot)", "tentar redefinir o papel da IA"),
    (r"act\s+as\s+(an?\s+)?(assistant|agent|ai|model|gpt|system|expert)", "tentar redefinir o papel da IA"),
    (r"from\s+now\s+on\b", "estabelecer regra a partir de agora"),
    (r"new\s+(rules|instructions|guidelines|directives)", "novas regras/instruções"),
    (r"(your|its)\s+(new|actual|real|true)\s+(instructions|rules|prompt)", "referência a instruções ocultas"),
    (r"do\s+not\s+(mention|reveal|tell|disclose|show|say|report)\s+(this|these|the user|anyone|it)", "pedir para não revelar conteúdo"),
    (r"(never|don.t)\s+(mention|reveal|tell|disclose|show|say|report)\b", "pedir para não revelar conteúdo"),
    (r"do\s+not\s+tell\s+(the\s+)?user\b", "pedir para não avisar o usuário"),
    (r"system\s+prompt", "referência a prompt de sistema"),
    (r"jailbreak", "tentativa de jailbreak"),
    (r"override\s+(all\s+)?(previous|prior)\s+instructions", "tentar sobrescrever instruções"),
    (r"base\s*64", "conteúdo codificado em base64"),
    (r"rot\s*13", "conteúdo codificado em ROT13"),
    (r"hex\s*:\s*[0-9a-f]{8,}", "conteúdo codificado em hex"),
    (r"hidden\s+(instructions|prompt|message|text)", "referência a instruções escondidas"),
    (r"secret\s+(instructions|prompt|message|text)", "referência a instruções secretas"),
    (r"if\s+you\s+(see|read|find|detect|understand)\s+this\b", "condição ativada quando a IA lê o texto"),
    (r"when\s+you\s+(see|read|find|detect|reach)\s+this\b", "condição ativada quando a IA lê o texto"),
    (r"attention\s+(ai|llm|model|gpt|assistant|recruiter|reader)", "chamada direta à IA"),
    (r"prioritize\s+(this|the following|these)", "pedir prioridade para conteúdo"),
    (r"(respond|answer|reply)\s+only\s+(with|in|using)\b", "controlar formato de resposta"),
    (r"in\s+(your|its)\s+(response|reply|answer|output)\s*,?\s+(include|say|write|mention|append|repeat)", "injetar conteúdo na resposta da IA"),
    (r"append\s+(this|the following|the text)", "injetar conteúdo na resposta da IA"),
    (r"include\s+this\s+(text|content|message)", "injetar conteúdo na resposta da IA"),
    (r"print\s+this\s+(text|message|content)", "injetar conteúdo na resposta da IA"),
    (r"\b(AI|LLM|GPT|CHATGPT|MODEL)\b.{0,60}(instructions|rules|prompt)", "instrução endereçada à IA"),
]


def build_regex() -> re.Pattern:
    return re.compile("|".join(f"(?:{p})" for p, _ in PATTERNS), re.IGNORECASE)


_REGEX = build_regex()


def scan_injection(text: str) -> list[str]:
    if not text:
        return []
    matches = set()
    for m in _REGEX.finditer(text):
        window = text[max(0, m.start() - 20) : m.end() + 40].replace("\n", " ")
        matches.add(window.strip()[:120])
    return sorted(matches)
