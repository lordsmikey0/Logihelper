from rapidfuzz import process, fuzz
import os
import json


ALIASES = {
    "мультиплексор": "Multiplexer",
    "мукс": "Multiplexer",
    "mux": "Multiplexer",
    "демультиплексор": "Demultiplexer",
    "демукс": "Demultiplexer",
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
    "мили": "Mealy machine"
}

def normalize_user_query(user_query: str):
    """
    Возвращает:
    - clean_query (str): нормализованная строка для анализа маркеров
    - detected_term (str | None): точное имя найденного компонента для базы знаний
    """
    words = user_query.lower().split()
    normalized_words = []
    detected_terms = set()

    for word in words:
        if len(word) <= 2:
            normalized_words.append(word)
            continue

        match = process.extractOne(word, ALIASES.keys(), scorer=fuzz.WRatio, score_cutoff=75)

        if match:
            best_key, score, _ = match
            term_name = ALIASES[best_key]
            normalized_words.append(term_name.lower())
            detected_terms.add(term_name)
        else:
            normalized_words.append(word)

    return " ".join(normalized_words), list(detected_terms)


def get_from_guide(clean_query: str, detected_terms: list, filepath: str = "logisim_docs.json") -> str:
    """
    Динамически собирает кастомный контекст для СПИСКА найденных терминов.
    """
    if not detected_terms or not os.path.exists(filepath):
        return ""

    with open(filepath, "r", encoding="utf-8") as f:
        docs = json.load(f)

    all_matched_blocks = []

    # Маркеры проверяем один раз для всего запроса
    query_lower = clean_query.lower()
    practice_markers = ['собрать', 'схема', 'ошибка', 'logisim', 'логисим', 'мигает', 'не работает', 'oscillation',
                        'подключить']
    compare_markers = ['разница', 'отличие', 'сравни', 'vs', 'чем отличается', 'или']

    is_practice = any(marker in query_lower for marker in practice_markers)
    is_compare = any(marker in query_lower for marker in compare_markers)

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
