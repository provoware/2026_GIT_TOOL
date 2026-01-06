const themeButtons = document.querySelectorAll(".theme-button");
const clockElement = document.querySelector(".clock");
const statusElement = document.querySelector(".status-message");
const templateList = document.querySelector("#template-list");
const favoritesList = document.querySelector("#favorites-list");
const categoryList = document.querySelector("#category-list");
const statsList = document.querySelector("#stats-list");
const searchInput = document.querySelector("#search-input");
const sortSelect = document.querySelector("#sort-select");
const templateForm = document.querySelector("#template-form");
const titleInput = document.querySelector("#template-title");
const categoryInput = document.querySelector("#template-category");
const descriptionInput = document.querySelector("#template-description");
const contentInput = document.querySelector("#template-content");
const tagsInput = document.querySelector("#template-tags");
const newTemplateButton = document.querySelector("#new-template");
const duplicateButton = document.querySelector("#duplicate-template");
const toggleFavoriteButton = document.querySelector("#toggle-favorite");
const copyButton = document.querySelector("#copy-template");
const markUsedButton = document.querySelector("#mark-used");
const exportTemplateTxt = document.querySelector("#export-template-txt");
const exportTemplateJson = document.querySelector("#export-template-json");
const exportCategoryButton = document.querySelector("#export-category");
const exportArchiveButton = document.querySelector("#export-archive");
const importButton = document.querySelector("#import-templates");
const deleteButton = document.querySelector("#delete-template");
const undoButton = document.querySelector("#undo-delete");
const addCategoryButton = document.querySelector("#add-category");
const newCategoryInput = document.querySelector("#new-category");
const resetCategoryButton = document.querySelector("#reset-category");
const favoritesFilterButton = document.querySelector("#filter-favorites");

const DEFAULT_CATEGORIES = [
  "ChatGPT – Universal",
  "Agenten-Prompting",
  "Linux / Bash",
  "Entwickler / Code",
  "Electron / Desktop-Apps",
  "KI-Bild-Generierung",
  "Analyse / Struktur",
  "Automatisierung / Workflows",
  "Persönlich / Eigene"
];

const isNonEmptyString = (value) => typeof value === "string" && value.trim().length > 0;

const setStatus = (message) => {
  if (statusElement && isNonEmptyString(message)) {
    statusElement.textContent = message.trim();
    return true;
  }
  return false;
};

const ensureList = (value) => (Array.isArray(value) ? value : []);

const getAllowedThemes = (buttons) =>
  Array.from(buttons)
    .map((button) => button.dataset.theme)
    .filter((theme) => isNonEmptyString(theme));

const updateClock = () => {
  const now = new Date();
  const timeString = now.toLocaleTimeString("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });

  if (clockElement) {
    const label = `Uhrzeit: ${timeString}`;
    clockElement.textContent = label;
    return clockElement.textContent === label;
  }

  return false;
};

const applyTheme = (themeClass, allowedThemes) => {
  if (!isNonEmptyString(themeClass)) {
    return false;
  }

  if (!Array.isArray(allowedThemes) || allowedThemes.length === 0) {
    return false;
  }

  if (!allowedThemes.includes(themeClass)) {
    return false;
  }

  document.body.className = themeClass;
  return document.body.className === themeClass;
};

const state = {
  payload: null,
  stats: null,
  selectedId: null,
  selectedCategory: null,
  filterFavorites: false,
  search: "",
  sort: "usage",
  lastDeleted: null
};

const updateState = (next) => {
  state.payload = next.payload ?? state.payload;
  state.stats = next.stats ?? state.stats;
  return state;
};

const getTemplates = () => ensureList(state.payload?.templates);

const renderFavorites = () => {
  if (!favoritesList) {
    return false;
  }
  const favorites = getTemplates().filter((template) => template.favorite);
  favoritesList.innerHTML = "";
  favorites.forEach((template) => {
    const item = document.createElement("li");
    item.textContent = template.title;
    favoritesList.appendChild(item);
  });
  return true;
};

const renderCategories = () => {
  if (!categoryList) {
    return false;
  }
  const categoriesFromTemplates = getTemplates().map((template) => template.category);
  const combined = [...new Set([...DEFAULT_CATEGORIES, ...categoriesFromTemplates])].sort((a, b) =>
    a.localeCompare(b, "de")
  );
  categoryList.innerHTML = "";
  combined.forEach((category) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = category;
    button.className = state.selectedCategory === category ? "primary" : "";
    button.addEventListener("click", () => {
      state.selectedCategory = category;
      renderTemplates();
      renderCategories();
    });
    item.appendChild(button);
    categoryList.appendChild(item);
  });
  return true;
};

