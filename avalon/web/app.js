const api = (path, options = {}) => fetch(path, options).then(async (res) => {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || res.statusText);
  }
  return res.json();
});

const $ = (id) => document.getElementById(id);

const stateEls = {
  serverStatus: $("serverStatus"),
  phaseValue: $("phaseValue"),
  publicState: $("publicState"),
  eventLog: $("eventLog"),
  privateState: $("privateState"),
  setupHint: $("setupHint"),
  actionHint: $("actionHint"),
};

const playerIdInput = $("playerId");

const formatJson = (obj) => JSON.stringify(obj, null, 2);

async function refreshState() {
  try {
    const state = await api("/game/state");
    stateEls.serverStatus.textContent = "Online";
    stateEls.phaseValue.textContent = state.state ? state.state.phase : "No game";
    stateEls.publicState.textContent = formatJson(state.state);
  } catch (err) {
    stateEls.serverStatus.textContent = "Offline";
    stateEls.publicState.textContent = "Unable to reach server.";
  }
}

async function refreshEvents() {
  try {
    const events = await api("/game/events");
    stateEls.eventLog.textContent = formatJson(events.events);
  } catch (err) {
    stateEls.eventLog.textContent = "Unable to load events.";
  }
}

async function loadPrivate() {
  const playerId = playerIdInput.value.trim();
  if (!playerId) return;
  try {
    const privateState = await api(`/game/state?player_id=${playerId}`);
    stateEls.privateState.textContent = formatJson(privateState);
  } catch (err) {
    stateEls.privateState.textContent = err.message;
  }
}

function parseJson(text, fallback) {
  if (!text.trim()) return fallback;
  return JSON.parse(text);
}

$("createGame").addEventListener("click", async () => {
  try {
    const players = parseJson($("playersJson").value, []);
    const roles = parseJson($("rolesJson").value, null);
    const hammer = $("hammerRule").checked;
    const payload = { players, hammer_auto_approve: hammer };
    if (roles) payload.roles = roles;
    await api("/game/new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    stateEls.setupHint.textContent = "Game created.";
    await refreshState();
    await refreshEvents();
  } catch (err) {
    stateEls.setupHint.textContent = err.message;
  }
});

$("startGame").addEventListener("click", async () => {
  try {
    await api("/game/start", { method: "POST" });
    stateEls.setupHint.textContent = "Game started.";
    await refreshState();
    await refreshEvents();
  } catch (err) {
    stateEls.setupHint.textContent = err.message;
  }
});

$("loadPrivate").addEventListener("click", loadPrivate);

$("sendChat").addEventListener("click", async () => {
  const playerId = playerIdInput.value.trim();
  const message = $("chatMessage").value.trim();
  if (!playerId || !message) return;
  try {
    await api("/game/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id: playerId, action_type: "chat", payload: { message } }),
    });
    $("chatMessage").value = "";
    await refreshState();
    await refreshEvents();
  } catch (err) {
    stateEls.actionHint.textContent = err.message;
  }
});

$("proposeTeam").addEventListener("click", async () => {
  const playerId = playerIdInput.value.trim();
  const raw = $("teamIds").value.trim();
  const team = raw ? raw.split(",").map((id) => id.trim()).filter(Boolean) : [];
  try {
    await api("/game/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id: playerId, action_type: "propose_team", payload: { team } }),
    });
    stateEls.actionHint.textContent = "Team proposed.";
    await refreshState();
    await refreshEvents();
  } catch (err) {
    stateEls.actionHint.textContent = err.message;
  }
});

$("approveTeam").addEventListener("click", () => voteTeam(true));
$("rejectTeam").addEventListener("click", () => voteTeam(false));

async function voteTeam(approve) {
  const playerId = playerIdInput.value.trim();
  try {
    await api("/game/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id: playerId, action_type: "vote_team", payload: { approve } }),
    });
    stateEls.actionHint.textContent = approve ? "Team approved." : "Team rejected.";
    await refreshState();
    await refreshEvents();
  } catch (err) {
    stateEls.actionHint.textContent = err.message;
  }
}

$("questSuccess").addEventListener("click", () => questVote(true));
$("questFail").addEventListener("click", () => questVote(false));

async function questVote(success) {
  const playerId = playerIdInput.value.trim();
  try {
    await api("/game/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id: playerId, action_type: "quest_vote", payload: { success } }),
    });
    stateEls.actionHint.textContent = success ? "Quest success sent." : "Quest fail sent.";
    await refreshState();
    await refreshEvents();
  } catch (err) {
    stateEls.actionHint.textContent = err.message;
  }
}

$("assassinate").addEventListener("click", async () => {
  const playerId = playerIdInput.value.trim();
  const targetId = $("assassinTarget").value.trim();
  try {
    await api("/game/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id: playerId, action_type: "assassinate", payload: { target_id: targetId } }),
    });
    stateEls.actionHint.textContent = "Assassination submitted.";
    await refreshState();
    await refreshEvents();
  } catch (err) {
    stateEls.actionHint.textContent = err.message;
  }
});

async function boot() {
  await refreshState();
  await refreshEvents();
  setInterval(refreshState, 2000);
  setInterval(refreshEvents, 4000);
}

boot();
