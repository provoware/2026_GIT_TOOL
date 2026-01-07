import { describe, expect, it } from "vitest";

import { initStateFromStorage, makeDefaultState, validateState } from "../state";

describe("State-Start und Validierung", () => {
  it("nutzt den Standardzustand bei leerem oder kaputtem Speicher", () => {
    const empty = initStateFromStorage(null);
    const invalid = initStateFromStorage("{");

    expect(empty.settings.activeProfile).toBe("Standard");
    expect(invalid.settings.activeProfile).toBe("Standard");
  });

  it("lädt gültige Daten aus dem Speicher", () => {
    const stored = JSON.stringify(makeDefaultState());
    const restored = initStateFromStorage(stored);

    expect(restored.settings.activeProfile).toBe("Standard");
    expect(Object.keys(restored.profiles)).toContain("Standard");
  });

  it("meldet erwartete Fehler bei ungültigen Daten", () => {
    const result = validateState({});

    expect(result.ok).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });
});
