export const ensureNonEmptyString = (value, label) => {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${label} muss ein nicht-leerer Text sein.`);
  }

  return value.trim();
};

export const ensureBoolean = (value, label) => {
  if (typeof value !== "boolean") {
    throw new Error(`${label} muss true oder false sein.`);
  }

  return value;
};

export const ensureInList = (value, list, label) => {
  if (!list.includes(value)) {
    throw new Error(`${label} ist ungültig.`);
  }

  return value;
};
