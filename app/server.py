"""
Language Ducks — маленький сервер для игры.

Запускается на ноутбуке командой:
    python3 server.py

Раздаёт файлы из этой же папки (app/) и отвечает на запросы игры
через простые JSON-эндпоинты вида /api/....

Только стандартная библиотека Python. Ничего не ставим.
Состояние игры хранится в памяти, в обычном словаре — как только
сервер остановят, игра забывается. Это нормально: игра одноразовая,
на один вечер за столом.
"""

import json
import random
import socket
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from words import WORDS

PORT = 8000
APP_DIR = Path(__file__).resolve().parent
MAX_PLAYERS = 10
MIN_PLAYERS = 2
MAX_NAME_LENGTH = 12
WORDS_PER_ROUND = 5
# Сколько секунд ждём после последнего ответа, прежде чем показать
# результаты — чтобы последний игрок успел убрать палец от экрана.
REVEAL_DELAY_SECONDS = 2.0
# Сколько секунд держим показ ответов, прежде чем перейти к следующему
# слову — чтобы за столом успели посмотреть и обсудить.
NEXT_WORD_DELAY_SECONDS = 6.0
# Сколько очков даёт правильный ответ. Неверный или пропущенный — 0.
POINTS_CORRECT = 100

# Состояние игры целиком живёт здесь, в памяти сервера.
# Дальше, в следующих частях, сюда добавятся вопросы, очки и т.д.
# players — список словарей вида {"id": "...", "name": "..."}. Первый
# в списке — это игрок, который зашёл раньше всех, и только он может
# начать игру.
# phase — в какой фазе сейчас игра: "lobby" (собираем игроков),
# "playing" (игра идёт), "final" (финал). Следующие части будут
# показывать разное в зависимости от этого поля.
# stage — какой этап игры сейчас идёт: пока только "translate" (этап
# «Перевод»). Появится позже, когда добавится этап «Обманка».
# words — слова, выбранные на этот этап игры (5 штук, случайно из
# words.py), в порядке, в котором их показывают.
# word_index — индекс текущего слова в words (0 — первое слово).
# answers — ответы игроков на текущее слово: id игрока -> его ответ.
# Очищается, когда игра переходит к следующему слову.
# all_answered_time — момент (time.time()), когда ответили все игроки.
# None, пока кто-то ещё не ответил. Нужен, чтобы показать результаты
# не сразу, а через REVEAL_DELAY_SECONDS — дать время убрать палец.
# scored_this_word — очки за текущее слово уже начислены игрокам (True)
# или ещё нет (False). Не даёт начислить очки дважды за одно слово,
# пока сервер ждёт NEXT_WORD_DELAY_SECONDS перед следующим словом.
game_state = {
    "players": [],
    "phase": "lobby",
    "stage": None,
    "words": [],
    "word_index": 0,
    "answers": {},
    "all_answered_time": None,
    "scored_this_word": False,
}

# Защищает переход к следующему слову от гонки: экран и несколько
# телефонов опрашивают сервер каждую секунду, и без замка два запроса
# могли бы одновременно решить, что пора начислять очки или листать слово.
state_lock = threading.Lock()


def normalize_answer(text):
    """Приводит ответ к виду для сравнения: без пробелов по краям,
    в нижнем регистре, «ё» приравнена к «е». Никакой другой хитрости."""
    return text.strip().lower().replace("ё", "е")


def is_answer_correct(word, answer_text):
    """Проверяет ответ игрока по основному переводу и запасным вариантам."""
    if not answer_text:
        return False
    candidates = [word["answer"]] + word.get("alternatives", [])
    normalized_candidates = {normalize_answer(candidate) for candidate in candidates}
    return normalize_answer(answer_text) in normalized_candidates


