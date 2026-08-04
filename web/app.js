"use strict";

const state = {
  notes: [],
  todos: [],
  archives: [],
  calendar: { entries: [] },
  selectedArchive: null,
  archiveEntries: [],
  database: "",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[char]));

function showToast(message, error = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", error);
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 3500);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({ status: "error", message: "Ungültige Serverantwort." }));
  if (!response.ok || payload.status !== "ok") {
    throw new Error(payload.message || `HTTP ${response.status}`);
  }
  return payload.data;
}

function setConnection(ok, database = "") {
  $("#serverLight").className = `light ${ok ? "good" : "bad"}`;
  $("#serverStatus").textContent = ok ? "Server verbunden" : "Server nicht erreichbar";
  $("#dbLight").className = `light ${ok && database ? "good" : "bad"}`;
  $("#databaseStatus").textContent = ok && database ? "Archivdatenbank verbunden" : "Datenbank nicht verbunden";
  $("#systemUrl").textContent = window.location.origin;
  $("#systemDatabase").textContent = database || "–";
  $("#archiveDatabase").textContent = database || "SQLite nicht verbunden";
}

function navigate(view) {
  $$(".nav-button").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  $$(".view").forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === view));
}

function formatDate(value) {
  if (!value) return "–";
  const date = new Date(`${value.slice(0, 10)}T12:00:00`);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("de-DE").format(date);
}

function renderDashboard() {
  const open = state.todos.filter((item) => item.status !== "erledigt");
  const done = state.todos.filter((item) => item.status === "erledigt");
  $("#metricNotes").textContent = state.notes.length;
  $("#metricOpenTasks").textContent = open.length;
  $("#metricDoneTasks").textContent = done.length;
  $("#metricArchives").textContent = state.archives.length;
  const noteItems = [...state.notes].sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at))).slice(0, 5);
  $("#dashboardNotes").innerHTML = noteItems.length ? noteItems.map((note) => `
    <div class="item-card"><h4>${escapeHtml(note.title)}</h4><p>${escapeHtml(note.body).slice(0, 220)}</p><div class="item-meta"><span>${formatDate(note.updated_at)}</span></div></div>`).join("") : "Keine Notizen vorhanden.";
  const todoItems = [...open].sort((a, b) => String(a.planned_date).localeCompare(String(b.planned_date))).slice(0, 6);
  $("#dashboardTasks").innerHTML = todoItems.length ? todoItems.map((item) => `
    <div class="item-card"><h4>${escapeHtml(item.title)}</h4><div class="item-meta"><span>${formatDate(item.planned_date)}</span><span>${escapeHtml(item.notes || "")}</span></div></div>`).join("") : "Keine offenen Aufgaben vorhanden.";
}

function renderNotes() {
  const term = $("#noteSearch").value.trim().toLowerCase();
  const notes = [...state.notes]
    .filter((note) => !term || `${note.title} ${note.body} ${(note.tags || []).join(" ")}`.toLowerCase().includes(term))
    .sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)));
  $("#notesList").innerHTML = notes.length ? notes.map((note) => `
    <article class="item-card">
      <header><div><h4>${note.favorite ? "★ " : ""}${escapeHtml(note.title)}</h4><div class="item-meta"><span>${formatDate(note.updated_at)}</span>${(note.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div></div><button class="button small secondary" data-note-favorite="${escapeHtml(note.id)}">${note.favorite ? "Favorit lösen" : "Favorit"}</button></header>
      <p>${escapeHtml(note.body)}</p>
    </article>`).join("") : "Keine passenden Notizen vorhanden.";
}

function renderTodos() {
  const filter = $("#todoFilter").value;
  const todos = [...state.todos]
    .filter((item) => filter === "all" || item.status === filter)
    .sort((a, b) => String(a.planned_date).localeCompare(String(b.planned_date)));
  $("#todosList").innerHTML = todos.length ? todos.map((item) => `
    <article class="item-card">
      <header><div><h4>${escapeHtml(item.title)}</h4><div class="item-meta"><span>${formatDate(item.planned_date)}</span><span class="tag">${escapeHtml(item.status)}</span></div></div>${item.status !== "erledigt" ? `<button class="button small primary" data-todo-complete="${escapeHtml(item.id)}">Erledigen</button>` : ""}</header>
      <p>${escapeHtml(item.notes || "")}</p>
    </article>`).join("") : "Keine passenden Aufgaben vorhanden.";
}

