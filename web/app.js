"use strict";

const state = {
  notes: [],
  todos: [],
  characters: [],
  archives: [],
  calendar: { entries: [] },
  selectedArchive: null,
  archiveEntries: [],
  database: "",
  catalog: [],
  snapshots: {},
  systemActions: [],
  files: { path: "", parent: "", entries: [] },
  selectedFile: null,
  activeAction: null,
  events: [],
  errors: 0,
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
const byId = (id, required = true) => {
  const node = document.getElementById(id);
  if (!node && required) throw new Error(`Erforderliches Oberflächenelement fehlt: #${id}`);
  return node;
};
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[char]));
const asArray = (value) => Array.isArray(value) ? value : [];
const asObject = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : {};

function light(id, status) {
  const node = byId(id, false);
  if (node) node.className = `light ${status}`;
}

function pulse(id, duration = 650) {
  light(id, "active");
  window.setTimeout(() => light(id, "idle"), duration);
}

function showToast(message, isError = false) {
  const toast = byId("toast", false);
  if (!toast) return;
  toast.textContent = String(message || "Aktion abgeschlossen.");
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 4200);
}

function reportError(error, { fatal = false, context = "Oberfläche" } = {}) {
  const message = error instanceof Error ? error.message : String(error);
  state.errors += 1;
  light("errorLight", state.errors > 2 ? "bad pulse" : "warn");
  addEvent(`${context}: ${message}`, "error");
  showToast(message, true);
  if (fatal) {
    const box = byId("fatalError", false);
    const text = byId("fatalErrorText", false);
    if (text) text.textContent = message;
    if (box) box.hidden = false;
  }
  console.error(context, error);
}

window.addEventListener("error", (event) => reportError(event.error || event.message, { fatal: true, context: "JavaScript" }));
window.addEventListener("unhandledrejection", (event) => reportError(event.reason, { fatal: true, context: "Asynchroner Vorgang" }));

function addEvent(message, type = "info") {
  state.events.unshift({ message: String(message), type, at: new Date() });
  state.events = state.events.slice(0, 12);
  renderFooter();
}

async function api(path, options = {}) {
  light("processLight", "active");
  const request = {
    credentials: "same-origin",
    cache: "no-store",
    ...options,
    headers: { Accept: "application/json", ...(options.headers || {}) },
  };
  if (request.body && !(request.body instanceof FormData)) {
    request.headers["Content-Type"] = "application/json";
  }
  try {
    const response = await fetch(path, request);
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
      ? await response.json()
      : { status: response.ok ? "ok" : "error", message: await response.text() };
    if (!response.ok || payload.status !== "ok") {
      throw new Error(payload.message || `HTTP ${response.status}`);
    }
    return payload.data ?? payload.payload ?? {};
  } finally {
    light("processLight", "idle");
  }
}

function setConnection(ok, database = "") {
  light("serverLight", ok ? "good" : "bad");
  byId("serverStatus").textContent = ok ? "Server verbunden" : "Server nicht erreichbar";
  light("dbLight", ok && database ? "good" : "warn");
  byId("databaseStatus").textContent = ok && database ? "Archivdatenbank verbunden" : "Datenbank wird initialisiert";
  byId("systemUrl").textContent = window.location.origin;
  byId("systemDatabase").textContent = database || "–";
  byId("archiveDatabase").textContent = database || "SQLite wird verbunden";
}

function navigate(view, { focus = true } = {}) {
  const target = $(`[data-panel="${CSS.escape(view)}"]`);
  if (!target) throw new Error(`Unbekannter Arbeitsbereich: ${view}`);
  $$('[data-view]').forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
    if (button.classList.contains("nav-button")) {
      button.setAttribute("aria-current", button.dataset.view === view ? "page" : "false");
    }
  });
  $$(".view").forEach((panel) => panel.classList.toggle("active", panel === target));
  try { localStorage.setItem("provoware_memo_active_view", view); } catch (_error) { /* optional */ }
  if (focus) byId("mainContent").focus({ preventScroll: true });
  addEvent(`Bereich geöffnet: ${view}`);
}

function formatDate(value, options = {}) {
  if (!value) return "–";
  const raw = String(value);
  const normalized = raw.length === 7 ? `${raw}-01T12:00:00` : `${raw.slice(0, 10)}T12:00:00`;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return raw;
  return new Intl.DateTimeFormat("de-DE", options).format(date);
}

function formatDateTime(value) {
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? "–" : new Intl.DateTimeFormat("de-DE", {
    dateStyle: "short", timeStyle: "short",
  }).format(date);
}

function normalizeModuleData(response) {
  if (!response || typeof response !== "object") return {};
  return asObject(response.data ?? response.payload ?? response);
}

function listFrom(data, keys) {
  const object = normalizeModuleData(data);
  for (const key of keys) {
    if (Array.isArray(object[key])) return object[key];
  }
  return [];
}

