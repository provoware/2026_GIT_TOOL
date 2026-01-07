const LOG_LEVELS = ["info", "warn", "error"];

const nowIso = () => new Date().toISOString();

const makeId = () => {
  const c = typeof globalThis !== "undefined" ? globalThis.crypto : null;
  if (c && typeof c.randomUUID === "function") return c.randomUUID();
  return Math.random().toString(16).slice(2) + "_" + Date.now().toString(16);
};

const normalizeText = (value, fallback) => {
  if (typeof value !== "string") return fallback;
  const trimmed = value.trim();
  return trimmed ? trimmed : fallback;
};

const normalizeLevel = (level) => {
  const candidate = normalizeText(level, "info").toLowerCase();
  return LOG_LEVELS.includes(candidate) ? candidate : "info";
};

const normalizeMeta = (meta) => {
  if (!meta || typeof meta !== "object" || Array.isArray(meta)) return {};
  return meta;
};

const formatLogLine = (entry) => {
  if (!entry) return "";
  const at = normalizeText(entry.at, nowIso());
  const module = normalizeText(entry.module, "system");
  const level = normalizeLevel(entry.level).toUpperCase();
  const message = normalizeText(entry.message, "Ohne Nachricht");
  return `${at} | ${module} | ${level} | ${message}`;
};

const createLogEntry = ({ module, level, message, meta, at, id } = {}) => {
  const entry = {
    id: normalizeText(id, makeId()),
    at: normalizeText(at, nowIso()),
    module: normalizeText(module, "system"),
    level: normalizeLevel(level),
    message: normalizeText(message, "Ohne Nachricht"),
    meta: normalizeMeta(meta),
  };
  entry.line = formatLogLine(entry);
  return entry;
};

const normalizeLogEntry = (raw) => {
  const module = raw?.module ?? raw?.type ?? "system";
  const level = raw?.level ?? (raw?.type === "error" ? "error" : "info");
  return createLogEntry({
    id: raw?.id,
    at: raw?.at,
    module,
    level,
    message: raw?.message,
    meta: raw?.meta,
  });
};

export { LOG_LEVELS, createLogEntry, formatLogLine, normalizeLogEntry };
