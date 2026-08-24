// Общий код для страниц игры Language Ducks.

// Спрашивает у сервера адрес подключения и количество игроков.
async function fetchGameInfo() {
  const response = await fetch("/api/info");
  return response.json();
}

// Отправляет вход в игру (или проверку уже сохранённого id).
async function joinGame(payload) {
  const response = await fetch("/api/join", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}