const renderStats = () => {
  if (!statsList || !state.stats) {
    return false;
  }
  const { totals, categoryStats } = state.stats;
  const entries = [
    `Templates gesamt: ${totals.templatesCount}`,
    `Favoriten: ${totals.favoritesCount}`,
    `Nutzung gesamt: ${totals.usageTotal}`,
    `Mind. 1x benutzt: ${totals.usedAtLeastOnce}`
  ];

  const topCategory = Object.entries(categoryStats)
    .sort((a, b) => b[1].count - a[1].count)[0];
  if (topCategory) {
    entries.push(`Meistgenutzte Kategorie: ${topCategory[0]}`);
  }

  statsList.innerHTML = "";
  entries.forEach((entry) => {
    const item = document.createElement("li");
    item.textContent = entry;
    statsList.appendChild(item);
  });
  return true;
};

const sortTemplates = (templates) => {
  const sorted = [...templates];
  if (state.sort === "recent") {
    sorted.sort((a, b) => (b.lastUsed ?? "").localeCompare(a.lastUsed ?? ""));
  } else if (state.sort === "alpha") {
    sorted.sort((a, b) => a.title.localeCompare(b.title, "de"));
  } else {
    sorted.sort((a, b) => b.usageCount - a.usageCount || a.title.localeCompare(b.title, "de"));
  }
  return sorted;
};

const getFilteredTemplates = () => {
  const templates = getTemplates();
  const searchTerm = state.search.toLowerCase();
  return sortTemplates(
    templates.filter((template) => {
      if (state.filterFavorites && !template.favorite) {
        return false;
      }
      if (state.selectedCategory && template.category !== state.selectedCategory) {
        return false;
      }
      if (!searchTerm) {
        return true;
      }
      const tags = ensureList(template.tags).join(" ");
      return (
        template.title.toLowerCase().includes(searchTerm) ||
        template.category.toLowerCase().includes(searchTerm) ||
        tags.toLowerCase().includes(searchTerm)
      );
    })
  );
};

const renderTemplates = () => {
  if (!templateList) {
    return false;
  }
  const templates = getFilteredTemplates();
  templateList.innerHTML = "";
  templates.forEach((template) => {
    const item = document.createElement("li");
    item.className = "template-card";
    if (template.id === state.selectedId) {
      item.classList.add("is-active");
    }

    const title = document.createElement("strong");
    title.textContent = template.title;

    const description = document.createElement("p");
    description.textContent = template.description;

    const meta = document.createElement("div");
    meta.className = "template-meta";
    const category = document.createElement("span");
    category.className = "badge";
    category.textContent = template.category;
    const favorite = document.createElement("span");
    favorite.textContent = template.favorite ? "⭐ Favorit" : "☆ Nicht favorisiert";

    meta.appendChild(category);
    meta.appendChild(favorite);

    item.appendChild(title);
    item.appendChild(description);
    item.appendChild(meta);

    item.addEventListener("click", () => {
      selectTemplate(template.id, true);
    });

    templateList.appendChild(item);
  });
  return true;
};

const renderAll = () => {
  renderFavorites();
  renderCategories();
  renderStats();
  renderTemplates();
};

const buildTemplatePayload = () => {
  const title = titleInput?.value ?? "";
  const category = categoryInput?.value ?? "";
  const content = contentInput?.value ?? "";
  const description = descriptionInput?.value ?? "";
  const tags = (tagsInput?.value ?? "")
    .split(",")
    .map((tag) => tag.trim())
    .filter((tag) => isNonEmptyString(tag));

  if (!isNonEmptyString(title)) {
    setStatus("Titel fehlt. Bitte ausfüllen.");
    titleInput?.focus();
    return null;
  }
  if (!isNonEmptyString(category)) {
    setStatus("Kategorie fehlt. Bitte ausfüllen.");
    categoryInput?.focus();
    return null;
  }
  if (!isNonEmptyString(content)) {
    setStatus("Inhalt fehlt. Bitte ausfüllen.");
    contentInput?.focus();
    return null;
  }

  return {
    title: title.trim(),
    category: category.trim(),
    description: description.trim() || "Ohne Beschreibung.",
    content: content.trim(),
    tags
  };
};

