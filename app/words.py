"""
Language Ducks — слова для этапа «Перевод».

Каждое слово — это словарь:
    word         — само слово на иностранном языке
    language     — язык по-русски, для показа на экране
    answer       — правильный перевод
    alternatives — запасные варианты перевода, которые тоже считаются
                   верными (например «бабочка» и «мотылёк»)

Проверка ответа игрока с этим списком будет в следующей части —
здесь только сами слова. По 4 слова на язык, от простых до неочевидных,
чтобы было интересно и школьнику, и взрослому за столом.
"""

WORDS = [
    # Английский
    {"word": "cat", "language": "английский", "answer": "кот",
     "alternatives": ["кошка", "котик"]},
    {"word": "mirror", "language": "английский", "answer": "зеркало",
     "alternatives": []},
    {"word": "butterfly", "language": "английский", "answer": "бабочка",
     "alternatives": ["мотылёк"]},
    {"word": "serendipity", "language": "английский", "answer": "счастливая случайность",
     "alternatives": ["удачное совпадение", "приятная неожиданность"]},

    # Немецкий
    {"word": "die Katze", "language": "немецкий", "answer": "кошка",
     "alternatives": ["кот"]},
    {"word": "der Spiegel", "language": "немецкий", "answer": "зеркало",
     "alternatives": []},
    {"word": "der Schmetterling", "language": "немецкий", "answer": "бабочка",
     "alternatives": ["мотылёк"]},
    {"word": "der Kummerspeck", "language": "немецкий", "answer": "заедание горя",
     "alternatives": ["стрессовый жир", "жир от переживаний", "заедание стресса"]},

    # Испанский
    {"word": "el gato", "language": "испанский", "answer": "кот",
     "alternatives": ["кошка"]},
    {"word": "el espejo", "language": "испанский", "answer": "зеркало",
     "alternatives": []},
    {"word": "la mariposa", "language": "испанский", "answer": "бабочка",
     "alternatives": ["мотылёк"]},
    {"word": "la sobremesa", "language": "испанский", "answer": "разговор за столом после еды",
     "alternatives": ["посиделки после обеда", "время за столом после еды"]},

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
    {"word": "парасон", "language": "белорусский", "answer": "зонтик",
     "alternatives": ["зонт"]},
    {"word": "вавёрка", "language": "белорусский", "answer": "белка",
     "alternatives": []},
]