function renderDashboard() {
  const open = state.todos.filter((item) => item.status !== "erledigt");
  const done = state.todos.filter((item) => item.status === "erledigt");
  byId("metricNotes").textContent = state.notes.length;
  byId("metricOpenTasks").textContent = open.length;
  byId("metricDoneTasks").textContent = done.length;
  byId("metricCharacters").textContent = state.characters.length;
  byId("metricArchives").textContent = state.archives.length;
  byId("metricModules").textContent = state.catalog.filter((item) => item.enabled).length;

  const noteItems = [...state.notes]
    .sort((a, b) => String(b.updated_at || b.created_at).localeCompare(String(a.updated_at || a.created_at)))
    .slice(0, 5);
  byId("dashboardNotes").innerHTML = noteItems.length ? noteItems.map((note) => `
    <button class="item-card clickable" type="button" data-view="memo">
      <strong>${escapeHtml(note.title)}</strong><span>${escapeHtml(note.body || "").slice(0, 180)}</span>
      <small>${formatDate(note.updated_at || note.created_at)}</small>
    </button>`).join("") : '<span class="empty-state">Keine Notizen vorhanden.</span>';

  const todoItems = [...open].sort((a, b) => String(a.planned_date).localeCompare(String(b.planned_date))).slice(0, 6);
  byId("dashboardTasks").innerHTML = todoItems.length ? todoItems.map((item) => `
    <button class="item-card clickable" type="button" data-view="tasks">
      <strong>${escapeHtml(item.title)}</strong><span>${formatDate(item.planned_date)}</span>
      <small>${escapeHtml(item.notes || "")}</small>
    </button>`).join("") : '<span class="empty-state">Keine offenen Aufgaben vorhanden.</span>';

  const favorites = [
    ...state.notes.filter((item) => item.favorite).map((item) => ({ label: item.title, type: "Notiz", view: "memo" })),
    ...state.characters.filter((item) => item.favorite).map((item) => ({ label: item.name, type: "Charakter", view: "characters" })),
  ].slice(0, 8);
  const modules = state.catalog.filter((item) => item.enabled).slice(0, Math.max(0, 8 - favorites.length))
    .map((item) => ({ label: item.name, type: "Modul", view: "modules" }));
  byId("dashboardFavorites").innerHTML = [...favorites, ...modules].length
    ? [...favorites, ...modules].map((item) => `<button class="compact-link" type="button" data-view="${item.view}"><span>${escapeHtml(item.type)}</span><strong>${escapeHtml(item.label)}</strong></button>`).join("")
    : '<span class="empty-state">Noch keine Favoriten.</span>';
}

function sortedNotes() {
  const term = byId("noteSearch").value.trim().toLowerCase();
  const mode = byId("noteSort").value;
  const filtered = state.notes.filter((note) => !term || `${note.title} ${note.body} ${asArray(note.tags).join(" ")}`.toLowerCase().includes(term));
  if (mode === "oldest") return filtered.sort((a, b) => String(a.updated_at).localeCompare(String(b.updated_at)));
  if (mode === "title") return filtered.sort((a, b) => String(a.title).localeCompare(String(b.title), "de"));
  if (mode === "favorites") return filtered.sort((a, b) => Number(Boolean(b.favorite)) - Number(Boolean(a.favorite)));
  return filtered.sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)));
}

function renderNotes() {
  const notes = sortedNotes();
  byId("notesList").innerHTML = notes.length ? notes.map((note) => `
    <article class="item-card">
      <header><div><h4>${note.favorite ? "★ " : ""}${escapeHtml(note.title)}</h4><div class="item-meta"><span>${formatDate(note.updated_at || note.created_at)}</span>${asArray(note.tags).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div></div>
      <button class="button small secondary" type="button" data-note-favorite="${escapeHtml(note.id)}">${note.favorite ? "Favorit lösen" : "Favorit"}</button></header>
      <p>${escapeHtml(note.body)}</p>
      <div class="actions"><button class="button small secondary" type="button" data-module-id="notiz_editor" data-module-action="update_note" data-prefill='${escapeHtml(JSON.stringify({ id: note.id, title: note.title, body: note.body, tags: note.tags || [] }))}'>Bearbeiten</button></div>
    </article>`).join("") : '<span class="empty-state">Keine passenden Notizen vorhanden.</span>';
}

function renderTodos() {
  const filter = byId("todoFilter").value;
  const todos = [...state.todos]
    .filter((item) => filter === "all" || item.status === filter)
    .sort((a, b) => String(a.planned_date).localeCompare(String(b.planned_date)));
  byId("todosList").innerHTML = todos.length ? todos.map((item) => `
    <article class="item-card">
      <header><div><h4>${escapeHtml(item.title)}</h4><div class="item-meta"><span>${formatDate(item.planned_date)}</span><span class="tag">${escapeHtml(item.status)}</span></div></div>${item.status !== "erledigt" ? `<button class="button small primary" type="button" data-todo-complete="${escapeHtml(item.id)}">Erledigen</button>` : ""}</header>
      <p>${escapeHtml(item.notes || "")}</p>
    </article>`).join("") : '<span class="empty-state">Keine passenden Aufgaben vorhanden.</span>';
}