const selectTemplate = (templateId, markUsed) => {
  const templates = getTemplates();
  const selected = templates.find((template) => template.id === templateId);
  if (!selected) {
    return false;
  }
  state.selectedId = selected.id;
  titleInput.value = selected.title;
  categoryInput.value = selected.category;
  descriptionInput.value = selected.description;
  contentInput.value = selected.content;
  tagsInput.value = ensureList(selected.tags).join(", ");

  if (markUsed) {
    updateTemplateUsage(selected.id);
  }

  renderTemplates();
  return true;
};

const updateTemplateUsage = (templateId) => {
  const templates = getTemplates();
  const updatedTemplates = templates.map((template) => {
    if (template.id !== templateId) {
      return template;
    }
    const nextCount = Number(template.usageCount ?? 0) + 1;
    return {
      ...template,
      usageCount: nextCount,
      lastUsed: new Date().toISOString()
    };
  });

  return saveTemplates(updatedTemplates, "Nutzung aktualisiert.");
};

const saveTemplates = async (templates, message) => {
  const payload = {
    meta: state.payload?.meta ?? {},
    templates
  };
  const response = await window.templatesApi.save(payload);
  updateState(response);
  renderAll();
  if (message) {
    setStatus(message);
  }
  return response;
};

const resetForm = () => {
  titleInput.value = "";
  categoryInput.value = "";
  descriptionInput.value = "";
  contentInput.value = "";
  tagsInput.value = "";
  state.selectedId = null;
};

const duplicateTemplate = () => {
  const templates = getTemplates();
  const current = templates.find((template) => template.id === state.selectedId);
  if (!current) {
    setStatus("Bitte zuerst ein Template auswählen.");
    return;
  }
  const duplicate = {
    ...current,
    id: crypto.randomUUID(),
    title: `${current.title} (Kopie)`,
    usageCount: 0,
    lastUsed: null,
    favorite: false,
    created: new Date().toISOString(),
    updated: new Date().toISOString()
  };
  saveTemplates([...templates, duplicate], "Template dupliziert.");
};

const toggleFavorite = () => {
  const templates = getTemplates();
  const updated = templates.map((template) => {
    if (template.id !== state.selectedId) {
      return template;
    }
    return { ...template, favorite: !template.favorite };
  });
  saveTemplates(updated, "Favorit aktualisiert.");
};

const handleCopy = async () => {
  const templates = getTemplates();
  const current = templates.find((template) => template.id === state.selectedId);
  if (!current) {
    setStatus("Bitte zuerst ein Template auswählen.");
    return;
  }
  try {
    await navigator.clipboard.writeText(current.content);
    setStatus("Inhalt kopiert. Du kannst ihn jetzt einfügen.");
    updateTemplateUsage(current.id);
  } catch (error) {
    setStatus("Kopieren fehlgeschlagen. Bitte erneut versuchen.");
  }
};

const handleDelete = () => {
  const templates = getTemplates();
  const current = templates.find((template) => template.id === state.selectedId);
  if (!current) {
    setStatus("Bitte zuerst ein Template auswählen.");
    return;
  }
  state.lastDeleted = current;
  undoButton.hidden = false;
  const nextTemplates = templates.filter((template) => template.id !== current.id);
  saveTemplates(nextTemplates, "Template gelöscht. Du kannst es rückgängig machen.");
  resetForm();
};

const handleUndo = () => {
  if (!state.lastDeleted) {
    return;
  }
  const templates = getTemplates();
  const restored = [...templates, state.lastDeleted];
  state.lastDeleted = null;
  undoButton.hidden = true;
  saveTemplates(restored, "Löschen rückgängig gemacht.");
};

const handleExportTemplate = async (format) => {
  const templates = getTemplates();
  const current = templates.find((template) => template.id === state.selectedId);
  if (!current) {
    setStatus("Bitte zuerst ein Template auswählen.");
    return;
  }
  try {
    const filePath = await window.templatesApi.exportTemplate(current, format);
    setStatus(`Export erstellt: ${filePath}`);
  } catch (error) {
    setStatus("Export fehlgeschlagen. Bitte Dateinamen prüfen.");
  }
};

const handleExportCategory = async () => {
  const templates = getTemplates();
  const current = templates.find((template) => template.id === state.selectedId);
  const category = current?.category ?? state.selectedCategory;
  if (!isNonEmptyString(category)) {
    setStatus("Bitte eine Kategorie auswählen.");
    return;
  }
  try {
    const filePath = await window.templatesApi.exportCategory(category);
    setStatus(`Kategorie exportiert: ${filePath}`);
  } catch (error) {
    setStatus("Kategorie-Export fehlgeschlagen. Bitte prüfen.");
  }
};

