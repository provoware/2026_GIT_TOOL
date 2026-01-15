export function buildSelfTestReport({
  state,
  profiles,
  allItems,
  storageAvailable,
  validateState,
  coerceState,
  safeJsonParse,
  nowIso,
  simulateFailure = false,
}) {
  const results = [];
  const pushResult = (id, label, run, hint) => {
    let ok = false;
    let details = "";
    try {
      const res = run();
      ok = !!res.ok;
      details = res.details || "";
    } catch (error) {
      ok = false;
      details = `Fehler: ${String(error)}`;
    }
    results.push({ id, label, ok, details, hint });
  };

  pushResult(
    "state-structure",
    "State-Struktur prüfen",
    () => {
      const validation = validateState(state);
      return {
        ok: validation.ok,
        details: validation.ok ? "OK" : validation.errors.join(" "),
      };
    },
    "Prüft, ob die Datenstruktur vollständig und konsistent ist."
  );

  pushResult(
    "roundtrip",
    "Export-Import-Roundtrip",
    () => {
      const payload = JSON.stringify({ ...state, exportedAt: nowIso() });
      const parsed = safeJsonParse(payload);
      if (!parsed.ok) return { ok: false, details: "JSON konnte nicht gelesen werden." };
      const validation = validateState(coerceState(parsed.value));
      return {
        ok: validation.ok,
        details: validation.ok ? "OK" : validation.errors.join(" "),
      };
    },
    "Prüft, ob Export und erneutes Einlesen fehlerfrei funktionieren."
  );

  pushResult(
    "storage",
    "LocalStorage verfügbar",
    () => ({
      ok: storageAvailable,
      details: storageAvailable ? "OK" : "LocalStorage ist blockiert.",
    }),
    "Wichtig für Speichern und Autosave."
  );

  pushResult(
    "profiles",
    "Profile vorhanden",
    () => ({
      ok: Array.isArray(profiles) && profiles.length > 0,
      details: Array.isArray(profiles) && profiles.length > 0 ? `OK (${profiles.length})` : "Keine Profile gefunden.",
    }),
    "Mindestens ein Profil sollte existieren."
  );

  pushResult(
    "items",
    "Einträge lesbar",
    () => {
      const ok = Array.isArray(allItems) && allItems.every((it) => it?.id && it?.type && it?.value);
      return {
        ok,
        details: ok ? `OK (${allItems.length})` : "Mindestens ein Eintrag ist fehlerhaft.",
      };
    },
    "Prüft, ob Einträge eine ID, Typ und Wert besitzen."
  );

  if (simulateFailure) {
    results.push({
      id: "simulated-failure",
      label: "Simulierter Fehler",
      ok: false,
      details: "Absichtlich rot zum Testen der Anzeige.",
      hint: "Nur für Diagnosezwecke nutzen.",
    });
  }

  const failed = results.filter((r) => !r.ok).length;
  const summary = failed === 0 ? "Alle Tests bestanden." : `${failed} Test(s) fehlgeschlagen.`;

  return {
    ok: failed === 0,
    results,
    summary,
    ranAt: nowIso(),
  };
}
