// Общий код для страниц игры Language Ducks.

// Спрашивает у сервера адрес подключения и количество игроков.
async function fetchGameInfo() {
  const response = await fetch("/api/info");
  return response.json();
}
