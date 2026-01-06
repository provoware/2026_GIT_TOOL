export const ensureNonEmptyString = (value, label) => {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${label} muss ein nicht-leerer Text sein.`);
  }

  return value.trim();
};

export const ensurePlainObject = (value, label) => {
  if (
    value === null ||
    typeof value !== "object" ||
    Array.isArray(value)
  ) {
    throw new Error(`${label} muss ein Objekt sein.`);
  }

  return value;
};

export const ensureBoolean = (value, label) => {
  if (typeof value !== "boolean") {
    throw new Error(`${label} muss true oder false sein.`);
  }

  return value;
};

export const ensureArrayOfNonEmptyStrings = (values, label) => {
  if (!Array.isArray(values) || values.length === 0) {
    throw new Error(`${label} muss eine Liste mit Werten sein.`);
  }

  return values.map((value, index) =>
    ensureNonEmptyString(value, `${label}[${index}]`)
  );
};

export const ensureInList = (value, list, label) => {
  if (!list.includes(value)) {
    throw new Error(`${label} ist ungültig.`);
  }

  return value;
};
