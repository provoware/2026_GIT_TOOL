const isPlainObject = (value) => !!value && typeof value === "object" && !Array.isArray(value);

const normalizeMessage = (message, fallback) => {
  if (typeof message === "string" && message.trim()) return message.trim();
  return fallback;
};

const buildFailure = ({ step, index, total, progress, message, hint, detail }) => ({
  ok: false,
  stepId: step?.id ?? "unbekannt",
  stepLabel: step?.label ?? "Unbekannter Schritt",
  index,
  total,
  progress,
  message: normalizeMessage(message, "Schritt fehlgeschlagen."),
  hint: normalizeMessage(hint, "Bitte prüfen Sie die Umgebung und starten Sie erneut."),
  detail: normalizeMessage(detail, ""),
});

const normalizeStepResult = ({ step, result, index, total, progress }) => {
  if (!isPlainObject(result) || typeof result.ok !== "boolean") {
    return buildFailure({
      step,
      index,
      total,
      progress,
      message: "Schritt lieferte kein gültiges Ergebnis.",
      hint: "Bitte Anwendung neu starten (Reload).",
      detail: "Das Ergebnis muss ein Objekt mit ok=true/false sein.",
    });
  }
  return {
    ok: result.ok,
    stepId: step.id,
    stepLabel: step.label,
    index,
    total,
    progress,
    message: normalizeMessage(result.message, result.ok ? "Schritt erfolgreich." : "Schritt fehlgeschlagen."),
    hint: normalizeMessage(result.hint, ""),
    detail: normalizeMessage(result.detail, ""),
  };
};

const validateCallbacks = ({ onProgress, onError, onDone }) => {
  const errors = [];
  if (onProgress && typeof onProgress !== "function") errors.push("onProgress ist keine Funktion.");
  if (onError && typeof onError !== "function") errors.push("onError ist keine Funktion.");
  if (onDone && typeof onDone !== "function") errors.push("onDone ist keine Funktion.");
  return errors;
};

const validateSteps = (steps) => {
  if (!Array.isArray(steps) || steps.length === 0) {
    return ["Es wurden keine Startschritte angegeben."];
  }
  const errors = [];
  steps.forEach((step, index) => {
    if (!isPlainObject(step)) errors.push(`Schritt ${index + 1} ist kein Objekt.`);
    if (!step?.id || typeof step.id !== "string") errors.push(`Schritt ${index + 1} hat keine id.`);
    if (!step?.label || typeof step.label !== "string") errors.push(`Schritt ${index + 1} hat kein label.`);
    if (typeof step?.run !== "function") errors.push(`Schritt ${index + 1} hat keine run-Funktion.`);
  });
  return errors;
};

export async function runStartupSequence({ steps, onProgress, onError, onDone, context }) {
  const callbackErrors = validateCallbacks({ onProgress, onError, onDone });
  const stepErrors = validateSteps(steps);
  const inputErrors = [...callbackErrors, ...stepErrors];

  if (inputErrors.length > 0) {
    const error = buildFailure({
      step: { id: "eingabe", label: "Eingaben prüfen" },
      index: 0,
      total: Array.isArray(steps) ? steps.length : 0,
      progress: 0,
      message: "Startschritte sind ungültig.",
      hint: "Bitte wenden Sie sich an die Administration.",
      detail: inputErrors.join(" "),
    });
    if (typeof onError === "function") onError(error);
    return { ok: false, error };
  }

  const total = steps.length;
  for (let index = 0; index < total; index += 1) {
    const step = steps[index];
    const startProgress = Math.round((index / total) * 100);
    if (typeof onProgress === "function") {
      onProgress({
        stage: "start",
        stepId: step.id,
        stepLabel: step.label,
        index,
        total,
        progress: startProgress,
      });
    }

    let result;
    try {
      result = await step.run(context);
    } catch (error) {
      const failure = buildFailure({
        step,
        index,
        total,
        progress: startProgress,
        message: "Schritt konnte nicht ausgeführt werden.",
        hint: "Bitte Anwendung neu starten (Reload).",
        detail: error instanceof Error ? error.message : "Unbekannter Fehler.",
      });
      if (typeof onError === "function") onError(failure);
      return { ok: false, error: failure };
    }

    const normalized = normalizeStepResult({ step, result, index, total, progress: Math.round(((index + 1) / total) * 100) });
    if (typeof onProgress === "function") onProgress({ stage: "complete", ...normalized });

    if (!normalized.ok) {
      if (typeof onError === "function") onError(normalized);
      return { ok: false, error: normalized };
    }
  }

  const summary = { ok: true, steps: total, progress: 100 };
  if (typeof onDone === "function") onDone(summary);
  return summary;
}
