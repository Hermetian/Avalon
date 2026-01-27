const api = (path, options = {}) => fetch(path, options).then(async (res) => {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || res.statusText);
  }
  return res.json();
});

const $ = (id) => document.getElementById(id);
const roleGrid = $("roleGrid");
const humanCountEl = $("humanCount");
const botCountEl = $("botCount");
const totalCountEl = $("totalCount");
const joinLinksEl = $("joinLinks");
const serverStatusEl = $("serverStatus");
const phaseValueEl = $("phaseValue");
const publicStateEl = $("publicState");
const eventLogEl = $("eventLog");
const setupHintEl = $("setupHint");
const roleHintEl = $("roleHint");

const optionalRoles = [
  "Morgana",
  "Mordred",
  "Oberon",
  "Minion of Mordred",
  "Loyal Servant",
];

const mandatoryRoles = ["Merlin", "Percival", "Assassin"];

let humanCount = 2;
let botCount = 3;

function updateTotals() {
  const total = humanCount + botCount;
  humanCountEl.textContent = humanCount;
  botCountEl.textContent = botCount;
  totalCountEl.textContent = total;
  const valid = total >= 5 && total <= 10;
  totalCountEl.style.color = valid ? "inherit" : "#c75c2c";
}

function createRoleToggle(role) {
  const wrapper = document.createElement("div");
  wrapper.className = "role-card";
  const label = document.createElement("label");
  label.textContent = role;
  const toggle = document.createElement("input");
  toggle.type = "checkbox";
  toggle.checked = role === "Loyal Servant";
  toggle.dataset.role = role;
  wrapper.appendChild(label);
  wrapper.appendChild(toggle);
  return wrapper;
}

optionalRoles.forEach((role) => roleGrid.appendChild(createRoleToggle(role)));

function adjustCount(kind, delta) {
  if (kind === "human") {
    humanCount = Math.max(1, humanCount + delta);
  } else {
    botCount = Math.max(0, botCount + delta);
  }
  updateTotals();
}

$("humanUp").addEventListener("click", () => adjustCount("human", 1));
$("humanDown").addEventListener("click", () => adjustCount("human", -1));
$("botUp").addEventListener("click", () => adjustCount("bot", 1));
$("botDown").addEventListener("click", () => adjustCount("bot", -1));

function buildPlayers() {
  const players = [];
  for (let i = 1; i <= humanCount; i += 1) {
    players.push({ id: `h${i}`, name: `Human ${i}`, is_bot: false });
  }
  for (let i = 1; i <= botCount; i += 1) {
    players.push({ id: `b${i}`, name: `Bot ${i}`, is_bot: true });
  }
  return players;
}

function buildRoles(totalPlayers) {
  const selected = mandatoryRoles.slice();
  const toggles = roleGrid.querySelectorAll("input[type=checkbox]");
  toggles.forEach((toggle) => {
    if (toggle.checked) selected.push(toggle.dataset.role);
  });
  while (selected.length < totalPlayers) {
    selected.push("Loyal Servant");
  }
  if (selected.length > totalPlayers) {
    return null;
  }
  return selected;
}

function renderJoinLinks(players) {
  if (!players.length) {
    joinLinksEl.textContent = "No links yet.";
    return;
  }
  joinLinksEl.innerHTML = "";
  players.filter((p) => !p.is_bot).forEach((player) => {
    const card = document.createElement("div");
    card.className = "link-card";
    const url = `${window.location.origin}/play?player_id=${player.id}`;
    card.innerHTML = `<strong>${player.name}</strong><p class="hint">${url}</p>`;
    joinLinksEl.appendChild(card);
  });
}

async function refreshState() {
  try {
    const state = await api("/game/state");
    serverStatusEl.textContent = "Online";
    phaseValueEl.textContent = state.state ? state.state.phase : "No game";
    publicStateEl.textContent = JSON.stringify(state.state, null, 2);
  } catch (err) {
    serverStatusEl.textContent = "Offline";
    publicStateEl.textContent = "Unable to reach server.";
  }
}

async function refreshEvents() {
  try {
    const events = await api("/game/events");
    eventLogEl.textContent = JSON.stringify(events.events, null, 2);
  } catch (err) {
    eventLogEl.textContent = "Unable to load events.";
  }
}

$("createGame").addEventListener("click", async () => {
  try {
    const players = buildPlayers();
    const total = players.length;
    if (total < 5 || total > 10) {
      throw new Error("Total players must be between 5 and 10.");
    }
    const roles = buildRoles(total);
    if (!roles) {
      throw new Error("Too many roles selected for the player count.");
    }
    const hammer = $("hammerRule").checked;
    await api("/game/new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ players, roles, hammer_auto_approve: hammer }),
    });
    setupHintEl.textContent = "Game created.";
    renderJoinLinks(players);
    await refreshState();
    await refreshEvents();
  } catch (err) {
    setupHintEl.textContent = err.message;
  }
});

$("startGame").addEventListener("click", async () => {
  try {
    await api("/game/start", { method: "POST" });
    setupHintEl.textContent = "Game started.";
    await refreshState();
    await refreshEvents();
  } catch (err) {
    setupHintEl.textContent = err.message;
  }
});

function updateRoleHint() {
  const toggles = roleGrid.querySelectorAll("input[type=checkbox]");
  const selected = [...toggles].filter((toggle) => toggle.checked).map((toggle) => toggle.dataset.role);
  roleHintEl.textContent = `Mandatory: ${mandatoryRoles.join(", ")}. Selected: ${selected.join(", ") || "None"}.`;
}

roleGrid.addEventListener("change", updateRoleHint);
updateRoleHint();
updateTotals();
refreshState();
refreshEvents();
setInterval(refreshState, 2000);
setInterval(refreshEvents, 4000);
