const DEFAULT_SCALE = 1.0;

const nowIso = () => new Date().toISOString();
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const norm = (s) => (s ?? "").trim().replace(/\s+/g, " ");
const normKey = (s) => norm(s).toLowerCase();

function safeJsonParse(text) {
  try {
    return { ok: true, value: JSON.parse(text) };
  } catch (e) {
    return { ok: false, error: e };
  }
}

function makeId() {
  const c = typeof globalThis !== "undefined" ? globalThis.crypto : null;
  if (c && typeof c.randomUUID === "function") return c.randomUUID();
  return Math.random().toString(16).slice(2) + "_" + Date.now().toString(16);
}

function makeDefaultState() {
  const createdAt = nowIso();
  return {
    version: 1,
    updatedAt: createdAt,
    settings: {
      activeProfile: "Standard",
      favoritesOnly: false,
      themeId: "nebula",
      uiScale: DEFAULT_SCALE,
      generator: {
        mode: "mix",
        count: 12,
        perType: { genre: 6, mood: 4, style: 6 },
        range: { min: 8, max: 24 },
        delimiter: ", ",
        showTypeLabels: false,
        includeTypes: { genre: true, mood: true, style: true },
      },
      autosaveMinutes: 10,
      maxLogs: 500,
    },
    profiles: {
      Standard: {
        createdAt,
        updatedAt: createdAt,
        items: [],
      },
    },
    logs: [],
    stats: {
      generatorRuns: 0,
      lastRunAt: null,
      lastRunMode: null,
      lastRunCount: 0,
      totalGeneratedTokens: 0,
      duplicatesIgnored: 0,
      itemsAdded: 0,
      exports: 0,
      imports: 0,
      lastExportAt: null,
      lastImportAt: null,
    },
  };
}

function normalizeItem(raw, fallbackType = "genre") {
  const type = ["genre", "mood", "style"].includes(raw?.type) ? raw.type : fallbackType;
  const value = norm(raw?.value ?? raw?.key ?? "");
  const key = normKey(raw?.key ? raw.key : value);
  const createdAt = typeof raw?.createdAt === "string" && raw.createdAt ? raw.createdAt : nowIso();
  const updatedAt = typeof raw?.updatedAt === "string" && raw.updatedAt ? raw.updatedAt : createdAt;
  return {
    id: typeof raw?.id === "string" && raw.id ? raw.id : makeId(),
    type,
    value,
    key,
    favorite: !!raw?.favorite,
    createdAt,
    updatedAt,
  };
}

function coerceState(maybe) {
  const fallback = makeDefaultState();
  if (!maybe || typeof maybe !== "object") return fallback;

  const state = { ...fallback, ...maybe };
  state.settings = { ...fallback.settings, ...(maybe.settings || {}) };
  state.settings.generator = { ...fallback.settings.generator, ...((maybe.settings || {}).generator || {}) };
  state.settings.generator.perType = { ...fallback.settings.generator.perType, ...(((maybe.settings || {}).generator || {}).perType || {}) };
  state.settings.generator.range = { ...fallback.settings.generator.range, ...(((maybe.settings || {}).generator || {}).range || {}) };
  state.settings.generator.includeTypes = { ...fallback.settings.generator.includeTypes, ...(((maybe.settings || {}).generator || {}).includeTypes || {}) };

  state.profiles = { ...(maybe.profiles || fallback.profiles) };
  for (const [p, v] of Object.entries(state.profiles)) {
    const items = Array.isArray(v?.items) ? v.items : [];
    state.profiles[p] = {
      createdAt: v?.createdAt || state.updatedAt || nowIso(),
      updatedAt: v?.updatedAt || state.updatedAt || nowIso(),
      items: items.map((it) => normalizeItem(it, it?.type)).filter((it) => it.key && it.value),
    };
  }

  state.logs = Array.isArray(maybe.logs) ? maybe.logs : [];
  state.stats = { ...fallback.stats, ...(maybe.stats || {}) };
  state.version = 1;
  state.updatedAt = maybe.updatedAt || nowIso();

  if (!state.settings.activeProfile || !state.profiles?.[state.settings.activeProfile]) {
    const p = Object.keys(state.profiles || {}).sort((a, b) => a.localeCompare(b))[0];
    state.settings.activeProfile = p || "Standard";
  }
  if (typeof state.settings.uiScale !== "number") state.settings.uiScale = DEFAULT_SCALE;

  return state;
}

function validateState(st) {
  const errors = [];
  if (!st || typeof st !== "object") errors.push("State ist kein Objekt.");
  if (!st?.profiles || typeof st.profiles !== "object") errors.push("profiles fehlt oder ist ungültig.");
  if (!st?.settings || typeof st.settings !== "object") errors.push("settings fehlt oder ist ungültig.");
  if (st?.profiles) {
    for (const [pname, p] of Object.entries(st.profiles)) {
      if (!p || typeof p !== "object") errors.push(`Profil ${pname} ist ungültig.`);
      if (!Array.isArray(p?.items)) errors.push(`Profil ${pname}.items ist nicht Array.`);
      if (Array.isArray(p?.items)) {
        for (const it of p.items) {
          if (!it?.id) errors.push(`Profil ${pname}: item ohne id`);
          if (!["genre", "mood", "style"].includes(it?.type)) errors.push(`Profil ${pname}: item mit ungültigem type`);
          if (!it?.value || !it?.key) errors.push(`Profil ${pname}: item mit leerem value/key`);
        }
      }
    }
  }
  if (!st?.settings?.activeProfile || !st?.profiles?.[st.settings.activeProfile]) errors.push("activeProfile fehlt oder existiert nicht.");
  return { ok: errors.length === 0, errors };
}

function initStateFromStorage(raw) {
  if (!raw) return makeDefaultState();
  const parsed = safeJsonParse(raw);
  return parsed.ok ? coerceState(parsed.value) : makeDefaultState();
}

export {
  DEFAULT_SCALE,
  clamp,
  coerceState,
  initStateFromStorage,
  makeDefaultState,
  makeId,
  normalizeItem,
  norm,
  normKey,
  nowIso,
  safeJsonParse,
  validateState,
};