def handle_join(payload):
    """Обрабатывает вход игрока, переименование или проверку сохранённого id.

    Если пришёл известный id — это тот же телефон, что уже играет.
    Если вместе с id пришло новое имя и игра ещё не началась —
    переименовываем игрока, а не заводим второго (иначе при повторном
    входе на экране появлялся бы дубль). Если игра уже идёт, новое имя
    игнорируем — известный телефон просто возвращается в игру под
    прежним именем, без ошибки. Если имени нет или оно не изменилось —
    просто подтверждаем, что игрок уже в игре (нужно для обновления
    страницы на телефоне). Если id нет или он не найден (например,
    сервер перезапустили) — пробуем завести нового игрока по имени.
    """
    player_id = payload.get("id")
    raw_name = payload.get("name") or ""
    name = raw_name.strip()[:MAX_NAME_LENGTH]

    if player_id:
        existing_player = None
        for player in game_state["players"]:
            if player["id"] == player_id:
                existing_player = player
                break

        if existing_player:
            # Свой игрок — заходит заново, это можно в любой фазе игры,
            # иначе ведущий потеряет свою кнопку «Начать» при обновлении
            # страницы. А вот переименоваться можно только пока игра не
            # началась — если игра уже идёт, новое имя просто игнорируем
            # и возвращаем игрока в игру под прежним именем.
            if game_state["phase"] != "lobby" or not name or name.lower() == existing_player["name"].lower():
                return {"ok": True, "id": existing_player["id"], "name": existing_player["name"]}
            for player in game_state["players"]:
                if player is not existing_player and player["name"].lower() == name.lower():
                    return {"ok": False, "error": "Такое имя уже занято, выбери другое"}
            existing_player["name"] = name
            return {"ok": True, "id": existing_player["id"], "name": existing_player["name"]}

        if game_state["phase"] != "lobby":
            return {"ok": False, "error": "Игра уже началась, подожди следующую"}

        if not name:
            return {"ok": False, "error": "Игра началась заново, зайди ещё раз"}

    if game_state["phase"] != "lobby":
        return {"ok": False, "error": "Игра уже началась, подожди следующую"}

    if not name:
        return {"ok": False, "error": "Введи имя"}

    if len(game_state["players"]) >= MAX_PLAYERS:
        return {"ok": False, "error": "Игроков уже 10 — новых мест нет"}

    for player in game_state["players"]:
        if player["name"].lower() == name.lower():
            return {"ok": False, "error": "Такое имя уже занято, выбери другое"}

    new_player = {"id": uuid.uuid4().hex, "name": name, "score": 0}
    game_state["players"].append(new_player)
    return {"ok": True, "id": new_player["id"], "name": new_player["name"]}


def pick_round_words():
    """Выбирает 5 слов на партию: по одному случайному слову с каждого
    из 5 языков. Так слова в партии точно из разных языков, а заодно
    не может попасться два слова с одинаковым правильным переводом.
    """
    languages = sorted({w["language"] for w in WORDS})
    chosen = []
    used_answers = set()
    for language in languages:
        candidates = [w for w in WORDS
                      if w["language"] == language and w["answer"] not in used_answers]
        word = random.choice(candidates)
        chosen.append(word)
        used_answers.add(word["answer"])
    random.shuffle(chosen)
    return chosen


def handle_start(payload):
    """Обрабатывает нажатие «Начать игру» на телефоне ведущего.

    Начать может только самый первый зашедший игрок, и только пока
    игра ещё в лобби, и только если игроков минимум двое.
    """
    player_id = payload.get("id")

    if game_state["phase"] != "lobby":
        return {"ok": True}

    if not game_state["players"] or game_state["players"][0]["id"] != player_id:
        return {"ok": False, "error": "Начать игру может только тот, кто зашёл первым"}

    if len(game_state["players"]) < MIN_PLAYERS:
        return {"ok": False, "error": "Нужен хотя бы ещё один игрок"}

    game_state["phase"] = "playing"
    game_state["stage"] = "translate"
    game_state["words"] = pick_round_words()
    game_state["word_index"] = 0
    game_state["answers"] = {}
    game_state["all_answered_time"] = None
    game_state["scored_this_word"] = False
    return {"ok": True}


def handle_answer(payload):
    """Обрабатывает ответ игрока на текущее слово этапа «Перевод».

    Каждый игрок отвечает на одно слово только один раз: если ответ
    уже сохранён, второй присланный ответ просто игнорируем — первый
    остаётся в силе, чтобы никто не мог подсмотреть чужие ответы и
    переписать свой.
    """
    player_id = payload.get("id")
    answer_text = (payload.get("answer") or "").strip()

    if game_state["phase"] != "playing":
        return {"ok": False, "error": "Сейчас не время отвечать"}

    player = None
    for candidate in game_state["players"]:
        if candidate["id"] == player_id:
            player = candidate
            break
    if not player:
        return {"ok": False, "error": "Игрок не найден"}

    if not answer_text:
        return {"ok": False, "error": "Ответ пустой"}

    if player_id not in game_state["answers"]:
        game_state["answers"][player_id] = answer_text
        if len(game_state["answers"]) >= len(game_state["players"]):
            game_state["all_answered_time"] = time.time()

    return {"ok": True}


