const api = (path, options = {}) => fetch(path, options).then(async (res) => {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || res.statusText);
  }
  return res.json();
});

const $ = (id) => document.getElementById(id);
const playerPickerEl = $("playerPicker");
const playerNameInput = $("playerNameInput");
const pickerHintEl = $("pickerHint");
const phaseValueEl = $("phaseValue");
const playerCountEl = $("playerCount");
const hostControlsEl = $("hostControls");
const hostSlotListEl = $("hostSlotList");
const hostAddHuman = $("hostAddHuman");
const hostRemoveHuman = $("hostRemoveHuman");

const isHost = ["localhost", "127.0.0.1"].includes(window.location.hostname);

function renderPicker(players) {
  playerPickerEl.innerHTML = "";
  if (!players.length) {
    playerPickerEl.textContent = "No players yet.";
    return;
  }
  players
    .filter((p) => !p.is_bot)
    .forEach((player) => {
      const row = document.createElement("div");
      row.className = "slot-row";
      const tag = document.createElement("span");
      tag.className = "slot-tag";
      tag.textContent = player.claimed ? "Claimed" : "Open";
      const name = document.createElement("div");
      name.textContent = player.name;
      const pickBtn = document.createElement("button");
      pickBtn.textContent = player.claimed ? "Taken" : "Choose";
      pickBtn.disabled = player.claimed;
      pickBtn.addEventListener("click", () => claimSeat(player.id));
      row.appendChild(tag);
      row.appendChild(name);
      row.appendChild(pickBtn);
      playerPickerEl.appendChild(row);
    });
}

function renderHostSlots(players) {
  hostSlotListEl.innerHTML = "";
  players
    .filter((p) => !p.is_bot)
    .forEach((player) => {
      const row = document.createElement("div");
      row.className = "slot-row";
      const tag = document.createElement("span");
      tag.className = "slot-tag";
      tag.textContent = player.claimed ? "Claimed" : "Open";
      const nameInput = document.createElement("input");
      nameInput.value = player.name;
      const saveBtn = document.createElement("button");
      saveBtn.className = "ghost";
      saveBtn.textContent = "Rename";
      saveBtn.addEventListener("click", async () => {
        await api("/game/players/rename", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ player_id: player.id, name: nameInput.value.trim() || player.name }),
        });
        await refresh();
      });
      const resetBtn = document.createElement("button");
      resetBtn.className = "ghost";
      resetBtn.textContent = "Kick";
      resetBtn.addEventListener("click", async () => {
        await api("/game/players/reset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ player_id: player.id }),
        });
        await refresh();
      });
      const removeBtn = document.createElement("button");
      removeBtn.className = "ghost";
      removeBtn.textContent = "Remove slot";
      removeBtn.addEventListener("click", async () => {
        await api("/game/players/remove", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ player_id: player.id }),
        });
        await refresh();
      });
      row.appendChild(tag);
      row.appendChild(nameInput);
      row.appendChild(saveBtn);
      row.appendChild(resetBtn);
      row.appendChild(removeBtn);
      hostSlotListEl.appendChild(row);
    });
}

async function claimSeat(targetId) {
  const name = playerNameInput.value.trim();
  if (!name) {
    pickerHintEl.textContent = "Enter your name first.";
    return;
  }
  try {
    await api("/game/players/claim", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id: targetId, name }),
    });
    localStorage.setItem("avalon_player_id", targetId);
    window.location.href = `/game?player_id=${targetId}`;
  } catch (err) {
    pickerHintEl.textContent = err.message;
  }
}

async function refresh() {
  try {
    const state = await api("/game/state");
    if (!state.state) {
      pickerHintEl.textContent = "Waiting for host to create a game.";
      return;
    }
    const players = state.state.players || [];
    phaseValueEl.textContent = state.state.phase;
    playerCountEl.textContent = players.length;
    renderPicker(players);
    if (isHost) {
      hostControlsEl.classList.remove("hidden");
      renderHostSlots(players);
    }
  } catch (err) {
    pickerHintEl.textContent = err.message;
  }
}

if (isHost) {
  hostAddHuman.addEventListener("click", async () => {
    await api("/game/players/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_bot: false }),
    });
    await refresh();
  });
  hostRemoveHuman.addEventListener("click", async () => {
    const state = await api("/game/state");
    const humans = (state.state?.players || []).filter((p) => !p.is_bot);
    if (!humans.length) return;
    const last = humans[humans.length - 1];
    await api("/game/players/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id: last.id }),
    });
    await refresh();
  });
}

refresh();
setInterval(refresh, 2000);
