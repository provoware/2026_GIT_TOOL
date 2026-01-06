import { contextBridge, ipcRenderer } from "electron";

const templatesApi = {
  load: () => ipcRenderer.invoke("templates:load"),
  save: (payload) => ipcRenderer.invoke("templates:save", payload),
  exportTemplate: (template, format) =>
    ipcRenderer.invoke("templates:export", { template, format }),
  exportCategory: (category) => ipcRenderer.invoke("templates:exportCategory", { category }),
  exportArchive: () => ipcRenderer.invoke("templates:exportArchive"),
  importTemplates: () => ipcRenderer.invoke("templates:import")
};

const startupApi = {
  onStatus: (handler) => {
    if (typeof handler !== "function") {
      throw new Error("startupApi.onStatus erwartet eine Funktion.");
    }
    const listener = (_event, payload) => handler(payload);
    ipcRenderer.on("startup:status", listener);
    return () => ipcRenderer.removeListener("startup:status", listener);
  }
};

contextBridge.exposeInMainWorld("templatesApi", templatesApi);
contextBridge.exposeInMainWorld("startupApi", startupApi);