function renderCharacters() {
  const term = byId("characterSearch").value.trim().toLowerCase();
  const characters = state.characters.filter((item) => !term || JSON.stringify(item).toLowerCase().includes(term));
  byId("charactersList").innerHTML = characters.length ? characters.map((item) => `
    <article class="item-card">
      <header><div><h4>${item.favorite ? "★ " : ""}${escapeHtml(item.name)}</h4><div class="item-meta"><span class="tag">${escapeHtml(item.role || "Rolle offen")}</span><span>${escapeHtml(item.archetype || "")}</span></div></div><button class="button small secondary" type="button" data-character-favorite="${escapeHtml(item.id)}">${item.favorite ? "Favorit lösen" : "Favorit"}</button></header>
      <p>${escapeHtml(item.biography || "Keine Biografie hinterlegt.")}</p>
      <div class="item-meta">${asArray(item.traits).map((trait) => `<span class="tag">${escapeHtml(trait)}</span>`).join("")}</div>
      <div class="actions"><button class="button small secondary" type="button" data-module-id="charakter_modul" data-module-action="update_character" data-prefill='${escapeHtml(JSON.stringify({ id: item.id, name: item.name, role: item.role, archetype: item.archetype }))}'>Bearbeiten</button></div>
    </article>`).join("") : '<span class="empty-state">Keine passenden Charaktere vorhanden.</span>';
}

function daysInMonth(month) {
  const [year, monthNumber] = month.split("-").map(Number);
  if (!year || !monthNumber) return 31;
  return new Date(year, monthNumber, 0).getDate();
}

function renderCalendar() {
  const view = byId("calendarView").value;
  const reference = byId("calendarDate").value || new Date().toISOString().slice(0, 10);
  const entries = asArray(state.calendar.entries);
  if (view !== "monat") {
    byId("calendarGrid").innerHTML = entries.length ? entries.map((entry) => `
      <article class="item-card"><strong>${formatDate(entry.date)}</strong><span>${escapeHtml(entry.icon || "•")} ${escapeHtml(entry.title)}</span><small>${escapeHtml(entry.status || "")}</small></article>`).join("") : '<span class="empty-state">Keine Kalendereinträge vorhanden.</span>';
    return;
  }
  const month = reference.slice(0, 7);
  const grouped = new Map();
  entries.forEach((entry) => {
    if (!grouped.has(entry.date)) grouped.set(entry.date, []);
    grouped.get(entry.date).push(entry);
  });
  const cells = [];
  for (let day = 1; day <= daysInMonth(month); day += 1) {
    const date = `${month}-${String(day).padStart(2, "0")}`;
    const dayEntries = grouped.get(date) || [];
    cells.push(`<div class="calendar-day"><div class="date">${formatDate(date)}</div>${dayEntries.map((entry) => `<span class="calendar-event ${entry.status === "erledigt" ? "done" : ""}">${escapeHtml(entry.icon || "•")} ${escapeHtml(entry.title)}</span>`).join("")}</div>`);
  }
  byId("calendarGrid").innerHTML = cells.join("");
}

function renderArchives() {
  byId("archiveList").innerHTML = state.archives.length ? state.archives.map((archive) => `
    <button class="archive-button ${state.selectedArchive?.slug === archive.slug ? "active" : ""}" type="button" data-archive="${escapeHtml(archive.slug)}"><strong>${escapeHtml(archive.name)}</strong><br><span class="muted">${escapeHtml(archive.description || "")}</span></button>`).join("") : '<span class="empty-state">Keine Archive vorhanden.</span>';
  byId("archiveTitle").textContent = state.selectedArchive?.name || "Archiv auswählen";
  byId("archiveDescriptionText").textContent = state.selectedArchive?.description || "";
  $$("input, textarea, button", byId("archiveEntryForm")).forEach((control) => { control.disabled = !state.selectedArchive; });
  byId("archiveEntries").innerHTML = state.selectedArchive ? (state.archiveEntries.length ? state.archiveEntries.map((entry) => `
    <article class="item-card"><header><div><h4>${escapeHtml(entry.value)}</h4><div class="item-meta"><span class="tag">${escapeHtml(entry.category)}</span><span>${formatDate(entry.updated_at)}</span></div></div><div class="actions"><button class="button small secondary" type="button" data-module-id="archiv_manager" data-module-action="update_entry" data-prefill='${escapeHtml(JSON.stringify({ entry_id: entry.id, value: entry.value, category: entry.category }))}'>Bearbeiten</button><button class="button small danger" type="button" data-archive-delete="${entry.id}">Löschen</button></div></header></article>`).join("") : '<span class="empty-state">Dieses Archiv enthält noch keine Einträge.</span>') : '<span class="empty-state">Bitte ein Archiv auswählen.</span>';
}

function moduleCard(module) {
  const actions = asArray(module.actions);
  const snapshot = normalizeModuleData(state.snapshots[module.id]);
  const count = Object.values(snapshot).find((value) => Array.isArray(value))?.length;
  return `<article class="module-card panel" data-module-card="${escapeHtml(module.id)}">
    <header><div><p class="eyebrow">${escapeHtml(module.group || "MODUL")}</p><h3>${escapeHtml(module.name)}</h3></div><span class="tag">${module.enabled ? "aktiv" : "inaktiv"}</span></header>
    <p class="muted">${escapeHtml(module.description || "Registriertes Provoware-Memo-Modul")}</p>
    <div class="module-meta"><span>ID: ${escapeHtml(module.id)}</span>${module.version ? `<span>v${escapeHtml(module.version)}</span>` : ""}${Number.isInteger(count) ? `<span>${count} Einträge</span>` : ""}</div>
    <div class="action-chips">${actions.map((action) => `<button class="action-chip ${action.mode === "write" ? "write" : ""}" type="button" data-module-id="${escapeHtml(module.id)}" data-module-action="${escapeHtml(action.id)}">${escapeHtml(action.label)}</button>`).join("")}</div>
  </article>`;
}

