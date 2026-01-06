const logValidationError = (message) => {
  console.warn(`[validate] ${message}`);
};

export const ensureNonEmptyString = (value, label) => {
  if (typeof value !== "string" || value.trim().length === 0) {
    const message = `${label} muss ein nicht-leerer Text sein.`;
    logValidationError(message);
    throw new Error(message);
  }

  return value.trim();
};

export const ensurePlainObject = (value, label) => {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    const message = `${label} muss ein Objekt sein.`;
    logValidationError(message);
    throw new Error(message);
  }

  return value;
};

export const ensureBoolean = (value, label) => {
  if (typeof value !== "boolean") {
    const message = `${label} muss true oder false sein.`;
    logValidationError(message);
    throw new Error(message);
  }

  return value;
};

export const ensureArray = (values, label) => {
  if (!Array.isArray(values)) {
    const message = `${label} muss eine Liste sein.`;
    logValidationError(message);
    throw new Error(message);
  }

  return values;
};

export const ensureArrayOfNonEmptyStrings = (values, label) => {
  if (!Array.isArray(values) || values.length === 0) {
    const message = `${label} muss eine Liste mit Werten sein.`;
    logValidationError(message);
    throw new Error(message);
  }

  return values.map((value, index) =>
    ensureNonEmptyString(value, `${label}[${index}]`)
  );
};

export const ensureArrayOfStrings = (values, label) => {
  if (!Array.isArray(values)) {
    const message = `${label} muss eine Liste sein.`;
    logValidationError(message);
    throw new Error(message);
  }

  return values.map((value, index) =>
    ensureNonEmptyString(value, `${label}[${index}]`)
  );
};

export const ensureInList = (value, list, label) => {
  if (!list.includes(value)) {
    const message = `${label} ist ungültig.`;
    logValidationError(message);
    throw new Error(message);
  }

  return value;
};

export const ensurePositiveInteger = (value, label) => {
  if (!Number.isInteger(value) || value <= 0) {
    const message = `${label} muss eine positive ganze Zahl sein.`;
    logValidationError(message);
    throw new Error(message);
  }

  return value;
};

export const ensureOptionalString = (value, label) => {
  if (value === undefined || value === null || value === "") {
    return null;
  }

  return ensureNonEmptyString(value, label);
};

export const ensureFunction = (value, label) => {
  if (typeof value !== "function") {
    const message = `${label} muss eine Funktion sein.`;
    logValidationError(message);
    throw new Error(message);
  }

  return value;
};