def advance_game():
    """Двигает игру вперёд по времени: начисляет очки за раскрытое слово
    и, спустя NEXT_WORD_DELAY_SECONDS после раскрытия, переходит к
    следующему слову или (после последнего) — к финалу.

    Вызывается перед каждым ответом на /api/info. Экраны сами ничего
    не решают — только показывают то, что отдаёт сервер, иначе ноутбук
    и телефоны могли бы разойтись во времени.
    """
    with state_lock:
        if game_state["phase"] != "playing" or not game_state["words"]:
            return
        if game_state["all_answered_time"] is None:
            return

        reveal_time = game_state["all_answered_time"] + REVEAL_DELAY_SECONDS
        now = time.time()
        if now < reveal_time:
            return

        if not game_state["scored_this_word"]:
            current_word = game_state["words"][game_state["word_index"]]
            for player in game_state["players"]:
                player_answer = game_state["answers"].get(player["id"])
                if is_answer_correct(current_word, player_answer):
                    player["score"] += POINTS_CORRECT
            game_state["scored_this_word"] = True

        if now - reveal_time >= NEXT_WORD_DELAY_SECONDS:
            if game_state["word_index"] + 1 < len(game_state["words"]):
                game_state["word_index"] += 1
                game_state["answers"] = {}
                game_state["all_answered_time"] = None
                game_state["scored_this_word"] = False
            else:
                game_state["phase"] = "final"


def compute_ranks(sorted_players):
    """Считает места по очкам с учётом ничьих: у игроков с одинаковым
    счётом — одно и то же место, а следующее место пропускается
    (как в спорте: 1, 1, 3), а не выдумывается победитель наугад."""
    ranks = []
    previous_score = None
    previous_rank = 0
    for index, player in enumerate(sorted_players):
        if player["score"] != previous_score:
            rank = index + 1
        else:
            rank = previous_rank
        ranks.append(rank)
        previous_rank = rank
        previous_score = player["score"]
    return ranks


def handle_restart(payload):
    """Обрабатывает «Сыграть ещё раз» на телефоне ведущего.

    Работает только в фазе "final" и только для первого зашедшего
    игрока. Обнуляет очки и возвращает игру в лобби — сами игроки
    остаются, заново вводить имена не нужно. Слова на новую партию
    выбираются заново, когда ведущий снова нажмёт «Начать игру».
    """
    player_id = payload.get("id")

    if game_state["phase"] != "final":
        return {"ok": False, "error": "Сыграть ещё раз можно только после игры"}

    if not game_state["players"] or game_state["players"][0]["id"] != player_id:
        return {"ok": False, "error": "Начать новую игру может только ведущий"}

    for player in game_state["players"]:
        player["score"] = 0

    game_state["phase"] = "lobby"
    game_state["stage"] = None
    game_state["words"] = []
    game_state["word_index"] = 0
    game_state["answers"] = {}
    game_state["all_answered_time"] = None
    game_state["scored_this_word"] = False
    return {"ok": True}