function renderModuleCatalog() {
  const term = byId("moduleSearch").value.trim().toLowerCase();
  const filtered = state.catalog.filter((module) => !term || `${module.name} ${module.id} ${module.description} ${asArray(module.actions).map((item) => item.label).join(" ")}`.toLowerCase().includes(term));
  const groups = new Map();
  filtered.forEach((module) => {
    const group = module.group || "Weitere";
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group).push(module);
  });
  byId("moduleCatalog").innerHTML = groups.size ? [...groups.entries()].map(([group, modules]) => `
    <section class="module-group"><div class="group-heading"><h3>${escapeHtml(group)}</h3><span>${modules.length} Module</span></div><div class="module-grid">${modules.map(moduleCard).join("")}</div></section>`).join("") : '<span class="empty-state">Keine Module entsprechen dem Filter.</span>';

  const renderSubset = (id, moduleIds) => {
    const modules = state.catalog.filter((item) => moduleIds.includes(item.id));
    byId(id).innerHTML = modules.length ? modules.map(moduleCard).join("") : '<span class="empty-state">Keine Module verfügbar.</span>';
  };
  renderSubset("fileModuleCards", ["datei_manager", "datei_suche", "download_aufraeumen"]);
  renderSubset("mediaModuleCards", ["media_wavesurfer", "media_ffmpeg_wrapper"]);
  renderSubset("profileModuleCards", ["profil_manager"]);
}

function renderFiles() {
  const body = byId("fileTableBody");
  const entries = asArray(state.files.entries);
  body.innerHTML = entries.length ? entries.map((item) => `
    <tr class="file-row ${state.selectedFile?.path === item.path ? "selected" : ""}" data-file-path="${escapeHtml(item.path)}" data-file-directory="${item.directory ? "true" : "false"}">
      <td><button class="file-name-button" type="button" data-file-path="${escapeHtml(item.path)}" data-file-directory="${item.directory ? "true" : "false"}">${item.directory ? "📁" : item.image ? "🖼" : "📄"} ${escapeHtml(item.name)}</button></td>
      <td>${escapeHtml(item.type)}</td><td>${escapeHtml(item.size_label)}</td><td>${escapeHtml(item.modified_label)}</td>
    </tr>`).join("") : '<tr><td colspan="4" class="empty-state">Dieser Ordner enthält keine sichtbaren Einträge.</td></tr>';
  byId("filePath").value = state.files.path || byId("filePath").value;
  renderFilePreview();
}

function renderFilePreview() {
  const item = state.selectedFile;
  const image = byId("filePreviewImage");
  const fallback = byId("filePreviewFallback");
  if (!item) {
    image.hidden = true;
    image.removeAttribute("src");
    fallback.hidden = false;
    fallback.textContent = "Datei auswählen, um Vorschau und Metadaten anzuzeigen.";
    byId("filePreviewName").textContent = "Keine Auswahl";
    byId("filePreviewMeta").innerHTML = "";
    return;
  }
  byId("filePreviewName").textContent = item.name;
  byId("filePreviewMeta").innerHTML = `
    <div><dt>Typ</dt><dd>${escapeHtml(item.type)}</dd></div>
    <div><dt>Größe</dt><dd>${escapeHtml(item.size_label)}</dd></div>
    <div><dt>Geändert</dt><dd>${escapeHtml(item.modified_label)}</dd></div>
    <div><dt>Pfad</dt><dd>${escapeHtml(item.path)}</dd></div>`;
  if (item.image && !item.directory) {
    image.src = `/api/file-preview?path=${encodeURIComponent(item.path)}&t=${Date.now()}`;
    image.hidden = false;
    fallback.hidden = true;
    image.onerror = () => {
      image.hidden = true;
      fallback.hidden = false;
      fallback.textContent = "Die Bildvorschau konnte nicht geladen werden.";
    };
  } else {
    image.hidden = true;
    image.removeAttribute("src");
    fallback.hidden = false;
    fallback.textContent = item.directory ? "Ordner per Klick öffnen." : "Für diesen Dateityp ist keine Bildvorschau verfügbar.";
  }
}

async function loadFiles(path = "") {
  const params = new URLSearchParams({
    path: path || byId("filePath").value.trim(),
    sort: byId("fileSort").value,
    descending: String(byId("fileDescending").checked),
    hidden: String(byId("fileHidden").checked),
  });
  try {
    const data = await api(`/api/files?${params}`);
    state.files = { path: data.path || "", parent: data.parent || "", entries: asArray(data.entries) };
    state.selectedFile = null;
    renderFiles();
    addEvent(`Ordner geladen: ${state.files.path}`);
  } catch (error) {
    reportError(error, { context: "Datei-Manager" });
  }
}

function renderSystemActions() {
  byId("systemActions").innerHTML = state.systemActions.length ? state.systemActions.map((action) => `
    <article class="module-card panel"><header><h3>${escapeHtml(action.label || action.id)}</h3><span class="tag">System</span></header><p class="muted">${escapeHtml(action.description || "Geprüfte interne Systemaktion")}</p><button class="button ${action.mode === "write" ? "danger" : "secondary"}" type="button" data-system-action="${escapeHtml(action.id)}">Ausführen</button></article>`).join("") : '<span class="empty-state">Keine Systemaktionen verfügbar.</span>';
}

