import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import {
  ensureBoolean,
  ensureNonEmptyString,
  ensurePlainObject
} from "./validation.js";
import { buildQualityRunResult } from "./quality.js";

const ensureFunction = (value, label) => {
  if (typeof value !== "function") {
    throw new Error(`${label} muss eine Funktion sein.`);
  }

  return value;
};

const ensureOptionalString = (value, label) => {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  return ensureNonEmptyString(value, label);
};

const ensureNonNegativeInteger = (value, label) => {
  if (!Number.isInteger(value) || value < 0) {
    throw new Error(`${label} muss eine nicht-negative ganze Zahl sein.`);
  }
  return value;
};

const ensureLogger = (logger) => {
  const safeLogger = ensurePlainObject(logger, "logger");
  ensureFunction(safeLogger.info, "logger.info");
  ensureFunction(safeLogger.warn, "logger.warn");
  ensureFunction(safeLogger.error, "logger.error");
  ensureFunction(safeLogger.debug, "logger.debug");
  return safeLogger;
};

const normalizeCommandResult = (result, label) => {
  const normalizedResult = ensurePlainObject(result, label);
  const ok = ensureBoolean(normalizedResult.ok, `${label}.ok`);
  const exitCode = ensureNonNegativeInteger(
    normalizedResult.exitCode,
    `${label}.exitCode`
  );
  const status = ensureNonEmptyString(normalizedResult.status, `${label}.status`);
  const errorMessage = ensureOptionalString(
    normalizedResult.errorMessage,
    `${label}.errorMessage`
  );

  return {
    ok,
    exitCode,
    status,
    errorMessage
  };
};

const buildRunMessage = (step) => {
  const normalizedStep = ensurePlainObject(step, "step");
  const label = ensureNonEmptyString(normalizedStep.label, "label");
  const description = ensureNonEmptyString(
    normalizedStep.description,
    "description"
  );
  return `${label}: ${description}`;
};

const buildDependencyResult = ({ ok, message }) => ({
  ok: ensureBoolean(ok, "dependency.ok"),
  message: ensureNonEmptyString(message, "dependency.message")
});

const buildFailureHints = (step, commandResult) => {
  const hints = [];
  const command = ensureNonEmptyString(step.command, "step.command");
  const helpHint = ensureOptionalString(step.help, "step.help");

  hints.push(`Befehl erneut starten: ${command}`);
  if (helpHint) {
    hints.push(`Hinweis (Hilfe): ${helpHint}`);
  }
  if (step.fixCommand) {
    hints.push(
      `Auto-Fix (automatische Reparatur) verfügbar: ${ensureNonEmptyString(
        step.fixCommand,
        "step.fixCommand"
      )}`
    );
  }
  if (commandResult.errorMessage) {
    hints.push(
      `Systemhinweis (Fehlertext): ${commandResult.errorMessage}`
    );
  }

  return hints;
};

export const createShellCommandRunner = (options = {}) => {
  const normalizedOptions =
    options === undefined ? {} : ensurePlainObject(options, "options");
  const spawnHandler = ensureFunction(
    normalizedOptions.spawnSync ?? spawnSync,
    "spawnSync"
  );

  return ({ command, label, logger }) => {
    const safeCommand = ensureNonEmptyString(command, "command");
    const safeLabel = ensureNonEmptyString(label, "label");
    const safeLogger = ensureLogger(logger);

    safeLogger.info(`[Schritt] ${safeLabel} startet.`);
    safeLogger.debug(`[Debug] Starte Befehl: ${safeCommand}`);

    const result = spawnHandler(safeCommand, { shell: true, stdio: "inherit" });
    const exitCode =
      typeof result.status === "number" ? result.status : 1;
    const ok = exitCode === 0;
    const status = ok ? "ok" : "failed";
    const errorMessage =
      result.error instanceof Error ? result.error.message : null;

    if (errorMessage) {
      safeLogger.warn(
        `[Hinweis] Systemfehler erkannt (Error): ${errorMessage}`
      );
    }

    safeLogger.info(
      `[Status] ${safeLabel} beendet: ${status.toUpperCase()} (Exit-Code ${exitCode}).`
    );

    return normalizeCommandResult(
      {
        ok,
        exitCode,
        status,
        errorMessage
      },
      "commandResult"
    );
  };
};

