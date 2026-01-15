const MODULE_INTERFACE = [
  { key: "id", type: "string", label: "Modul-ID" },
  { key: "label", type: "string", label: "Modulname" },
  { key: "init", type: "function", label: "Start-Funktion" },
];

const normalizeString = (value) => (typeof value === "string" ? value.trim() : "");

const makeResult = ({ id, label, ok, severity, message, meta = {} }) => ({
  id,
  label,
  ok,
  severity,
  message,
  meta,
});

const summarize = (results) => {
  const summary = { ok: 0, warn: 0, error: 0 };
  for (const r of results) {
    if (r.severity === "error") summary.error += 1;
    else if (r.severity === "warn") summary.warn += 1;
    else summary.ok += 1;
  }
  return summary;
};

export const buildModuleRegistry = (definitions) => {
  if (!Array.isArray(definitions)) return [];
  return definitions
    .filter((def) => def && typeof def === "object")
    .map((def) => ({
      ...def,
      init: () => ({ ok: true, message: "Modul bereit" }),
    }));
};

const validateModuleInterface = (module) => {
  const errors = [];
  if (!module || typeof module !== "object") {
    return ["Modul ist kein Objekt."];
  }
  for (const field of MODULE_INTERFACE) {
    const value = module[field.key];
    if (field.type === "string") {
      if (!normalizeString(value)) errors.push(`${field.label} fehlt.`);
    } else if (field.type === "function") {
      if (typeof value !== "function") errors.push(`${field.label} fehlt.`);
    }
  }
  return errors;
};

const checkStorage = (storage) => {
  if (!storage || typeof storage !== "object") {
    return { ok: false, message: "Lokaler Speicher (Local Storage) ist nicht verfügbar." };
  }
  const { get, set, remove } = storage;
  if (typeof get !== "function" || typeof set !== "function" || typeof remove !== "function") {
    return { ok: false, message: "Lokaler Speicher (Local Storage) kann nicht genutzt werden." };
  }
  const testKey = "__gms_start_check__";
  const setOk = set(testKey, "1");
  const getOk = get(testKey) === "1";
  const removeOk = remove(testKey);
  if (!setOk || !getOk || !removeOk) {
    return { ok: false, message: "Lokaler Speicher (Local Storage) blockiert oder voll." };
  }
  return { ok: true, message: "Lokaler Speicher (Local Storage) verfügbar." };
};

const checkStateShape = (state) => {
  if (!state || typeof state !== "object") {
    return { ok: false, message: "Basisdaten fehlen oder sind ungültig." };
  }
  if (!state.profiles || typeof state.profiles !== "object") {
    return { ok: false, message: "Profile fehlen oder sind ungültig." };
  }
  if (!state.settings || typeof state.settings !== "object") {
    return { ok: false, message: "Einstellungen fehlen oder sind ungültig." };
  }
  return { ok: true, message: "Basisdaten vorhanden." };
};

const checkPersistedData = (persistedSnapshot) => {
  if (!persistedSnapshot) {
    return {
      ok: true,
      severity: "warn",
      message: "Keine gespeicherten Daten gefunden. Es wird mit Standardwerten gestartet.",
    };
  }
  return { ok: true, severity: "ok", message: "Gespeicherte Daten gefunden." };
};

export const runStartupChecks = ({ state, modules, storage, persistedSnapshot }) => {
  const results = [];

  const storageResult = checkStorage(storage);
  results.push(
    makeResult({
      id: "storage",
      label: "Lokaler Speicher",
      ok: storageResult.ok,
      severity: storageResult.ok ? "ok" : "error",
      message: storageResult.message,
    }),
  );

  const stateResult = checkStateShape(state);
  results.push(
    makeResult({
      id: "state",
      label: "Basisdaten",
      ok: stateResult.ok,
      severity: stateResult.ok ? "ok" : "error",
      message: stateResult.message,
    }),
  );

  const persistedResult = checkPersistedData(persistedSnapshot);
  results.push(
    makeResult({
      id: "persisted",
      label: "Gespeicherte Daten",
      ok: persistedResult.ok,
      severity: persistedResult.severity,
      message: persistedResult.message,
    }),
  );

  const modulesArray = Array.isArray(modules) ? modules : [];
  if (!modulesArray.length) {
    results.push(
      makeResult({
        id: "modules",
        label: "Module",
        ok: false,
        severity: "error",
        message: "Keine Module gefunden. Bitte Konfiguration prüfen.",
      }),
    );
  } else {
    for (const mod of modulesArray) {
      const errors = validateModuleInterface(mod);
      const ok = errors.length === 0;
      results.push(
        makeResult({
          id: `module-${mod?.id || "unbekannt"}`,
          label: `Modul: ${mod?.label || "Unbekannt"}`,
          ok,
          severity: ok ? "ok" : "error",
          message: ok ? "Schnittstelle ist korrekt." : `Schnittstelle fehlerhaft: ${errors.join(" ")}`,
          meta: { moduleId: mod?.id || null },
        }),
      );
    }
  }

  const summary = summarize(results);
  const ok = summary.error === 0;
  return { ok, results, summary };
};
