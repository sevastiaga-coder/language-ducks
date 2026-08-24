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
import socket
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT = 8000
APP_DIR = Path(__file__).resolve().parent
MAX_PLAYERS = 10
MIN_PLAYERS = 2
MAX_NAME_LENGTH = 12

# Состояние игры целиком живёт здесь, в памяти сервера.
# Дальше, в следующих частях, сюда добавятся вопросы, очки и т.д.
# players — список словарей вида {"id": "...", "name": "..."}. Первый
# в списке — это игрок, который зашёл раньше всех, и только он может
# начать игру.
# phase — в какой фазе сейчас игра: "lobby" (собираем игроков),
# "playing" (игра идёт), "final" (финал). Следующие части будут
# показывать разное в зависимости от этого поля.
game_state = {
    "players": [],
    "phase": "lobby",
}


def handle_join(payload):
    """Обрабатывает вход игрока, переименование или проверку сохранённого id.

    Если пришёл известный id — это тот же телефон, что уже играет.
    Если вместе с id пришло новое имя — переименовываем игрока, а не
    заводим второго (иначе при повторном входе на экране появлялся бы
    дубль). Если имени нет или оно не изменилось — просто подтверждаем,
    что игрок уже в игре (нужно для обновления страницы на телефоне).
    Если id нет или он не найден (например, сервер перезапустили) —
    пробуем завести нового игрока по имени.
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
            # Свой игрок — заходит заново или переименовывается, это можно
            # в любой фазе игры, иначе ведущий потеряет свою кнопку «Начать»
            # при обновлении страницы.
            if not name or name.lower() == existing_player["name"].lower():
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

    new_player = {"id": uuid.uuid4().hex, "name": name}
    game_state["players"].append(new_player)
    return {"ok": True, "id": new_player["id"], "name": new_player["name"]}


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
            query = parse_qs(parsed_url.query)
            player_id = (query.get("id") or [None])[0]
            is_host = bool(
                player_id
                and game_state["players"]
                and game_state["players"][0]["id"] == player_id
            )
            self.send_json({
                "address": "{}:{}".format(LOCAL_IP, PORT),
                "playerCount": len(game_state["players"]),
                "players": [player["name"] for player in game_state["players"]],
                "phase": game_state["phase"],
                "isHost": is_host,
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

        self.send_error(404, "Not found")


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), GameRequestHandler)
    print("Language Ducks запущен!")
    print("Экран ноутбука: http://localhost:{}/screen.html".format(PORT))
    print("Адрес для телефонов: http://{}:{}".format(LOCAL_IP, PORT))
    print("Чтобы остановить — нажми Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")


if __name__ == "__main__":
    main()