function daysInMonth(month) {
  const [year, monthNumber] = month.split("-").map(Number);
  return new Date(year, monthNumber, 0).getDate();
}

function renderCalendar() {
  const month = $("#calendarDate").value || new Date().toISOString().slice(0, 7);
  const grouped = new Map();
  (state.calendar.entries || []).forEach((entry) => {
    if (!grouped.has(entry.date)) grouped.set(entry.date, []);
    grouped.get(entry.date).push(entry);
  });
  const cells = [];
  for (let day = 1; day <= daysInMonth(month); day += 1) {
    const date = `${month}-${String(day).padStart(2, "0")}`;
    const entries = grouped.get(date) || [];
    cells.push(`<div class="calendar-day"><div class="date">${formatDate(date)}</div>${entries.map((entry) => `<span class="calendar-event ${entry.status === "erledigt" ? "done" : ""}">${escapeHtml(entry.icon)} ${escapeHtml(entry.title)}</span>`).join("")}</div>`);
  }
  $("#calendarGrid").innerHTML = cells.join("");
}

function renderArchives() {
  $("#archiveList").innerHTML = state.archives.length ? state.archives.map((archive) => `
    <button class="archive-button ${state.selectedArchive?.slug === archive.slug ? "active" : ""}" data-archive="${escapeHtml(archive.slug)}"><strong>${escapeHtml(archive.name)}</strong><br><span class="muted">${escapeHtml(archive.description || "")}</span></button>`).join("") : "Keine Archive vorhanden.";
  $("#archiveTitle").textContent = state.selectedArchive?.name || "Archiv auswählen";
  $("#archiveDescriptionText").textContent = state.selectedArchive?.description || "";
  $("#archiveEntryForm").querySelectorAll("input, textarea, button").forEach((control) => { control.disabled = !state.selectedArchive; });
  $("#archiveEntries").innerHTML = state.selectedArchive ? (state.archiveEntries.length ? state.archiveEntries.map((entry) => `
    <article class="item-card">
      <header><div><h4>${escapeHtml(entry.value)}</h4><div class="item-meta"><span class="tag">${escapeHtml(entry.category)}</span><span>${formatDate(entry.updated_at)}</span></div></div><button class="button small danger" data-archive-delete="${entry.id}">Löschen</button></header>
    </article>`).join("") : "Dieses Archiv enthält noch keine Einträge.") : "Bitte ein Archiv auswählen.";
}

function renderAll() {
  renderDashboard();
  renderNotes();
  renderTodos();
  renderCalendar();
  renderArchives();
}

async function loadAll() {
  try {
    const data = await api("/api/bootstrap");
    state.notes = data.notes || [];
    state.todos = data.todos || [];
    state.archives = data.archives || [];
    state.calendar = data.calendar || { entries: [] };
    state.database = data.database || "";
    if (state.selectedArchive) {
      state.selectedArchive = state.archives.find((item) => item.slug === state.selectedArchive.slug) || null;
    }
    setConnection(true, state.database);
    renderAll();
  } catch (error) {
    setConnection(false, "");
    showToast(error.message, true);
  }
}

