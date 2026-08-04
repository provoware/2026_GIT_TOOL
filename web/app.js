"use strict";

const state = {
  notes: [],
  todos: [],
  characters: [],
  archives: [],
  calendar: { entries: [], appointments: [], legend: [], day_markers: [], reminders: { due: [], upcoming: [] } },
  miniCalendarDate: new Date().toISOString().slice(0, 10),
  notifiedReminderIds: new Set(),
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

function safeHex(value, fallback = "#64748b") {
  return /^#[0-9a-f]{6}$/i.test(String(value || "")) ? String(value).toLowerCase() : fallback;
}

function monthKey(value) {
  return String(value || new Date().toISOString().slice(0, 10)).slice(0, 7);
}

function addMonths(dateValue, amount) {
  const [year, month] = monthKey(dateValue).split("-").map(Number);
  const shifted = new Date(year, month - 1 + amount, 1, 12, 0, 0);
  return `${shifted.getFullYear()}-${String(shifted.getMonth() + 1).padStart(2, "0")}-01`;
}

function addDays(dateValue, amount) {
  const current = new Date(`${String(dateValue).slice(0, 10)}T12:00:00`);
  current.setDate(current.getDate() + amount);
  return current.toISOString().slice(0, 10);
}

function calendarLegendMap() {
  return new Map(asArray(state.calendar.legend).map((item) => [item.id, item]));
}

function calendarMarkerMap() {
  return new Map(asArray(state.calendar.day_markers).map((item) => [item.date, item]));
}

function calendarAppointmentMap() {
  const grouped = new Map();
  asArray(state.calendar.appointments).forEach((item) => {
    if (!grouped.has(item.date)) grouped.set(item.date, []);
    grouped.get(item.date).push(item);
  });
  return grouped;
}

function calendarTaskMap() {
  const grouped = new Map();
  asArray(state.calendar.entries).forEach((item) => {
    if (!grouped.has(item.date)) grouped.set(item.date, []);
    grouped.get(item.date).push(item);
  });
  return grouped;
}

function markerGradient(colors) {
  const values = asArray(colors).map((item) => safeHex(item.color));
  if (!values.length) return "none";
  const size = 100 / values.length;
  const stops = values.flatMap((color, index) => [
    `${color} ${Math.round(index * size * 100) / 100}%`,
    `${color} ${Math.round((index + 1) * size * 100) / 100}%`,
  ]);
  return `linear-gradient(135deg, ${stops.join(", ")})`;
}

function formatAppointmentTime(item) {
  if (item.all_day) return "Ganztägig";
  if (item.start_time && item.end_time) return `${item.start_time}–${item.end_time}`;
  return item.start_time || "Ohne Uhrzeit";
}

function renderCalendarLegendControls() {
  const legend = asArray(state.calendar.legend);
  byId("calendarLegend").innerHTML = legend.map((item) => `<span class="legend-chip"><i style="--legend-color:${safeHex(item.color)}"></i>${escapeHtml(item.title)}</span>`).join("");
  byId("calendarLegendEditor").innerHTML = legend.map((item, index) => `
    <div class="legend-editor-row">
      <input type="hidden" data-legend-id value="${escapeHtml(item.id)}">
      <input type="color" data-legend-color value="${safeHex(item.color)}" aria-label="Farbe ${index + 1}">
      <input type="text" data-legend-title value="${escapeHtml(item.title)}" maxlength="40" aria-label="Titel Farbe ${index + 1}" required>
    </div>`).join("");
  byId("dayColorOptions").innerHTML = legend.map((item) => `
    <label class="day-color-choice" style="--choice-color:${safeHex(item.color)}">
      <input type="checkbox" name="dayColor" value="${escapeHtml(item.id)}">
      <span>${escapeHtml(item.title)}</span>
    </label>`).join("");
  const colorSelect = byId("appointmentColor");
  const current = colorSelect.value;
  colorSelect.innerHTML = '<option value="">Ohne Farbe</option>' + legend.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.title)}</option>`).join("");
  colorSelect.value = legend.some((item) => item.id === current) ? current : "";
}

function renderCalendarReminders() {
  const reminders = asObject(state.calendar.reminders);
  const due = asArray(reminders.due);
  const upcoming = asArray(reminders.upcoming);
  const all = [...due, ...upcoming].slice(0, 12);
  byId("calendarReminderCount").textContent = `${due.length} offen`;
  byId("calendarReminders").innerHTML = all.length ? all.map((item) => `
    <article class="item-card reminder-card ${item.reminder_status === "due" ? "due" : ""}">
      <strong>${item.reminder_status === "due" ? "🔔 " : "◷ "}${escapeHtml(item.title)}</strong>
      <span>${formatDateTime(item.reminder_at)} · ${formatAppointmentTime(item)}</span>
      ${item.location ? `<small>${escapeHtml(item.location)}</small>` : ""}
      ${item.reminder_status === "due" ? `<button class="button small secondary" type="button" data-reminder-ack="${escapeHtml(item.id)}">Bestätigen</button>` : ""}
    </article>`).join("") : '<span class="empty-state">Keine offenen Erinnerungen.</span>';

  if (typeof Notification !== "undefined" && Notification.permission === "granted") {
    due.forEach((item) => {
      if (state.notifiedReminderIds.has(item.id)) return;
      state.notifiedReminderIds.add(item.id);
      new Notification(`Provoware Memo: ${item.title}`, {
        body: `${formatAppointmentTime(item)}${item.location ? ` · ${item.location}` : ""}`,
        tag: `provoware-${item.id}`,
      });
    });
  }
}

function renderCalendarAgenda() {
  const legend = calendarLegendMap();
  const appointments = [...asArray(state.calendar.appointments)].sort((a, b) => `${a.date} ${a.start_time || ""}`.localeCompare(`${b.date} ${b.start_time || ""}`));
  byId("calendarAppointmentCount").textContent = `${appointments.length} Termin${appointments.length === 1 ? "" : "e"}`;
  byId("calendarAgenda").innerHTML = appointments.length ? appointments.map((item) => {
    const color = legend.get(item.color_id);
    return `<article class="item-card appointment-card" style="--appointment-color:${safeHex(color?.color)}">
      <header><div><strong>${escapeHtml(item.title)}</strong><div class="item-meta"><span>${formatDate(item.date)}</span><span>${escapeHtml(formatAppointmentTime(item))}</span>${item.location ? `<span>${escapeHtml(item.location)}</span>` : ""}${color ? `<span>${escapeHtml(color.title)}</span>` : ""}</div></div>
      <div class="actions"><button class="button small secondary" type="button" data-appointment-edit="${escapeHtml(item.id)}">Bearbeiten</button><button class="button small danger" type="button" data-appointment-delete="${escapeHtml(item.id)}">Löschen</button></div></header>
      ${item.notes ? `<p>${escapeHtml(item.notes)}</p>` : ""}
      ${item.reminder_at ? `<small>Erinnerung: ${formatDateTime(item.reminder_at)}</small>` : ""}
    </article>`;
  }).join("") : '<span class="empty-state">Keine Termine im gewählten Zeitraum.</span>';
}

function calendarDayMarkup(dateValue, day, marker, appointments, tasks, { compact = false } = {}) {
  const today = new Date().toISOString().slice(0, 10);
  const colors = asArray(marker?.colors);
  const gradient = markerGradient(colors);
  const visibleTasks = tasks.filter((item) => byId("calendarShowCompleted", false)?.checked !== false || item.status !== "erledigt");
  const colorInfo = colors.map((item) => `<span class="calendar-color-info" style="--item-color:${safeHex(item.color)}" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</span>`).join("");
  const showReminders = byId("calendarShowReminders", false)?.checked !== false;
  const appointmentInfo = appointments.slice(0, compact ? 1 : 3).map((item) => `<button class="calendar-appointment" type="button" data-appointment-edit="${escapeHtml(item.id)}" title="${escapeHtml(`${item.title} · ${formatAppointmentTime(item)}`)}"><span>${showReminders && item.reminder_at ? "🔔" : escapeHtml(item.start_time || (item.all_day ? "Tag" : "•"))}</span>${escapeHtml(item.title)}</button>`).join("");
  const taskInfo = compact ? "" : visibleTasks.slice(0, 3).map((item) => `<span class="calendar-event ${item.status === "erledigt" ? "done" : ""}">${escapeHtml(item.icon || "•")} ${escapeHtml(item.title)}</span>`).join("");
  const more = Math.max(0, appointments.length - (compact ? 1 : 3)) + Math.max(0, visibleTasks.length - (compact ? 0 : 3));
  return `<div class="calendar-day ${dateValue === today ? "today" : ""} ${colors.length ? "marked" : ""}" style="--day-gradient:${gradient}">
    <button class="calendar-date-button" type="button" data-calendar-date="${dateValue}" aria-label="${formatDate(dateValue, { weekday: "long", day: "numeric", month: "long" })}">${day}</button>
    ${compact ? "" : `<div class="calendar-color-summary">${colorInfo}</div>`}
    <div class="calendar-day-content">${appointmentInfo}${taskInfo}${more ? `<span class="calendar-more">+${more} weitere</span>` : ""}</div>
  </div>`;
}

function renderHeaderMiniCalendar() {
  const reference = state.miniCalendarDate || state.calendar.reference_date || new Date().toISOString().slice(0, 10);
  const month = monthKey(reference);
  const [year, monthNumber] = month.split("-").map(Number);
  byId("miniCalendarTitle").textContent = new Intl.DateTimeFormat("de-DE", { month: "long", year: "numeric" }).format(new Date(year, monthNumber - 1, 1));
  const markers = calendarMarkerMap();
  const appointments = calendarAppointmentMap();
  const tasks = calendarTaskMap();
  const firstDay = new Date(year, monthNumber - 1, 1).getDay();
  const offset = firstDay === 0 ? 6 : firstDay - 1;
  const cells = Array.from({ length: offset }, () => '<span class="mini-calendar-empty"></span>');
  for (let day = 1; day <= daysInMonth(month); day += 1) {
    const dateValue = `${month}-${String(day).padStart(2, "0")}`;
    const marker = markers.get(dateValue);
    const colors = asArray(marker?.colors).slice(0, 4);
    const hasItems = asArray(appointments.get(dateValue)).length || asArray(tasks.get(dateValue)).length;
    const dots = colors.map((item) => `<i style="--mini-color:${safeHex(item.color)}"></i>`).join("");
    cells.push(`<button class="mini-calendar-day ${dateValue === new Date().toISOString().slice(0, 10) ? "today" : ""}" type="button" data-mini-date="${dateValue}" title="${escapeHtml(marker?.summary || "")}"><span>${day}</span><small>${dots}${hasItems ? "<b></b>" : ""}</small></button>`);
  }
  byId("headerMiniCalendar").innerHTML = cells.join("");
}

function renderCalendar() {
  const view = byId("calendarView").value;
  const reference = byId("calendarDate").value || state.calendar.reference_date || new Date().toISOString().slice(0, 10);
  const entries = asArray(state.calendar.entries);
  const appointments = calendarAppointmentMap();
  const tasks = calendarTaskMap();
  const markers = calendarMarkerMap();
  const range = asObject(state.calendar.range);
  byId("calendarRangeLabel").textContent = range.start && range.end ? `${formatDate(range.start)} bis ${formatDate(range.end)}` : "Zeitraum wird geladen.";
  renderCalendarLegendControls();
  renderCalendarAgenda();
  renderCalendarReminders();
  renderHeaderMiniCalendar();

  if (view !== "monat") {
    const combined = [
      ...entries.map((item) => ({ date: item.date, title: item.title, meta: item.status, icon: item.icon || "•" })),
      ...asArray(state.calendar.appointments).map((item) => ({ date: item.date, title: item.title, meta: formatAppointmentTime(item), icon: "◆" })),
    ].sort((a, b) => `${a.date} ${a.title}`.localeCompare(`${b.date} ${b.title}`));
    byId("calendarGrid").className = "calendar-grid calendar-list-view";
    byId("calendarGrid").innerHTML = combined.length ? combined.map((item) => `<article class="item-card"><strong>${formatDate(item.date)}</strong><span>${escapeHtml(item.icon)} ${escapeHtml(item.title)}</span><small>${escapeHtml(item.meta || "")}</small></article>`).join("") : '<span class="empty-state">Keine Kalendereinträge vorhanden.</span>';
    return;
  }

  const month = monthKey(reference);
  const [year, monthNumber] = month.split("-").map(Number);
  const showWeekends = byId("calendarShowWeekends").checked;
  const firstDay = new Date(year, monthNumber - 1, 1).getDay();
  let offset = firstDay === 0 ? 6 : firstDay - 1;
  if (!showWeekends) offset = Math.min(offset, 5);
  const cells = Array.from({ length: offset }, () => '<span class="calendar-empty-cell" aria-hidden="true"></span>');
  for (let day = 1; day <= daysInMonth(month); day += 1) {
    const dateValue = `${month}-${String(day).padStart(2, "0")}`;
    const weekday = new Date(`${dateValue}T12:00:00`).getDay();
    if (!showWeekends && (weekday === 0 || weekday === 6)) continue;
    cells.push(calendarDayMarkup(dateValue, day, markers.get(dateValue), asArray(appointments.get(dateValue)), asArray(tasks.get(dateValue))));
  }
  const grid = byId("calendarGrid");
  grid.className = `calendar-grid ${showWeekends ? "seven-days" : "five-days"}`;
  grid.innerHTML = cells.join("");
  const weekdays = $(".calendar-weekdays");
  if (weekdays) weekdays.classList.toggle("five-days", !showWeekends);
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
    const tasks = state.todos.filter((item) => item.status !== "erledigt").map((item) => ({ date: item.planned_date, title: item.title, type: "Aufgabe" }));
    const appointments = asArray(state.calendar.appointments).map((item) => ({ date: item.date, title: item.title, type: item.start_time || "Termin" }));
    const items = [...tasks, ...appointments].filter((item) => item.date >= new Date().toISOString().slice(0, 10)).sort((a, b) => String(a.date).localeCompare(String(b.date))).slice(0, 5);
    upcoming.innerHTML = items.length ? items.map((item) => `<div class="footer-event"><time>${formatDate(item.date)}</time><span>${escapeHtml(item.title)} · ${escapeHtml(item.type)}</span></div>`).join("") : "Keine anstehenden Aufgaben oder Termine.";
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

async function loadCalendar({ announce = true } = {}) {
  const view = byId("calendarView").value;
  const reference = byId("calendarDate").value || new Date().toISOString().slice(0, 10);
  try {
    state.calendar = await api(`/api/calendar?view=${encodeURIComponent(view)}&reference_date=${encodeURIComponent(reference)}`);
    state.miniCalendarDate = reference;
    renderCalendar();
    if (announce) addEvent(`Kalenderansicht geladen: ${view}`);
  } catch (error) {
    reportError(error, { context: "Kalender laden" });
  }
}

async function loadReminders() {
  try {
    state.calendar.reminders = await api("/api/calendar/reminders?horizon_hours=168");
    renderCalendarReminders();
    renderFooter();
  } catch (error) {
    reportError(error, { context: "Erinnerungen laden" });
  }
}

async function shiftCalendar(direction) {
  const view = byId("calendarView").value;
  const current = byId("calendarDate").value || new Date().toISOString().slice(0, 10);
  const shifted = view === "monat" ? addMonths(current, direction) : addDays(current, direction * (view === "woche" ? 7 : 365));
  byId("calendarDate").value = shifted;
  state.miniCalendarDate = shifted;
  await loadCalendar();
}

function selectCalendarDate(dateValue) {
  byId("calendarDate").value = dateValue;
  byId("dayColorDate").value = dateValue;
  byId("appointmentDate").value = dateValue;
  const marker = calendarMarkerMap().get(dateValue);
  const selected = new Set(asArray(marker?.color_ids));
  $$("#dayColorOptions input[name='dayColor']").forEach((input) => { input.checked = selected.has(input.value); });
}

function resetAppointmentForm(dateValue = "") {
  const form = byId("appointmentForm");
  form.reset();
  byId("appointmentId").value = "";
  byId("appointmentFormTitle").textContent = "Neuer Termin";
  byId("appointmentReset").hidden = true;
  byId("appointmentDate").value = dateValue || byId("calendarDate").value || new Date().toISOString().slice(0, 10);
  byId("appointmentReminder").value = "-1";
  byId("appointmentTimeRow").hidden = false;
}

function editAppointment(appointmentId) {
  const item = asArray(state.calendar.appointments).find((entry) => entry.id === appointmentId);
  if (!item) throw new Error("Termin wurde nicht gefunden.");
  byId("appointmentId").value = item.id;
  byId("appointmentFormTitle").textContent = "Termin bearbeiten";
  byId("appointmentReset").hidden = false;
  byId("appointmentTitle").value = item.title || "";
  byId("appointmentDate").value = item.date || "";
  byId("appointmentAllDay").checked = Boolean(item.all_day);
  byId("appointmentStart").value = item.start_time || "";
  byId("appointmentEnd").value = item.end_time || "";
  byId("appointmentLocation").value = item.location || "";
  byId("appointmentColor").value = item.color_id || "";
  byId("appointmentReminder").value = item.reminder_minutes == null ? "-1" : String(item.reminder_minutes);
  byId("appointmentNotes").value = item.notes || "";
  byId("appointmentTimeRow").hidden = Boolean(item.all_day);
  navigate("calendar");
  byId("appointmentTitle").focus();
}

async function enableNotifications() {
  if (typeof Notification === "undefined") {
    showToast("Browser-Benachrichtigungen werden nicht unterstützt.", true);
    return;
  }
  const permission = await Notification.requestPermission();
  showToast(permission === "granted" ? "Browser-Erinnerungen sind aktiviert." : "Browser-Erinnerungen wurden nicht aktiviert.", permission !== "granted");
  if (permission === "granted") renderCalendarReminders();
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
    } else if (form.id === "appointmentForm") {
      const appointmentId = byId("appointmentId").value;
      const payload = {
        title: byId("appointmentTitle").value.trim(),
        date: byId("appointmentDate").value,
        all_day: byId("appointmentAllDay").checked,
        start_time: byId("appointmentStart").value || null,
        end_time: byId("appointmentEnd").value || null,
        location: byId("appointmentLocation").value.trim(),
        notes: byId("appointmentNotes").value.trim(),
        color_id: byId("appointmentColor").value || null,
        reminder_minutes: Number(byId("appointmentReminder").value),
      };
      const path = appointmentId ? `/api/calendar/appointments/${encodeURIComponent(appointmentId)}` : "/api/calendar/appointments";
      await api(path, { method: appointmentId ? "PUT" : "POST", body: JSON.stringify(payload) });
      pulse("saveLight");
      showToast(appointmentId ? "Termin aktualisiert." : "Termin gespeichert.");
      resetAppointmentForm(payload.date);
      byId("calendarDate").value = payload.date;
      await loadCalendar({ announce: false });
    } else if (form.id === "dayColorForm") {
      const selected = $$("#dayColorOptions input[name='dayColor']:checked").map((input) => input.value);
      if (selected.length > 4) throw new Error("Pro Tag sind höchstens vier Farben möglich.");
      const dateValue = byId("dayColorDate").value;
      await api("/api/calendar/day-colors", { method: "PUT", body: JSON.stringify({ date: dateValue, color_ids: selected }) });
      pulse("saveLight");
      showToast("Tagesfarben gespeichert.");
      byId("calendarDate").value = dateValue;
      await loadCalendar({ announce: false });
    } else if (form.id === "calendarLegendForm") {
      const rows = $$("#calendarLegendEditor .legend-editor-row");
      const legend = rows.map((row) => ({
        id: $("[data-legend-id]", row).value,
        title: $("[data-legend-title]", row).value.trim(),
        color: $("[data-legend-color]", row).value,
      }));
      await api("/api/calendar/legend", { method: "PUT", body: JSON.stringify({ legend }) });
      pulse("saveLight");
      showToast("Farblegende gespeichert.");
      await loadCalendar({ announce: false });
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
    else if (action === "calendar-prev") await shiftCalendar(-1);
    else if (action === "calendar-next") await shiftCalendar(1);
    else if (action === "calendar-today") {
      const today = new Date().toISOString().slice(0, 10);
      byId("calendarDate").value = today;
      state.miniCalendarDate = today;
      await loadCalendar();
    }
    else if (action === "mini-calendar-prev") {
      const shifted = addMonths(state.miniCalendarDate, -1);
      state.miniCalendarDate = shifted;
      byId("calendarDate").value = shifted;
      await loadCalendar({ announce: false });
    }
    else if (action === "mini-calendar-next") {
      const shifted = addMonths(state.miniCalendarDate, 1);
      state.miniCalendarDate = shifted;
      byId("calendarDate").value = shifted;
      await loadCalendar({ announce: false });
    }
    else if (action === "enable-notifications") await enableNotifications();
    else if (action === "reset-appointment") resetAppointmentForm();
    else if (action === "load-files" || action === "refresh-files") await loadFiles();
    else if (action === "file-parent" && state.files.parent) await loadFiles(state.files.parent);
    else if (action === "clear-output") byId("systemOutput").textContent = "Noch keine Systemaktion ausgeführt.";
    else if (action === "close-action-dialog") closeModuleAction();
    else if (action === "reload-page") window.location.reload();
    return;
  }
  const miniDateButton = event.target.closest("[data-mini-date]");
  if (miniDateButton) {
    const dateValue = miniDateButton.dataset.miniDate;
    state.miniCalendarDate = dateValue;
    byId("calendarDate").value = dateValue;
    selectCalendarDate(dateValue);
    navigate("calendar");
    await loadCalendar({ announce: false });
    return;
  }
  const calendarDateButton = event.target.closest("[data-calendar-date]");
  if (calendarDateButton) {
    selectCalendarDate(calendarDateButton.dataset.calendarDate);
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
  const appointmentEdit = event.target.closest("[data-appointment-edit]");
  if (appointmentEdit) { editAppointment(appointmentEdit.dataset.appointmentEdit); return; }
  const appointmentDelete = event.target.closest("[data-appointment-delete]");
  if (appointmentDelete && window.confirm("Termin wirklich löschen?")) {
    await api(`/api/calendar/appointments/${encodeURIComponent(appointmentDelete.dataset.appointmentDelete)}`, { method: "DELETE" });
    pulse("saveLight");
    showToast("Termin gelöscht.");
    resetAppointmentForm();
    await loadCalendar({ announce: false });
    return;
  }
  const reminderAck = event.target.closest("[data-reminder-ack]");
  if (reminderAck) {
    await api(`/api/calendar/reminders/${encodeURIComponent(reminderAck.dataset.reminderAck)}/acknowledge`, { method: "POST", body: "{}" });
    pulse("saveLight");
    state.notifiedReminderIds.delete(reminderAck.dataset.reminderAck);
    await loadReminders();
    return;
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
  else if (["calendarShowWeekends", "calendarShowCompleted", "calendarShowReminders"].includes(event.target.id)) {
    try {
      localStorage.setItem("provoware_calendar_options", JSON.stringify({
        weekends: byId("calendarShowWeekends").checked,
        completed: byId("calendarShowCompleted").checked,
        reminders: byId("calendarShowReminders").checked,
      }));
    } catch (_error) { /* optional */ }
    renderCalendar();
  }
  else if (event.target.id === "appointmentAllDay") {
    byId("appointmentTimeRow").hidden = event.target.checked;
    if (event.target.checked) { byId("appointmentStart").value = ""; byId("appointmentEnd").value = ""; }
  }
  else if (event.target.matches("#dayColorOptions input[name='dayColor']")) {
    const selected = $$("#dayColorOptions input[name='dayColor']:checked");
    if (selected.length > 4) {
      event.target.checked = false;
      showToast("Pro Tag können höchstens vier Farben gewählt werden.", true);
    }
  }
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
    byId("appointmentDate").value = today;
    byId("dayColorDate").value = today;
    state.miniCalendarDate = today;
    try {
      const options = JSON.parse(localStorage.getItem("provoware_calendar_options") || "{}");
      if (typeof options.weekends === "boolean") byId("calendarShowWeekends").checked = options.weekends;
      if (typeof options.completed === "boolean") byId("calendarShowCompleted").checked = options.completed;
      if (typeof options.reminders === "boolean") byId("calendarShowReminders").checked = options.reminders;
    } catch (_error) { /* optional */ }
    updateClock();
    window.setInterval(updateClock, 1000);
    const initialView = (() => {
      try { return localStorage.getItem("provoware_memo_active_view") || "dashboard"; }
      catch (_error) { return "dashboard"; }
    })();
    navigate($(`[data-panel="${CSS.escape(initialView)}"]`) ? initialView : "dashboard", { focus: false });
    document.documentElement.dataset.appReady = "binding";
    await loadAll();
    resetAppointmentForm(today);
    selectCalendarDate(today);
    await loadFiles("");
    const reminderSeconds = Math.max(15, Number(state.calendar.options?.reminder_poll_seconds || 60));
    window.setInterval(() => loadReminders(), reminderSeconds * 1000);
    document.documentElement.dataset.appReady = "true";
    addEvent("Provoware Memo ist vollständig bedienbar.", "success");
  } catch (error) {
    document.documentElement.dataset.appReady = "error";
    reportError(error, { fatal: true, context: "Initialisierung" });
  }
}

document.addEventListener("DOMContentLoaded", init, { once: true });
