import json
import re
from pathlib import Path

from rapidfuzz import process
from rapidfuzz.distance import DamerauLevenshtein


MODEL_DOCS_PATH = Path(__file__).resolve().parents[1] / "data" / "model_docs.json"


ALIASES = {
    "мультиплексор": "Multiplexer",
    "мукс": "Multiplexer",
    "multiplexer": "Multiplexer",
    "mux": "Multiplexer",
    "демультиплексор": "Demultiplexer",
    "демукс": "Demultiplexer",
    "demultiplexer": "Demultiplexer",
    "demux": "Demultiplexer",
    "декодер": "Decoder",
    "дешифратор": "Decoder",
    "полусумматор": "Half Adder",
    "сумматор": "Full Adder",
    "алу": "Arithmetic Logic Unit",
    "alu": "Arithmetic Logic Unit",
    "такт": "Clock",
    "tact": "Clock",
    "d-триггер": "D flip-flop",
    "d-trigger": "D flip-flop",
    "регистр": "Register",
    "мура": "Moore machine",
    "мили": "Mealy machine",
    "decoder": "Decoder",
    "half adder": "Half Adder",
    "full adder": "Full Adder",
    "arithmetic logic unit": "Arithmetic Logic Unit",
    "d flip-flop": "D flip-flop",
    "register": "Register",
    "n-bit register": "Register",
    "clock": "Clock",
    "clock generator": "Clock",
    "clk": "Clock",
    "moore": "Moore machine",
    "moore machine": "Moore machine",
    "moore fsm": "Moore machine",
    "mealy": "Mealy machine",
    "mealy machine": "Mealy machine",
    "mealy fsm": "Mealy machine",
}

if MODEL_DOCS_PATH.is_file():
    with MODEL_DOCS_PATH.open(encoding="utf-8") as docs_file:
        for article in json.load(docs_file):
            for alias in article.get("aliases", ()):
                ALIASES[alias.casefold()] = article["term"]

_TOKEN_PATTERN = re.compile(r"\d+(?:[.,]\d+)?|[^\W\d_]+")


def _normalize_token(token: str) -> str:
    return token.casefold().replace("ё", "е").replace(",", ".")


def _numeric_tokens(words: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(word for word in words if word[0].isdigit())


_EXACT_ALIASES = {}
_FUZZY_ALIASES = {}
for alias, term in ALIASES.items():
    words = tuple(map(_normalize_token, _TOKEN_PATTERN.findall(alias)))
    phrase = " ".join(words)
    _EXACT_ALIASES[phrase] = term
    if len(phrase) >= 5:
        _FUZZY_ALIASES.setdefault((len(words), _numeric_tokens(words)), {})[phrase] = term

_MAX_ALIAS_WORDS = max(length for length, _ in _FUZZY_ALIASES)


def _match_alias(words: tuple[str, ...]) -> str | None:
    phrase = " ".join(words)
    if phrase in _EXACT_ALIASES:
        return _EXACT_ALIASES[phrase]

    candidates = _FUZZY_ALIASES.get((len(words), _numeric_tokens(words)))
    if not candidates or len(phrase) < 5:
        return None

    # Limit edits and require an unambiguous best match across article titles.
    max_edits = 1 if len(phrase) < 10 else 2
    best_distance = max_edits + 1
    best_terms = set()
    for alias, distance, _ in process.extract_iter(
        phrase, candidates.keys(), scorer=DamerauLevenshtein.distance, score_cutoff=max_edits
    ):
        if distance < best_distance:
            best_distance = distance
            best_terms.clear()
        if distance == best_distance:
            best_terms.add(candidates[alias])
    if len(best_terms) == 1:
        return best_terms.pop()
    return None


def normalize_user_query(user_query: str):
    """Return the normalized query and matching article titles in query order."""
    query = user_query.lower()
    tokens = list(_TOKEN_PATTERN.finditer(query))
    words = tuple(_normalize_token(token.group()) for token in tokens)
    normalized_parts = []
    detected_terms = {}
    position = 0
    start = 0

    while start < len(tokens):
        stop = start + 1
        while stop < min(len(tokens), start + _MAX_ALIAS_WORDS):
            separator = query[tokens[stop - 1].end():tokens[stop].start()]
            if separator.strip(" \t\r\n-–—"):
                break
            stop += 1

        # Try longer phrases first so specific topics beat generic aliases.
        for end in range(stop, start, -1):
            term = _match_alias(words[start:end])
            if term is not None:
                normalized_parts.extend((query[position:tokens[start].start()], term.lower()))
                detected_terms[term] = None
                position = tokens[end - 1].end()
                start = end
                break
        else:
            start += 1

    normalized_parts.append(query[position:])
    return " ".join("".join(normalized_parts).split()), list(detected_terms)


def get_from_guide(clean_query: str, detected_terms: list, filepath: str | Path = MODEL_DOCS_PATH) -> str:
    """
    Динамически собирает кастомный контекст для СПИСКА найденных терминов.
    """
    if not detected_terms or not Path(filepath).is_file():
        return ""

    with open(filepath, "r", encoding="utf-8") as f:
        docs = json.load(f)

    all_matched_blocks = []

    # Маркеры проверяем один раз для всего запроса
    query_lower = clean_query.lower()
    practice_markers = ['собрать', 'схема', 'ошибка', 'logisim', 'логисим', 'мигает', 'не работает', 'oscillation',
                        'подключить']
    compare_markers = ['разница', 'отличие', 'сравни', 'vs', 'отличается', 'или',
                       'compare', 'difference', 'differ']

    is_practice = any(marker in query_lower for marker in practice_markers)
    is_compare = any(re.search(rf"\b{marker}\b", query_lower) for marker in compare_markers)

    for term in detected_terms:
        target_data = None
        for item in docs:
            if item.get("term") == term:
                target_data = item
                break

        if not target_data:
            continue

        # Собираем блок для конкретного термина
        item_parts = [
            f"COMPONENT: {target_data['term']}",
            f"Core Theory: {target_data['definition']}",
            f"How it works: {target_data['how_it_works']}"
        ]

        # TODO: Add a CPU role in dataset
        # if "cpu_role" in target_data:
        #     item_parts.append(f"Role in CPU architecture: {target_data['cpu_role']}")

        if is_practice and 'logisim_recipe' in target_data:
            recipe = target_data['logisim_recipe']
            req_blocks = ", ".join(recipe.get('required_blocks', []))
            wiring_tip = recipe.get('wiring_tip', '')
            item_parts.append(f"Logisim Recipe: Blocks: {req_blocks}. Tip: {wiring_tip}")

            troubles = "; ".join(target_data.get('troubleshooting', []))
            if troubles:
                item_parts.append(f"Troubleshooting: {troubles}")

        if is_compare and 'comparison' in target_data:
            comp = target_data['comparison']
            item_parts.append(f"Comparison with {comp.get('versus')}: {comp.get('key_difference')}")

        all_matched_blocks.append("\n".join(item_parts))

    if not all_matched_blocks:
        return ""

    instruction = "\n\nUSE THESE [TECHNICAL DOCUMENTATION] PIECES TO ANSWER (Rely ONLY on this info, look for connections between components if asked):\n\n"
    return instruction + "\n\n* * *\n\n".join(all_matched_blocks)