const handleExportArchive = async () => {
  try {
    const filePath = await window.templatesApi.exportArchive();
    setStatus(`Archiv exportiert: ${filePath}`);
  } catch (error) {
    setStatus("Archiv-Export fehlgeschlagen. Bitte erneut versuchen.");
  }
};

const handleImport = async () => {
  try {
    const result = await window.templatesApi.importTemplates();
    if (!result) {
      setStatus("Import abgebrochen.");
      return;
    }
    updateState(result);
    renderAll();
    setStatus("Import abgeschlossen.");
  } catch (error) {
    setStatus("Import fehlgeschlagen. Bitte JSON prüfen.");
  }
};

const handleAddCategory = () => {
  const value = newCategoryInput?.value ?? "";
  if (!isNonEmptyString(value)) {
    setStatus("Bitte einen Kategorienamen eingeben.");
    return;
  }
  state.selectedCategory = value.trim();
  newCategoryInput.value = "";
  renderCategories();
  renderTemplates();
  setStatus("Kategorie hinzugefügt.");
};

const handleSave = async (event) => {
  event.preventDefault();
  const payload = buildTemplatePayload();
  if (!payload) {
    return;
  }

  const templates = getTemplates();
  let nextTemplates = templates;
  const nowIso = new Date().toISOString();

  if (state.selectedId) {
    nextTemplates = templates.map((template) =>
      template.id === state.selectedId
        ? {
            ...template,
            ...payload,
            updated: nowIso
          }
        : template
    );
    await saveTemplates(nextTemplates, "Template gespeichert.");
  } else {
    const newTemplate = {
      id: crypto.randomUUID(),
      favorite: false,
      usageCount: 0,
      lastUsed: null,
      editable: true,
      created: nowIso,
      updated: nowIso,
      ...payload
    };
    nextTemplates = [...templates, newTemplate];
    await saveTemplates(nextTemplates, "Neues Template erstellt.");
    state.selectedId = newTemplate.id;
  }

  renderTemplates();
};

if (themeButtons.length > 0) {
  const allowedThemes = getAllowedThemes(themeButtons);
  const initialTheme = document.body.className;

  themeButtons.forEach((button) => {
    const isActive = button.dataset.theme === initialTheme;
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });

  themeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const themeClass = button.dataset.theme;
      const applied = applyTheme(themeClass, allowedThemes);

      if (applied) {
        themeButtons.forEach((entry) => {
          entry.setAttribute("aria-pressed", entry === button ? "true" : "false");
        });
      }
    });
  });
}

searchInput?.addEventListener("input", (event) => {
  state.search = event.target.value;
  renderTemplates();
});

sortSelect?.addEventListener("change", (event) => {
  state.sort = event.target.value;
  renderTemplates();
});

favoritesFilterButton?.addEventListener("click", () => {
  state.filterFavorites = !state.filterFavorites;
  favoritesFilterButton.classList.toggle("primary", state.filterFavorites);
  renderTemplates();
});

resetCategoryButton?.addEventListener("click", () => {
  state.selectedCategory = null;
  renderTemplates();
  renderCategories();
});

addCategoryButton?.addEventListener("click", handleAddCategory);
newTemplateButton?.addEventListener("click", () => {
  resetForm();
  setStatus("Neues Template: Bitte Felder ausfüllen.");
});

duplicateButton?.addEventListener("click", duplicateTemplate);

toggleFavoriteButton?.addEventListener("click", toggleFavorite);

copyButton?.addEventListener("click", handleCopy);

markUsedButton?.addEventListener("click", () => {
  if (state.selectedId) {
    updateTemplateUsage(state.selectedId);
  } else {
    setStatus("Bitte zuerst ein Template auswählen.");
  }
});

exportTemplateTxt?.addEventListener("click", () => handleExportTemplate("txt"));
exportTemplateJson?.addEventListener("click", () => handleExportTemplate("json"));
exportCategoryButton?.addEventListener("click", handleExportCategory);
exportArchiveButton?.addEventListener("click", handleExportArchive);
importButton?.addEventListener("click", handleImport);

deleteButton?.addEventListener("click", handleDelete);
undoButton?.addEventListener("click", handleUndo);

templateForm?.addEventListener("submit", handleSave);

const init = async () => {
  if (!window.templatesApi) {
    setStatus("Template-API nicht verfügbar.");
    return;
  }
  const response = await window.templatesApi.load();
  updateState(response);
  renderAll();
  setStatus("Templates geladen. Wähle eine Vorlage oder erstelle eine neue.");
};

updateClock();
setInterval(updateClock, 1000);

init();
