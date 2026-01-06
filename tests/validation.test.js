import { test } from "node:test";
import assert from "node:assert/strict";
import {
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString
} from "../src/utils/validation.js";

test("ensureNonEmptyString trims input", () => {
  const result = ensureNonEmptyString("  ok ", "label");
  assert.equal(result, "ok");
});

test("ensureBoolean rejects non boolean", () => {
  assert.throws(() => ensureBoolean("yes", "flag"), /flag muss true oder false sein/);
});

test("ensureInList validates values", () => {
  assert.equal(ensureInList("a", ["a", "b"], "field"), "a");
});