async function loadArchive(slug) {
  state.selectedArchive = state.archives.find((archive) => archive.slug === slug) || null;
  if (!state.selectedArchive) return;
  const query = encodeURIComponent($("#archiveSearch").value.trim());
  try {
    const data = await api(`/api/archives/${encodeURIComponent(slug)}/entries?query=${query}`);
    state.archiveEntries = data.entries || [];
    renderArchives();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function loadCalendar() {
  const month = $("#calendarDate").value || new Date().toISOString().slice(0, 7);
  try {
    state.calendar = await api(`/api/calendar?view=monat&reference_date=${month}-01`);
    renderCalendar();
  } catch (error) {
    showToast(error.message, true);
  }
}

function bindEvents() {
  $$(".nav-button").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.view)));
  $("#refreshAll").addEventListener("click", loadAll);
  $("#noteSearch").addEventListener("input", renderNotes);
  $("#todoFilter").addEventListener("change", renderTodos);
  $("#calendarLoad").addEventListener("click", loadCalendar);
  $("#archiveSearch").addEventListener("input", () => state.selectedArchive && loadArchive(state.selectedArchive.slug));

  $("#noteForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await api("/api/notes", { method: "POST", body: JSON.stringify({
        title: $("#noteTitle").value.trim(), body: $("#noteBody").value.trim(),
        tags: $("#noteTags").value.split(",").map((tag) => tag.trim()).filter(Boolean),
      }) });
      event.currentTarget.reset();
      showToast("Notiz gespeichert.");
      await loadAll();
    } catch (error) { showToast(error.message, true); }
  });

  $("#todoForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await api("/api/todos", { method: "POST", body: JSON.stringify({
        title: $("#todoTitle").value.trim(), planned_date: $("#todoDate").value, notes: $("#todoNotes").value.trim(),
      }) });
      event.currentTarget.reset();
      $("#todoDate").value = new Date().toISOString().slice(0, 10);
      showToast("Aufgabe gespeichert.");
      await loadAll();
    } catch (error) { showToast(error.message, true); }
  });

  $("#archiveForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const data = await api("/api/archives", { method: "POST", body: JSON.stringify({
        name: $("#archiveName").value.trim(), description: $("#archiveDescription").value.trim(), split_on_comma: $("#archiveSplit").checked,
      }) });
      event.currentTarget.reset();
      $("#archiveSplit").checked = true;
      showToast("Archiv angelegt.");
      await loadAll();
      if (data.archive?.slug) await loadArchive(data.archive.slug);
    } catch (error) { showToast(error.message, true); }
  });

  $("#archiveEntryForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.selectedArchive) return;
    try {
      await api(`/api/archives/${encodeURIComponent(state.selectedArchive.slug)}/entries`, { method: "POST", body: JSON.stringify({
        category: $("#archiveCategory").value.trim(), value: $("#archiveValue").value.trim(),
      }) });
      $("#archiveValue").value = "";
      showToast("Archiveintrag gespeichert.");
      await loadArchive(state.selectedArchive.slug);
    } catch (error) { showToast(error.message, true); }
  });

  document.addEventListener("click", async (event) => {
    const archiveButton = event.target.closest("[data-archive]");
    if (archiveButton) { await loadArchive(archiveButton.dataset.archive); return; }
    const favoriteButton = event.target.closest("[data-note-favorite]");
    if (favoriteButton) {
      try { await api(`/api/notes/${encodeURIComponent(favoriteButton.dataset.noteFavorite)}/favorite`, { method: "POST", body: "{}" }); await loadAll(); } catch (error) { showToast(error.message, true); }
      return;
    }
    const completeButton = event.target.closest("[data-todo-complete]");
    if (completeButton) {
      try { await api(`/api/todos/${encodeURIComponent(completeButton.dataset.todoComplete)}/complete`, { method: "POST", body: "{}" }); await loadAll(); } catch (error) { showToast(error.message, true); }
      return;
    }
    const deleteButton = event.target.closest("[data-archive-delete]");
    if (deleteButton && state.selectedArchive && window.confirm("Archiveintrag wirklich löschen?")) {
      try { await api(`/api/archive-entries/${deleteButton.dataset.archiveDelete}`, { method: "DELETE" }); await loadArchive(state.selectedArchive.slug); } catch (error) { showToast(error.message, true); }
    }
  });
}

function init() {
  const today = new Date().toISOString().slice(0, 10);
  $("#todoDate").value = today;
  $("#calendarDate").value = today.slice(0, 7);
  bindEvents();
  loadAll();
}

document.addEventListener("DOMContentLoaded", init);
