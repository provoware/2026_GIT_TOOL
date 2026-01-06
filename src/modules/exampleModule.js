import { ensureNonEmptyString, ensurePlainObject } from "../core/validation.js";

export const manifest = {
  id: "example-module",
  name: "Beispiel-Modul",
  version: "1.0.0"
};

export const activate = (context = {}) => {
  const normalizedContext = ensurePlainObject(context, "context");
  const logger = ensurePlainObject(normalizedContext.logger, "context.logger");
  const appName = ensureNonEmptyString(normalizedContext.appName, "context.appName");

  if (typeof logger.info !== "function") {
    throw new Error("context.logger.info muss eine Funktion sein.");
  }

  logger.info(`Beispiel-Modul aktiv: ${appName}`);

  return {
    status: "aktiv",
    message: "Beispiel-Modul bereit."
  };
};

export const deactivate = () => ({
  status: ensureNonEmptyString("inaktiv", "deactivate.status"),
  message: ensureNonEmptyString("Beispiel-Modul beendet.", "deactivate.message")
});