function renderSystem() {
  byId("systemModules").textContent = `${state.catalog.filter((item) => item.enabled).length} / ${state.catalog.length}`;
  byId("systemUpdated").textContent = formatDateTime(new Date());
  byId("moduleHealth").innerHTML = state.catalog.length ? state.catalog.map((module) => {
    const snap = asObject(state.snapshots[module.id]);
    const ok = snap.status !== "error";
    return `<div class="health-row"><span class="light ${ok ? "good" : "bad"}"></span><strong>${escapeHtml(module.name)}</strong><span>${escapeHtml(snap.message || (ok ? "bereit" : "fehlerhaft"))}</span></div>`;
  }).join("") : '<span class="empty-state">Keine Module geladen.</span>';
}

function renderFooter() {
  const recent = byId("recentEvents", false);
  if (recent) recent.innerHTML = state.events.length ? state.events.slice(0, 5).map((item) => `<div class="footer-event ${item.type}"><time>${item.at.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })}</time><span>${escapeHtml(item.message)}</span></div>`).join("") : "Noch keine Ereignisse.";
  const upcoming = byId("upcomingEvents", false);
  if (upcoming) {
    const tasks = state.todos.filter((item) => item.status !== "erledigt").sort((a, b) => String(a.planned_date).localeCompare(String(b.planned_date))).slice(0, 4);
    upcoming.innerHTML = tasks.length ? tasks.map((item) => `<div class="footer-event"><time>${formatDate(item.planned_date)}</time><span>${escapeHtml(item.title)}</span></div>`).join("") : "Keine anstehenden Aufgaben.";
  }
  const important = byId("importantInfo", false);
  if (important) important.innerHTML = `<div class="footer-event"><span>Lokaler Betrieb – Daten bleiben auf diesem Rechner.</span></div><div class="footer-event"><span>${state.catalog.length} Module registriert · ${state.errors} Oberflächenfehler</span></div>`;
}

function renderAll() {
  renderDashboard();
  renderNotes();
  renderTodos();
  renderCharacters();
  renderCalendar();
  renderArchives();
  renderModuleCatalog();
  renderFiles();
  renderSystemActions();
  renderSystem();
  renderFooter();
}

function snapshotList(moduleId, keys) {
  return listFrom(state.snapshots[moduleId], keys);
}

