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

contextBridge.exposeInMainWorld("templatesApi", templatesApi);