def get_local_ip():
    """Узнаёт адрес ноутбука в домашней Wi-Fi сети.

    Трюк: "подключаемся" по UDP к 8.8.8.8 — реального пакета это не
    отправляет (UDP ничего не проверяет заранее), зато операционная
    система выбирает, через какой сетевой интерфейс это письмо пошло
    бы, и мы подсматриваем адрес этого интерфейса.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        sock.close()
    return ip


LOCAL_IP = get_local_ip()


class GameRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Не засорять терминал техническими логами каждого запроса.
        pass

    def send_json(self, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, filename):
        file_path = APP_DIR / filename
        if not file_path.is_file():
            # Сообщение об ошибке должно быть латиницей — иначе сервер
            # падает при запросе, например, браузером /favicon.ico.
            self.send_error(404, "Not found")
            return

        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }
        content_type = content_types.get(file_path.suffix, "application/octet-stream")

        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/info":
            advance_game()

            query = parse_qs(parsed_url.query)
            player_id = (query.get("id") or [None])[0]
            is_host = bool(
                player_id
                and game_state["players"]
                and game_state["players"][0]["id"] == player_id
            )

            current_word = None
            if game_state["phase"] == "playing" and game_state["words"]:
                current_word = game_state["words"][game_state["word_index"]]

            answered_names = [
                player["name"] for player in game_state["players"]
                if player["id"] in game_state["answers"]
            ]

            # Показываем результаты только через REVEAL_DELAY_SECONDS после
            # того, как ответил последний игрок — чтобы успел убрать палец.
            revealed = (
                current_word is not None
                and game_state["all_answered_time"] is not None
                and (time.time() - game_state["all_answered_time"]) >= REVEAL_DELAY_SECONDS
            )

            results = []
            my_correct = False
            if revealed:
                for player in game_state["players"]:
                    player_answer = game_state["answers"].get(player["id"])
                    correct = is_answer_correct(current_word, player_answer)
                    results.append({
                        "name": player["name"],
                        "answered": player["id"] in game_state["answers"],
                        "answer": player_answer,
                        "correct": correct,
                        "points": POINTS_CORRECT if correct else 0,
                    })
                if player_id:
                    my_correct = is_answer_correct(current_word, game_state["answers"].get(player_id))

            # Таблица очков — от лидера к последнему. При равном счёте
            # порядок как в списке игроков (кто зашёл раньше), а место
            # (rank) у них одинаковое — это честная ничья, а не выдумка.
            sorted_players = sorted(game_state["players"], key=lambda p: -p["score"])
            ranks = compute_ranks(sorted_players)
            scoreboard = [
                {"name": player["name"], "score": player["score"], "rank": rank}
                for player, rank in zip(sorted_players, ranks)
            ]

            my_score = None
            my_rank = None
            for player, rank in zip(sorted_players, ranks):
                if player["id"] == player_id:
                    my_score = player["score"]
                    my_rank = rank
                    break

            my_points = None
            if revealed and player_id:
                my_points = POINTS_CORRECT if my_correct else 0

            self.send_json({
                "address": "{}:{}".format(LOCAL_IP, PORT),
                "playerCount": len(game_state["players"]),
                "players": [player["name"] for player in game_state["players"]],
                "phase": game_state["phase"],
                "isHost": is_host,
                "stage": game_state["stage"],
                "wordIndex": game_state["word_index"] + 1 if current_word else 0,
                "wordTotal": len(game_state["words"]),
                "word": current_word["word"] if current_word else None,
                "wordLanguage": current_word["language"] if current_word else None,
                "answeredNames": answered_names,
                "answeredCount": len(game_state["answers"]),
                "allAnswered": bool(game_state["players"])
                and len(game_state["answers"]) >= len(game_state["players"]),
                "myAnswered": bool(player_id) and player_id in game_state["answers"],
                "myAnswerText": game_state["answers"].get(player_id) if player_id else None,
                "revealed": revealed,
                "correctAnswer": current_word["answer"] if revealed else None,
                "results": results,
                "myCorrect": my_correct,
                "scoreboard": scoreboard,
                "myScore": my_score,
                "myRank": my_rank,
                "myPoints": my_points,
            })
            return

        if path == "/":
            self.serve_file("index.html")
            return

        # Убираем ведущий "/", чтобы отдать файл из папки app/
        self.serve_file(path.lstrip("/"))

    def do_POST(self):
        path = self.path.split("?")[0]

        if path == "/api/join":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw_body = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = {}
            self.send_json(handle_join(payload))
            return

        if path == "/api/start":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw_body = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = {}
            self.send_json(handle_start(payload))
            return

        if path == "/api/answer":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw_body = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = {}
            self.send_json(handle_answer(payload))
            return

        if path == "/api/restart":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw_body = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = {}
            self.send_json(handle_restart(payload))
            return

        self.send_error(404, "Not found")


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), GameRequestHandler)
    print()
    print("=" * 45)
    print("   ИГРА ЗАПУЩЕНА!")
    print("=" * 45)
    print()
    print("   Адрес для телефонов друзей (тот же Wi-Fi):")
    print()
    print("   >>>  {}:{}  <<<".format(LOCAL_IP, PORT))
    print()
    print("   Чтобы закончить игру — просто закрой это окно.")
    print("=" * 45)
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")


if __name__ == "__main__":
    main()
