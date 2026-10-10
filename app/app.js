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

// Игрок подтвердил выход из игры (крестик на телефоне).
async function leaveGame(playerId) {
  const response = await fetch("/api/leave", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: playerId }),
  });
  return response.json();
}

// Меняет длительность показа результатов с большого экрана (шестерёнка
// на Л1). payload — {translateResultSeconds: 10} и/или {trickResultSeconds: 5}.
async function sendSettings(payload) {
  const response = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

// Плавный обратный отсчёт между опросами сервера. Сервер даёт целые
// секунды (с округлением вверх), поэтому момент окончания — это
// «сейчас + секунды» с запасом до секунды. Каждый новый опрос только
// уточняет его в меньшую сторону (min), а цифра идёт строго вниз и не
// чаще одного шага за тик: без прыжков вверх и без пропусков.
// onTick(секунды) вызывается при каждой смене цифры; null — таймера нет.
function createCountdown(onTick) {
  let stepKey = null;
  let endMs = null;
  let shown = null;

  setInterval(() => {
    if (endMs === null) {
      return;
    }
    const target = Math.max(0, Math.ceil((endMs - Date.now()) / 1000));
    if (target < shown) {
      shown -= 1;
      onTick(shown);
    }
  }, 200);

  return function update(newStepKey, secondsLeft) {
    if (secondsLeft === null) {
      stepKey = null;
      endMs = null;
      shown = null;
      onTick(null);
      return;
    }
    const newEnd = Date.now() + secondsLeft * 1000;
    if (newStepKey !== stepKey || endMs === null) {
      stepKey = newStepKey;
      endMs = newEnd;
      shown = secondsLeft;
      onTick(shown);
    } else {
      endMs = Math.min(endMs, newEnd);
    }
  };
}
