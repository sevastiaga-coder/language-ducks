"""
Language Ducks — слова для этапа «Перевод».

Каждое слово — это словарь:
    word         — само слово на иностранном языке
    language     — язык по-русски, для показа на экране
    answer       — правильный перевод
    alternatives — запасные варианты перевода, которые тоже считаются
                   верными (например «бабочка» и «мотылёк»)

Проверка ответа игрока с этим списком будет в следующей части —
здесь только сами слова. По 4 слова на язык. Большинство слов —
узнаваемые, где можно угадать по созвучию или по школьным знаниям;
на каждый язык есть одно слово посложнее, но всё равно отгадываемое.
"""

WORDS = [
    # Английский
    {"word": "cat", "language": "английский", "answer": "кот",
     "alternatives": ["кошка", "котик"]},
    {"word": "mirror", "language": "английский", "answer": "зеркало",
     "alternatives": []},
    {"word": "butterfly", "language": "английский", "answer": "бабочка",
     "alternatives": ["мотылёк"]},
    {"word": "shadow", "language": "английский", "answer": "тень",
     "alternatives": []},

    # Немецкий
    {"word": "die Katze", "language": "немецкий", "answer": "кошка",
     "alternatives": ["кот"]},
    {"word": "der Spiegel", "language": "немецкий", "answer": "зеркало",
     "alternatives": []},
    {"word": "der Apfel", "language": "немецкий", "answer": "яблоко",
     "alternatives": []},
    {"word": "der Schmetterling", "language": "немецкий", "answer": "бабочка",
     "alternatives": ["мотылёк"]},

    # Испанский
    {"word": "el gato", "language": "испанский", "answer": "кот",
     "alternatives": ["кошка"]},
    {"word": "el espejo", "language": "испанский", "answer": "зеркало",
     "alternatives": []},
    {"word": "el paraguas", "language": "испанский", "answer": "зонт",
     "alternatives": ["зонтик"]},
    {"word": "la mariposa", "language": "испанский", "answer": "бабочка",
     "alternatives": ["мотылёк"]},

    # Украинский
    {"word": "кіт", "language": "украинский", "answer": "кот",
     "alternatives": ["кошка"]},
    {"word": "дзеркало", "language": "украинский", "answer": "зеркало",
     "alternatives": []},
    {"word": "метелик", "language": "украинский", "answer": "бабочка",
     "alternatives": ["мотылёк"]},
    {"word": "парасолька", "language": "украинский", "answer": "зонтик",
     "alternatives": ["зонт"]},

    # Белорусский
    {"word": "люстэрка", "language": "белорусский", "answer": "зеркало",
     "alternatives": []},
    {"word": "матылёк", "language": "белорусский", "answer": "бабочка",
     "alternatives": ["мотылёк"]},
    {"word": "агурок", "language": "белорусский", "answer": "огурец",
     "alternatives": []},
    {"word": "парасон", "language": "белорусский", "answer": "зонтик",
     "alternatives": ["зонт"]},
]