async function loadAll({ announce = false } = {}) {
  if (announce) addEvent("Gesamtdaten werden aktualisiert.");
  try {
    const data = await api("/api/bootstrap");
    state.notes = asArray(data.notes);
    state.todos = asArray(data.todos);
    state.archives = asArray(data.archives);
    state.calendar = asObject(data.calendar);
    state.database = String(data.database || "");
    state.catalog = asArray(data.modules);
    state.systemActions = asArray(data.system_actions);

    const snapshots = await api("/api/module-snapshots").catch((error) => {
      reportError(error, { context: "Modul-Snapshots" });
      return {};
    });
    state.snapshots = asObject(snapshots.snapshots || snapshots);
    state.characters = snapshotList("charakter_modul", ["characters", "items"]);
    if (!state.notes.length) state.notes = snapshotList("notiz_editor", ["notes", "items"]);
    if (!state.todos.length) state.todos = snapshotList("todo_kalender", ["items", "todos"]);
    if (!state.archives.length) state.archives = snapshotList("archiv_manager", ["archives"]);
    const templateResponse = await api("/api/modules/notiz_editor/list_templates").catch(() => ({}));
    const templates = listFrom(templateResponse, ["templates"]);
    const templateSelect = byId("noteTemplate");
    templateSelect.innerHTML = '<option value="">Ohne Vorlage</option>' + templates.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name || item.title || item.id)}</option>`).join("");

    if (state.selectedArchive) {
      state.selectedArchive = state.archives.find((item) => item.slug === state.selectedArchive.slug) || null;
    }
    setConnection(true, state.database);
    renderAll();
    pulse("saveLight", 400);
    addEvent("Alle Inhalte und Module wurden geladen.", "success");
  } catch (error) {
    setConnection(false, "");
    reportError(error, { context: "Daten laden" });
  }
}

async function loadArchive(slug) {
  state.selectedArchive = state.archives.find((archive) => archive.slug === slug) || null;
  if (!state.selectedArchive) return;
  const query = encodeURIComponent(byId("archiveSearch").value.trim());
  try {
    const data = await api(`/api/archives/${encodeURIComponent(slug)}/entries?query=${query}`);
    state.archiveEntries = asArray(data.entries);
    renderArchives();
    addEvent(`Archiv geöffnet: ${state.selectedArchive.name}`);
  } catch (error) {
    reportError(error, { context: "Archiv laden" });
  }
}

async function loadCalendar() {
  const view = byId("calendarView").value;
  const reference = byId("calendarDate").value || new Date().toISOString().slice(0, 10);
  try {
    state.calendar = await api(`/api/calendar?view=${encodeURIComponent(view)}&reference_date=${encodeURIComponent(reference)}`);
    renderCalendar();
    addEvent(`Kalenderansicht geladen: ${view}`);
  } catch (error) {
    reportError(error, { context: "Kalender laden" });
  }
}

function findAction(moduleId, actionId) {
  const module = state.catalog.find((item) => item.id === moduleId);
  const action = asArray(module?.actions).find((item) => item.id === actionId);
  if (!module || !action) throw new Error(`Modulaktion ist nicht registriert: ${moduleId}/${actionId}`);
  return { module, action };
}

function fieldControl(field, value) {
  const id = `dynamic_${field.name}`;
  const required = field.required ? "required" : "";
  const placeholder = field.placeholder ? `placeholder="${escapeHtml(field.placeholder)}"` : "";
  const current = value ?? field.default ?? "";
  if (field.type === "textarea" || field.type === "json") {
    const text = field.type === "json" && typeof current !== "string" ? JSON.stringify(current, null, 2) : String(current ?? "");
    return `<label>${escapeHtml(field.label)}<textarea id="${id}" name="${escapeHtml(field.name)}" rows="6" data-field-type="${escapeHtml(field.type)}" ${required} ${placeholder}>${escapeHtml(text)}</textarea></label>`;
  }
  if (field.type === "select") {
    return `<label>${escapeHtml(field.label)}<select id="${id}" name="${escapeHtml(field.name)}" data-field-type="select" ${required}>${asArray(field.options).map((option) => `<option value="${escapeHtml(option)}" ${String(option) === String(current) ? "selected" : ""}>${escapeHtml(option)}</option>`).join("")}</select></label>`;
  }
  if (field.type === "checkbox") {
    return `<label class="checkbox dynamic-checkbox"><input id="${id}" name="${escapeHtml(field.name)}" type="checkbox" data-field-type="checkbox" ${current ? "checked" : ""}><span>${escapeHtml(field.label)}</span></label>`;
  }
  const htmlType = ["date", "number", "color"].includes(field.type) ? field.type : "text";
  return `<label>${escapeHtml(field.label)}<input id="${id}" name="${escapeHtml(field.name)}" type="${htmlType}" data-field-type="${escapeHtml(field.type)}" value="${escapeHtml(current)}" ${required} ${placeholder}></label>`;
}

function openModuleAction(moduleId, actionId, prefill = {}) {
  const { module, action } = findAction(moduleId, actionId);
  state.activeAction = { module, action };
  byId("actionDialogModule").textContent = `${module.group || "MODUL"} · ${module.name}`;
  byId("actionDialogTitle").textContent = action.label;
  byId("actionDialogDescription").textContent = action.description || (action.mode === "write" ? "Diese Aktion verändert Daten." : "Diese Aktion liest bestehende Daten.");
  byId("moduleActionFields").innerHTML = asArray(action.fields).length
    ? action.fields.map((field) => fieldControl(field, prefill[field.name])).join("")
    : '<p class="muted">Diese Aktion benötigt keine zusätzlichen Angaben.</p>';
  const result = byId("moduleActionResult");
  result.hidden = true;
  result.textContent = "";
  const dialog = byId("actionDialog");
  if (typeof dialog.showModal === "function") dialog.showModal(); else dialog.setAttribute("open", "");
  addEvent(`Modulaktion geöffnet: ${module.name} – ${action.label}`);
}

function closeModuleAction() {
  const dialog = byId("actionDialog");
  if (typeof dialog.close === "function" && dialog.open) dialog.close(); else dialog.removeAttribute("open");
  state.activeAction = null;
}

function readDynamicForm() {
  const payload = {};
  $$('[name]', byId("moduleActionFields")).forEach((control) => {
    const type = control.dataset.fieldType || "text";
    let value;
    if (type === "checkbox") value = control.checked;
    else if (type === "number") value = control.value === "" ? null : Number(control.value);
    else if (type === "list") value = control.value.split(",").map((item) => item.trim()).filter(Boolean);
    else if (type === "json") {
      try { value = control.value.trim() ? JSON.parse(control.value) : {}; }
      catch (error) { throw new Error(`${control.closest("label")?.firstChild?.textContent || control.name}: ungültiges JSON (${error.message})`); }
    } else value = control.value;
    if (value !== "" && value !== null) payload[control.name] = value;
  });
  return payload;
}

async function executeModuleAction() {
  if (!state.activeAction) return;
  const { module, action } = state.activeAction;
  const payload = readDynamicForm();
  if (action.confirm && !window.confirm(action.confirm)) return;
  try {
    const data = await api(`/api/modules/${encodeURIComponent(module.id)}/${encodeURIComponent(action.id)}`, {
      method: "POST", body: JSON.stringify(payload),
    });
    const result = byId("moduleActionResult");
    result.textContent = JSON.stringify(data, null, 2);
    result.hidden = false;
    pulse("saveLight");
    addEvent(`${module.name}: ${action.label} erfolgreich.`, "success");
    showToast(`${action.label}: erfolgreich.`);
    if (action.mode === "write") await loadAll();
  } catch (error) {
    reportError(error, { context: `${module.name}: ${action.label}` });
  }
}

async function runSystemAction(actionId) {
  const descriptor = state.systemActions.find((item) => item.id === actionId) || {};
  const question = descriptor.confirm || `${descriptor.label || actionId} jetzt ausführen?`;
  if (descriptor.confirm && !window.confirm(question)) return;
  try {
    const data = await api(`/api/system/actions/${encodeURIComponent(actionId)}`, { method: "POST", body: "{}" });
    byId("systemOutput").textContent = data.output || JSON.stringify(data, null, 2);
    addEvent(`Systemaktion abgeschlossen: ${descriptor.label || actionId}`, "success");
    showToast(`${descriptor.label || actionId}: abgeschlossen.`);
    pulse("saveLight");
  } catch (error) {
    reportError(error, { context: `Systemaktion ${actionId}` });
  }
}

async function globalSearch(term) {
  const target = byId("globalSearchResults");
  target.innerHTML = '<span class="empty-state">Suche läuft …</span>';
  try {
    const data = await api(`/api/search?q=${encodeURIComponent(term)}`);
    const results = asArray(data.results);
    target.innerHTML = results.length ? results.map((item) => `<button class="search-result" type="button" data-view="${escapeHtml(item.view || item.target || "modules")}"><span class="tag">${escapeHtml(item.type || item.kind || "Treffer")}</span><strong>${escapeHtml(item.title || item.name || "Treffer")}</strong><small>${escapeHtml(item.excerpt || item.description || item.text || "")}</small></button>`).join("") : '<span class="empty-state">Keine Treffer gefunden.</span>';
    addEvent(`Globale Suche: ${results.length} Treffer.`);
  } catch (error) {
    reportError(error, { context: "Globale Suche" });
    target.innerHTML = `<span class="empty-state error-text">${escapeHtml(error.message)}</span>`;
  }
}

async function handleSubmit(event) {
  const form = event.target.closest("form");
  if (!form) return;
  event.preventDefault();
  try {
    if (form.id === "globalSearchForm") {
      await globalSearch(byId("globalSearchInput").value.trim());
    } else if (form.id === "noteForm") {
      const templateId = byId("noteTemplate").value;
      await api("/api/notes", { method: "POST", body: JSON.stringify({
        title: byId("noteTitle").value.trim(), body: byId("noteBody").value.trim(),
        tags: byId("noteTags").value.split(",").map((item) => item.trim()).filter(Boolean),
        template_id: templateId || undefined,
      }) });
      form.reset();
      pulse("saveLight");
      showToast("Notiz gespeichert.");
      await loadAll();
    } else if (form.id === "todoForm") {
      await api("/api/todos", { method: "POST", body: JSON.stringify({
        title: byId("todoTitle").value.trim(), planned_date: byId("todoDate").value, notes: byId("todoNotes").value.trim(),
      }) });
      form.reset();
      byId("todoDate").value = new Date().toISOString().slice(0, 10);
      pulse("saveLight");
      showToast("Aufgabe gespeichert.");
      await loadAll();
    } else if (form.id === "characterForm") {
      await api("/api/modules/charakter_modul/create_character", { method: "POST", body: JSON.stringify({
        name: byId("characterName").value.trim(), role: byId("characterRole").value.trim(), archetype: byId("characterArchetype").value.trim(),
        biography: byId("characterBiography").value.trim(), traits: byId("characterTraits").value.split(",").map((item) => item.trim()).filter(Boolean),
        goals: byId("characterGoals").value.split(",").map((item) => item.trim()).filter(Boolean), tags: byId("characterTags").value.split(",").map((item) => item.trim()).filter(Boolean),
      }) });
      form.reset();
      pulse("saveLight");
      showToast("Charakter gespeichert.");
      await loadAll();
    } else if (form.id === "archiveForm") {
      const data = await api("/api/archives", { method: "POST", body: JSON.stringify({
        name: byId("archiveName").value.trim(), description: byId("archiveDescription").value.trim(), split_on_comma: byId("archiveSplit").checked,
      }) });
      form.reset();
      byId("archiveSplit").checked = true;
      pulse("saveLight");
      await loadAll();
      if (data.archive?.slug) await loadArchive(data.archive.slug);
    } else if (form.id === "archiveEntryForm") {
      if (!state.selectedArchive) throw new Error("Bitte zuerst ein Archiv auswählen.");
      await api(`/api/archives/${encodeURIComponent(state.selectedArchive.slug)}/entries`, { method: "POST", body: JSON.stringify({
        category: byId("archiveCategory").value.trim(), value: byId("archiveValue").value.trim(),
      }) });
      byId("archiveValue").value = "";
      pulse("saveLight");
      await loadArchive(state.selectedArchive.slug);
    } else if (form.id === "moduleActionForm") {
      await executeModuleAction();
    }
  } catch (error) {
    reportError(error, { context: `Formular ${form.id}` });
  }
}

async function handleClick(event) {
  const viewButton = event.target.closest("[data-view]");
  if (viewButton) {
    navigate(viewButton.dataset.view);
    return;
  }
  const actionButton = event.target.closest("[data-action]");
  if (actionButton) {
    const action = actionButton.dataset.action;
    if (action === "toggle-sidebar") byId("sidebar").classList.toggle("collapsed");
    else if (action === "refresh-all") await loadAll({ announce: true });
    else if (action === "load-calendar") await loadCalendar();
    else if (action === "load-files" || action === "refresh-files") await loadFiles();
    else if (action === "file-parent" && state.files.parent) await loadFiles(state.files.parent);
    else if (action === "clear-output") byId("systemOutput").textContent = "Noch keine Systemaktion ausgeführt.";
    else if (action === "close-action-dialog") closeModuleAction();
    else if (action === "reload-page") window.location.reload();
    return;
  }
  const fileSortButton = event.target.closest("[data-file-sort]");
  if (fileSortButton) {
    const sort = fileSortButton.dataset.fileSort;
    if (byId("fileSort").value === sort) byId("fileDescending").checked = !byId("fileDescending").checked;
    else { byId("fileSort").value = sort; byId("fileDescending").checked = false; }
    await loadFiles();
    return;
  }
  const fileButton = event.target.closest("[data-file-path]");
  if (fileButton) {
    const item = state.files.entries.find((entry) => entry.path === fileButton.dataset.filePath);
    if (!item) return;
    if (item.directory) await loadFiles(item.path);
    else { state.selectedFile = item; renderFiles(); addEvent(`Datei ausgewählt: ${item.name}`); }
    return;
  }
  const moduleButton = event.target.closest("[data-module-id][data-module-action]");
  if (moduleButton) {
    let prefill = {};
    if (moduleButton.dataset.prefill) {
      try { prefill = JSON.parse(moduleButton.dataset.prefill); } catch (_error) { prefill = {}; }
    }
    openModuleAction(moduleButton.dataset.moduleId, moduleButton.dataset.moduleAction, prefill);
    return;
  }
  const systemButton = event.target.closest("[data-system-action]");
  if (systemButton) { await runSystemAction(systemButton.dataset.systemAction); return; }
  const archiveButton = event.target.closest("[data-archive]");
  if (archiveButton) { await loadArchive(archiveButton.dataset.archive); return; }
  const favoriteButton = event.target.closest("[data-note-favorite]");
  if (favoriteButton) {
    await api(`/api/notes/${encodeURIComponent(favoriteButton.dataset.noteFavorite)}/favorite`, { method: "POST", body: "{}" });
    pulse("saveLight"); await loadAll(); return;
  }
  const characterFavorite = event.target.closest("[data-character-favorite]");
  if (characterFavorite) {
    await api("/api/modules/charakter_modul/toggle_favorite", { method: "POST", body: JSON.stringify({ id: characterFavorite.dataset.characterFavorite }) });
    pulse("saveLight"); await loadAll(); return;
  }
  const completeButton = event.target.closest("[data-todo-complete]");
  if (completeButton) {
    await api(`/api/todos/${encodeURIComponent(completeButton.dataset.todoComplete)}/complete`, { method: "POST", body: "{}" });
    pulse("saveLight"); await loadAll(); return;
  }
  const deleteButton = event.target.closest("[data-archive-delete]");
  if (deleteButton && state.selectedArchive && window.confirm("Archiveintrag wirklich löschen?")) {
    await api(`/api/archive-entries/${encodeURIComponent(deleteButton.dataset.archiveDelete)}`, { method: "DELETE" });
    pulse("saveLight"); await loadArchive(state.selectedArchive.slug);
  }
}

function handleInput(event) {
  if (event.target.id === "noteSearch" || event.target.id === "noteSort") renderNotes();
  else if (event.target.id === "todoFilter") renderTodos();
  else if (event.target.id === "characterSearch") renderCharacters();
  else if (event.target.id === "moduleSearch") renderModuleCatalog();
  else if (["fileSort", "fileDescending", "fileHidden"].includes(event.target.id) && state.files.path) loadFiles();
  else if (event.target.id === "archiveSearch" && state.selectedArchive) {
    window.clearTimeout(handleInput.archiveTimer);
    handleInput.archiveTimer = window.setTimeout(() => loadArchive(state.selectedArchive.slug), 220);
  }
}

function handleKeydown(event) {
  if (event.key === "F1") { event.preventDefault(); navigate("help"); return; }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "r") { event.preventDefault(); loadAll({ announce: true }); return; }
  if (!event.altKey) return;
  const map = { "1": "dashboard", n: "memo", a: "tasks", k: "calendar", m: "modules" };
  const view = map[event.key.toLowerCase()];
  if (view) { event.preventDefault(); navigate(view); }
}

function updateClock() {
  const now = new Date();
  byId("headerTime").textContent = now.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  byId("headerDate").textContent = now.toLocaleDateString("de-DE", { weekday: "long", day: "2-digit", month: "long", year: "numeric" });
}

function bindEvents() {
  document.addEventListener("click", (event) => {
    handleClick(event).catch((error) => reportError(error, { context: "Klickaktion" }));
  });
  document.addEventListener("submit", (event) => {
    handleSubmit(event).catch((error) => reportError(error, { context: "Formularaktion" }));
  });
  document.addEventListener("input", handleInput);
  document.addEventListener("change", handleInput);
  document.addEventListener("keydown", handleKeydown);
}

async function init() {
  try {
    bindEvents();
    const today = new Date().toISOString().slice(0, 10);
    byId("todoDate").value = today;
    byId("calendarDate").value = today;
    updateClock();
    window.setInterval(updateClock, 1000);
    const initialView = (() => {
      try { return localStorage.getItem("provoware_memo_active_view") || "dashboard"; }
      catch (_error) { return "dashboard"; }
    })();
    navigate($(`[data-panel="${CSS.escape(initialView)}"]`) ? initialView : "dashboard", { focus: false });
    document.documentElement.dataset.appReady = "binding";
    await loadAll();
    await loadFiles("");
    document.documentElement.dataset.appReady = "true";
    addEvent("Provoware Memo ist vollständig bedienbar.", "success");
  } catch (error) {
    document.documentElement.dataset.appReady = "error";
    reportError(error, { fatal: true, context: "Initialisierung" });
  }
}

document.addEventListener("DOMContentLoaded", init, { once: true });