export const ensureDependencies = ({
  logger,
  commandRunner,
  projectRoot = process.cwd()
}) => {
  const safeLogger = ensureLogger(logger);
  const safeCommandRunner = ensureFunction(commandRunner, "commandRunner");
  const safeRoot = ensureNonEmptyString(projectRoot, "projectRoot");
  const nodeModulesPath = path.join(safeRoot, "node_modules");

  if (fs.existsSync(nodeModulesPath)) {
    safeLogger.info(
      "[Info] Abhängigkeiten (Dependencies) vorhanden. Keine Installation nötig."
    );
    return buildDependencyResult({
      ok: true,
      message: "Abhängigkeiten vorhanden."
    });
  }

  safeLogger.warn(
    "[Hinweis] Abhängigkeiten fehlen. Ich starte npm install (automatische Installation)."
  );
  const installResult = normalizeCommandResult(
    safeCommandRunner({
      command: "npm install",
      label: "Abhängigkeiten installieren (Dependencies)",
      logger: safeLogger
    }),
    "installResult"
  );

  if (!installResult.ok) {
    safeLogger.error(
      "[Fehler] Abhängigkeiten konnten nicht installiert werden."
    );
    safeLogger.error(
      "[Hinweis] Bitte Internetzugang prüfen oder npm install manuell starten."
    );
  }

  return buildDependencyResult({
    ok: installResult.ok,
    message: installResult.ok
      ? "Abhängigkeiten installiert."
      : "Abhängigkeiten fehlen weiterhin."
  });
};

export const runQualityPlan = ({ plan, logger, commandRunner }) => {
  const normalizedPlan = ensurePlainObject(plan, "plan");
  const safeLogger = ensureLogger(logger);
  const safeCommandRunner = ensureFunction(commandRunner, "commandRunner");
  const steps = Array.isArray(normalizedPlan.steps) ? normalizedPlan.steps : [];
  const stopOnFailure = ensureBoolean(
    normalizedPlan.stopOnFailure,
    "stopOnFailure"
  );
  const results = [];

  let overallOk = true;

  steps.forEach((step) => {
    if (!overallOk && stopOnFailure) {
      return;
    }

    const message = buildRunMessage(step);
    safeLogger.info(`[Info] ${message}`);

    const firstRun = normalizeCommandResult(
      safeCommandRunner({
        command: step.command,
        label: step.label,
        logger: safeLogger
      }),
      `${step.id}.firstRun`
    );

    if (firstRun.ok) {
      results.push({
        id: step.id,
        label: step.label,
        status: "ok",
        message: "Prüfung erfolgreich abgeschlossen."
      });
      return;
    }

    if (step.shouldFix && step.fixCommand) {
      safeLogger.warn(
        "[Hinweis] Fehler erkannt. Ich starte Auto-Fix (automatische Reparatur)."
      );
      const fixRun = normalizeCommandResult(
        safeCommandRunner({
          command: step.fixCommand,
          label: `${step.label} Auto-Fix`,
          logger: safeLogger
        }),
        `${step.id}.fixRun`
      );
      if (fixRun.ok) {
        safeLogger.info(
          "[Info] Auto-Fix abgeschlossen. Ich prüfe erneut (Re-Check)."
        );
        const retryRun = normalizeCommandResult(
          safeCommandRunner({
            command: step.command,
            label: step.label,
            logger: safeLogger
          }),
          `${step.id}.retryRun`
        );
        if (retryRun.ok) {
          results.push({
            id: step.id,
            label: step.label,
            status: "ok",
            message: "Auto-Fix erfolgreich, Prüfung besteht."
          });
          return;
        }
      }
    }

    const hints = buildFailureHints(step, firstRun);
    results.push({
      id: step.id,
      label: step.label,
      status: "failed",
      message:
        hints.length > 0
          ? `Prüfung fehlgeschlagen. Hinweise (Tipps): ${hints.join(" | ")}`
          : "Prüfung fehlgeschlagen. Bitte Ausgabe prüfen."
    });
    overallOk = false;
  });

  return buildQualityRunResult({ ok: overallOk, steps: results });
};
