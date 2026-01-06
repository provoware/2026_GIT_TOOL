import assert from "node:assert/strict";
import test from "node:test";
import { buildIpcError, buildIpcSuccess, createSafeHandle } from "../src/utils/ipcSafe.js";

test("buildIpcSuccess wraps data in a valid response", () => {
  const payload = { value: 42 };
  const response = buildIpcSuccess(payload);

  assert.equal(response.ok, true);
  assert.deepEqual(response.data, payload);
});

test("buildIpcError returns a structured error response", () => {
  const error = new Error("Boom");
  error.code = "E_BOOM";
  const response = buildIpcError(error, "templates:load");

  assert.equal(response.ok, false);
  assert.equal(response.error.message, "Boom");
  assert.equal(response.error.code, "E_BOOM");
  assert.equal(response.error.context, "templates:load");
  assert.ok(response.error.details);
});

test("createSafeHandle wraps IPC handlers and logs errors", async () => {
  let loggedMessage = "";
  const ipcMain = {
    handle: (channel, handler) => {
      ipcMain.channel = channel;
      ipcMain.handler = handler;
    }
  };
  const logger = {
    error: (message) => {
      loggedMessage = message;
    }
  };

  const safeHandle = createSafeHandle({ ipcMain, logger });
  safeHandle("templates:test", async () => {
    throw new Error("Failure");
  });

  const response = await ipcMain.handler();

  assert.equal(ipcMain.channel, "templates:test");
  assert.equal(response.ok, false);
  assert.equal(response.error.message, "Failure");
  assert.ok(loggedMessage.includes("templates:test"));
});
