// Общий код для страниц игры Language Ducks.

// Спрашивает у сервера адрес подключения, количество игроков и фазу игры.
// playerId передаём, чтобы сервер сказал, ведущий ли это игрок.
async function fetchGameInfo(playerId) {
  const query = playerId ? "?id=" + encodeURIComponent(playerId) : "";
  const response = await fetch("/api/info" + query);
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

// Ведущий нажал «Начать игру».
async function startGame(playerId) {
  const response = await fetch("/api/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: playerId }),
  });
  return response.json();
}
