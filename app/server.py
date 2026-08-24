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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8000
APP_DIR = Path(__file__).resolve().parent

# Состояние игры целиком живёт здесь, в памяти сервера.
# Дальше, в следующих частях, сюда добавятся игроки, вопросы, очки и т.д.
game_state = {
    "players": [],
}


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
            self.send_error(404, "Файл не найден")
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
        path = self.path.split("?")[0]

        if path == "/api/info":
            self.send_json({
                "address": "{}:{}".format(LOCAL_IP, PORT),
                "playerCount": len(game_state["players"]),
            })
            return

        if path == "/":
            self.serve_file("screen.html")
            return

        # Убираем ведущий "/", чтобы отдать файл из папки app/
        self.serve_file(path.lstrip("/"))


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
