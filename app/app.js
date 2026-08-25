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

// Игрок отправляет ответ на текущее слово.
async function sendAnswer(playerId, answer) {
  const response = await fetch("/api/answer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: playerId, answer: answer }),
  });
  return response.json();
}

// Игрок отправляет выдумку на текущее слово этапа «Обманка».
async function sendFib(playerId, fib) {
  const response = await fetch("/api/fib", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: playerId, fib: fib }),
  });
  return response.json();
}

// Игрок голосует за один из вариантов на голосовании «Обманки».
async function sendVote(playerId, index) {
  const response = await fetch("/api/vote", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: playerId, index: index }),
  });
  return response.json();
}

// Ведущий нажал «Сыграть ещё раз» в финале.
async function restartGame(playerId) {
  const response = await fetch("/api/restart", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: playerId }),
  });
  return response.json();
}
