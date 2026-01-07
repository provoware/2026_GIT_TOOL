import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  ArrowDown,
  ArrowUp,
  BadgeInfo,
  ClipboardCheck,
  Dice5,
  Download,
  FileJson,
  Filter,
  FolderPlus,
  LayoutDashboard,
  Library,
  Monitor,
  Moon,
  Pencil,
  Plus,
  RefreshCcw,
  Scale,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Star,
  StarOff,
  Sun,
  Trash2,
  Upload,
  ListChecks,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
} from "recharts";

const APP_VERSION = "1.2.3";
const LS_KEY = "pppoppi_gms_archiv_v1";
const DEFAULT_SCALE = 1.0;

const nowIso = () => new Date().toISOString();
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const norm = (s) => (s ?? "").trim().replace(/\s+/g, " ");
const normKey = (s) => norm(s).toLowerCase();

function safeJsonParse(text) {
  try {
    return { ok: true, value: JSON.parse(text) };
  } catch (e) {
    return { ok: false, error: e };
  }
}

function safeLsGet(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}
function safeLsSet(key, value) {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}
function safeLsRemove(key) {
  try {
    localStorage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

function downloadText(filename, content, mime = "application/json") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function pickUnique(arr, count) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a.slice(0, clamp(count, 0, a.length));
}

function dedupeByKey(items, getKey) {
  const seen = new Set();
  const out = [];
  for (const it of items) {
    const k = getKey(it);
    if (!seen.has(k)) {
      seen.add(k);
      out.push(it);
    }
  }
  return out;
}

function humanTime(iso) {
  if (!iso) return "–";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "–";
  return d.toLocaleString();
}

function makeId() {
  const c = typeof globalThis !== "undefined" ? globalThis.crypto : null;
  if (c && typeof c.randomUUID === "function") return c.randomUUID();
  return Math.random().toString(16).slice(2) + "_" + Date.now().toString(16);
}

const ITEM_TYPES = [
  { id: "genre", label: "Genres", icon: Library, tone: "blue" },
  { id: "mood", label: "Moods", icon: Activity, tone: "green" },
  { id: "style", label: "Stile", icon: ListChecks, tone: "amber" },
];

const THEMES = [
  {
    id: "nebula",
    name: "Nebel (Dunkel)",
    icon: Moon,
    vars: {
      "--bg": "#050812",
      "--bg2": "#070d1f",
      "--star": "rgba(255,255,255,0.18)",

      "--panel": "rgba(2,6,23,0.78)",
      "--panel2": "rgba(2,6,23,0.90)",
      "--panelHover": "rgba(2,6,23,0.97)",

      "--border": "rgba(148,163,184,0.58)",
      "--border2": "rgba(148,163,184,0.36)",

      "--text": "rgba(248,250,252,0.99)",
      "--muted": "rgba(226,232,240,0.86)",
      "--muted2": "rgba(226,232,240,0.78)",

      "--inputBg": "rgba(2,6,23,0.96)",
      "--inputBorder": "rgba(148,163,184,0.52)",
      "--inputText": "rgba(248,250,252,0.99)",

      "--focus": "rgba(56,189,248,0.86)",

      "--accent": "rgba(16,185,129,0.92)",
      "--accentBorder": "rgba(16,185,129,0.62)",

      "--primary": "rgba(59,130,246,0.94)",
      "--primaryBorder": "rgba(59,130,246,0.66)",

      "--warn": "rgba(245,158,11,0.92)",
      "--warnBorder": "rgba(245,158,11,0.66)",

      "--danger": "rgba(244,63,94,0.92)",
      "--dangerBorder": "rgba(244,63,94,0.66)",

      "--ghost": "rgba(148,163,184,0.10)",
      "--ghostHover": "rgba(148,163,184,0.22)",
    },
  },
  {
    id: "high-contrast",
    name: "Hoher Kontrast",
    icon: ShieldCheck,
    vars: {
      "--bg": "#000000",
      "--bg2": "#050505",
      "--star": "rgba(255,255,255,0.30)",

      "--panel": "rgba(0,0,0,0.94)",
      "--panel2": "rgba(0,0,0,0.99)",
      "--panelHover": "rgba(0,0,0,1)",

      "--border": "rgba(255,255,255,0.88)",
      "--border2": "rgba(255,255,255,0.66)",

      "--text": "rgba(255,255,255,1)",
      "--muted": "rgba(255,255,255,0.92)",
      "--muted2": "rgba(255,255,255,0.86)",

      "--inputBg": "rgba(0,0,0,0.99)",
      "--inputBorder": "rgba(255,255,255,0.86)",
      "--inputText": "rgba(255,255,255,1)",

      "--focus": "rgba(0,255,255,0.98)",

      "--accent": "rgba(0,255,160,0.98)",
      "--accentBorder": "rgba(0,255,160,0.80)",

      "--primary": "rgba(0,140,255,0.98)",
      "--primaryBorder": "rgba(0,140,255,0.80)",

      "--warn": "rgba(255,185,0,0.98)",
      "--warnBorder": "rgba(255,185,0,0.80)",

      "--danger": "rgba(255,45,85,0.98)",
      "--dangerBorder": "rgba(255,45,85,0.80)",

      "--ghost": "rgba(255,255,255,0.10)",
      "--ghostHover": "rgba(255,255,255,0.22)",
    },
  },
  {
    id: "midnight",
    name: "Mitternachtsblau",
    icon: Monitor,
    vars: {
      "--bg": "#020617",
      "--bg2": "#020a1f",
      "--star": "rgba(255,255,255,0.16)",

      "--panel": "rgba(2,6,23,0.78)",
      "--panel2": "rgba(2,6,23,0.90)",
      "--panelHover": "rgba(2,6,23,0.97)",

      "--border": "rgba(148,163,184,0.54)",
      "--border2": "rgba(148,163,184,0.34)",

      "--text": "rgba(248,250,252,0.99)",
      "--muted": "rgba(226,232,240,0.86)",
      "--muted2": "rgba(226,232,240,0.78)",

      "--inputBg": "rgba(2,6,23,0.96)",
      "--inputBorder": "rgba(148,163,184,0.48)",
      "--inputText": "rgba(248,250,252,0.99)",

      "--focus": "rgba(167,139,250,0.86)",

      "--accent": "rgba(34,197,94,0.92)",
      "--accentBorder": "rgba(34,197,94,0.62)",

      "--primary": "rgba(99,102,241,0.94)",
      "--primaryBorder": "rgba(99,102,241,0.66)",

      "--warn": "rgba(245,158,11,0.92)",
      "--warnBorder": "rgba(245,158,11,0.66)",

      "--danger": "rgba(244,63,94,0.92)",
      "--dangerBorder": "rgba(244,63,94,0.66)",

      "--ghost": "rgba(148,163,184,0.10)",
      "--ghostHover": "rgba(148,163,184,0.22)",
    },
  },
  {
    id: "paper",
    name: "Papier (Hell)",
    icon: Sun,
    vars: {
      "--bg": "#f8fafc",
      "--bg2": "#eef2ff",
      "--star": "rgba(15,23,42,0.08)",

      "--panel": "rgba(255,255,255,0.92)",
      "--panel2": "rgba(255,255,255,0.98)",
      "--panelHover": "rgba(255,255,255,1)",

      "--border": "rgba(15,23,42,0.40)",
      "--border2": "rgba(15,23,42,0.24)",

      "--text": "rgba(15,23,42,0.98)",
      "--muted": "rgba(15,23,42,0.78)",
      "--muted2": "rgba(15,23,42,0.70)",

      "--inputBg": "rgba(255,255,255,1)",
      "--inputBorder": "rgba(15,23,42,0.36)",
      "--inputText": "rgba(15,23,42,0.98)",

      "--focus": "rgba(37,99,235,0.78)",

      "--accent": "rgba(5,150,105,0.92)",
      "--accentBorder": "rgba(5,150,105,0.50)",

      "--primary": "rgba(37,99,235,0.92)",
      "--primaryBorder": "rgba(37,99,235,0.50)",

      "--warn": "rgba(217,119,6,0.92)",
      "--warnBorder": "rgba(217,119,6,0.50)",

      "--danger": "rgba(225,29,72,0.92)",
      "--dangerBorder": "rgba(225,29,72,0.50)",

      "--ghost": "rgba(15,23,42,0.06)",
      "--ghostHover": "rgba(15,23,42,0.10)",
    },
  },
];

function applyTheme(themeId) {
  const theme = THEMES.find((t) => t.id === themeId) || THEMES[0];
  const root = document.documentElement;
  for (const [k, v] of Object.entries(theme.vars)) root.style.setProperty(k, v);
  root.dataset.theme = theme.id;
  return theme.id;
}

function applyScale(scale) {
  const root = document.documentElement;
  const px = 16 * clamp(scale, 0.8, 1.6);
  root.style.fontSize = `${px}px`;
}

function makeDefaultState() {
  const createdAt = nowIso();
  return {
    version: 1,
    updatedAt: createdAt,
    settings: {
      activeProfile: "Standard",
      favoritesOnly: false,
      themeId: "nebula",
      uiScale: DEFAULT_SCALE,
      generator: {
        mode: "mix",
        count: 12,
        perType: { genre: 6, mood: 4, style: 6 },
        range: { min: 8, max: 24 },
        delimiter: ", ",
        showTypeLabels: false,
        includeTypes: { genre: true, mood: true, style: true },
      },
      autosaveMinutes: 10,
      maxLogs: 500,
    },
    profiles: {
      Standard: {
        createdAt,
        updatedAt: createdAt,
        items: [],
      },
    },
    logs: [],
    stats: {
      generatorRuns: 0,
      lastRunAt: null,
      lastRunMode: null,
      lastRunCount: 0,
      totalGeneratedTokens: 0,
      duplicatesIgnored: 0,
      itemsAdded: 0,
      exports: 0,
      imports: 0,
      lastExportAt: null,
      lastImportAt: null,
    },
  };
}

function normalizeItem(raw, fallbackType = "genre") {
  const type = ["genre", "mood", "style"].includes(raw?.type) ? raw.type : fallbackType;
  const value = norm(raw?.value ?? raw?.key ?? "");
  const key = normKey(raw?.key ? raw.key : value);
  const createdAt = typeof raw?.createdAt === "string" && raw.createdAt ? raw.createdAt : nowIso();
  const updatedAt = typeof raw?.updatedAt === "string" && raw.updatedAt ? raw.updatedAt : createdAt;
  return {
    id: typeof raw?.id === "string" && raw.id ? raw.id : makeId(),
    type,
    value,
    key,
    favorite: !!raw?.favorite,
    createdAt,
    updatedAt,
  };
}

function coerceState(maybe) {
  const fallback = makeDefaultState();
  if (!maybe || typeof maybe !== "object") return fallback;

  const state = { ...fallback, ...maybe };
  state.settings = { ...fallback.settings, ...(maybe.settings || {}) };
  state.settings.generator = { ...fallback.settings.generator, ...((maybe.settings || {}).generator || {}) };
  state.settings.generator.perType = { ...fallback.settings.generator.perType, ...(((maybe.settings || {}).generator || {}).perType || {}) };
  state.settings.generator.range = { ...fallback.settings.generator.range, ...(((maybe.settings || {}).generator || {}).range || {}) };
  state.settings.generator.includeTypes = { ...fallback.settings.generator.includeTypes, ...(((maybe.settings || {}).generator || {}).includeTypes || {}) };

  state.profiles = { ...(maybe.profiles || fallback.profiles) };
  for (const [p, v] of Object.entries(state.profiles)) {
    const items = Array.isArray(v?.items) ? v.items : [];
    state.profiles[p] = {
      createdAt: v?.createdAt || state.updatedAt || nowIso(),
      updatedAt: v?.updatedAt || state.updatedAt || nowIso(),
      items: items.map((it) => normalizeItem(it, it?.type)).filter((it) => it.key && it.value),
    };
  }

  state.logs = Array.isArray(maybe.logs) ? maybe.logs : [];
  state.stats = { ...fallback.stats, ...(maybe.stats || {}) };
  state.version = 1;
  state.updatedAt = maybe.updatedAt || nowIso();

  if (!state.settings.activeProfile || !state.profiles?.[state.settings.activeProfile]) {
    const p = Object.keys(state.profiles || {}).sort((a, b) => a.localeCompare(b))[0];
    state.settings.activeProfile = p || "Standard";
  }
  if (!THEMES.some((t) => t.id === state.settings.themeId)) state.settings.themeId = "nebula";
  if (typeof state.settings.uiScale !== "number") state.settings.uiScale = DEFAULT_SCALE;

  return state;
}

function validateState(st) {
  const errors = [];
  if (!st || typeof st !== "object") errors.push("State ist kein Objekt.");
  if (!st?.profiles || typeof st.profiles !== "object") errors.push("profiles fehlt oder ist ungültig.");
  if (!st?.settings || typeof st.settings !== "object") errors.push("settings fehlt oder ist ungültig.");
  if (st?.profiles) {
    for (const [pname, p] of Object.entries(st.profiles)) {
      if (!p || typeof p !== "object") errors.push(`Profil ${pname} ist ungültig.`);
      if (!Array.isArray(p?.items)) errors.push(`Profil ${pname}.items ist nicht Array.`);
      if (Array.isArray(p?.items)) {
        for (const it of p.items) {
          if (!it?.id) errors.push(`Profil ${pname}: item ohne id`);
          if (!["genre", "mood", "style"].includes(it?.type)) errors.push(`Profil ${pname}: item mit ungültigem type`);
          if (!it?.value || !it?.key) errors.push(`Profil ${pname}: item mit leerem value/key`);
        }
      }
    }
  }
  if (!st?.settings?.activeProfile || !st?.profiles?.[st.settings.activeProfile]) errors.push("activeProfile fehlt oder existiert nicht.");
  return { ok: errors.length === 0, errors };
}

function useCtrlWheelZoom(scale, setScale) {
  useEffect(() => {
    const onWheel = (e) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      const delta = e.deltaY > 0 ? -0.05 : 0.05;
      setScale((s) => clamp(Number(s) + delta, 0.8, 1.6));
    };
    window.addEventListener("wheel", onWheel, { passive: false });
    return () => window.removeEventListener("wheel", onWheel);
  }, [setScale]);

  useEffect(() => {
    applyScale(scale);
  }, [scale]);
}

function TonePill({ children, tone = "slate" }) {
  const toneMap = {
    slate: "bg-[color:var(--panel)] border-[color:var(--border2)] text-[color:var(--text)]",
    blue: "bg-[rgba(37,99,235,0.20)] border-[rgba(37,99,235,0.50)] text-[color:var(--text)]",
    green: "bg-[rgba(5,150,105,0.20)] border-[rgba(5,150,105,0.50)] text-[color:var(--text)]",
    amber: "bg-[rgba(245,158,11,0.20)] border-[rgba(245,158,11,0.50)] text-[color:var(--text)]",
    red: "bg-[rgba(244,63,94,0.20)] border-[rgba(244,63,94,0.50)] text-[color:var(--text)]",
  };
  return (
    <span className={`inline-flex items-center gap-2 rounded-md border px-2 py-1 text-xs ${toneMap[tone] || toneMap.slate}`}>
      {children}
    </span>
  );
}

function IconButton({ label, onClick, disabled, tone = "ghost", children }) {
  const toneClass = {
    ghost: "btn btn-ghost",
    secondary: "btn btn-secondary",
    primary: "btn btn-primary",
    ok: "btn btn-ok",
    warn: "btn btn-warn",
    danger: "btn btn-danger",
  }[tone] || "btn btn-ghost";
  return (
    <button
      type="button"
      className={`h-9 w-9 grid place-items-center ${toneClass}`}
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
    >
      {children}
    </button>
  );
}

function Button({ children, onClick, disabled, tone = "secondary", className = "" }) {
  const toneClass = {
    secondary: "btn btn-secondary",
    primary: "btn btn-primary",
    ok: "btn btn-ok",
    warn: "btn btn-warn",
    danger: "btn btn-danger",
    ghost: "btn btn-ghost",
  }[tone] || "btn btn-secondary";
  return (
    <button type="button" className={`${toneClass} px-3 py-2 text-sm font-medium ${className}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

function Card({ title, icon: Icon, actions, children }) {
  return (
    <section className="glass rounded-xl overflow-hidden">
      <header className="px-4 py-3 border-b" style={{ borderColor: "var(--border2)" }}>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {Icon ? <Icon className="h-5 w-5" /> : null}
            <div className="text-[color:var(--text)] font-semibold tracking-wide">{title}</div>
          </div>
          {actions}
        </div>
      </header>
      <div className="px-4 py-4">{children}</div>
    </section>
  );
}

function StatTile({ label, value, hint }) {
  return (
    <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
      <div className="text-xs uppercase tracking-wide" style={{ color: "var(--muted2)" }}>{label}</div>
      <div className="mt-1 text-2xl font-semibold" style={{ color: "var(--text)" }}>{value}</div>
      {hint ? <div className="mt-1 text-xs" style={{ color: "var(--muted2)" }}>{hint}</div> : null}
    </div>
  );
}

function TypeBadge({ type }) {
  const m = {
    genre: { tone: "blue", label: "Genre" },
    mood: { tone: "green", label: "Mood" },
    style: { tone: "amber", label: "Stil" },
  }[type] || { tone: "slate", label: type };
  return <TonePill tone={m.tone}>{m.label}</TonePill>;
}

function Sidebar({ nav, setNav }) {
  const navItems = useMemo(() => ([
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "archiv", label: "Archiv", icon: Library },
    { id: "generator", label: "Generator", icon: Dice5 },
    { id: "importexport", label: "Import/Export", icon: FileJson },
    { id: "settings", label: "Einstellungen", icon: Settings },
  ]), []);

  return (
    <aside className="glass rounded-xl overflow-hidden">
      <div className="h-14 grid place-items-center border-b" style={{ borderColor: "var(--border2)" }}>
        <div className="h-9 w-9 rounded-lg grid place-items-center" style={{ background: "var(--panel2)", border: "1px solid var(--border2)" }}>
          <BadgeInfo className="h-5 w-5" />
        </div>
      </div>
      <div className="py-2">
        {navItems.map((n) => {
          const Icon = n.icon;
          const active = nav === n.id;
          return (
            <div key={n.id} className="px-2 py-1">
              <button
                type="button"
                className={`h-11 w-full rounded-lg grid place-items-center ${active ? "btn btn-primary" : "btn btn-ghost"}`}
                onClick={() => setNav(n.id)}
                aria-label={n.label}
                title={n.label}
              >
                <Icon className="h-5 w-5" />
              </button>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

function Topbar({
  globalSearch, setGlobalSearch,
  themeId, setThemeId,
  favoritesOnly, setFavoritesOnly,
  scale, resetScale,
  exportAll, openImport,
  archiveStats, activeProfileName, updatedAt,
  pushLog, showToast,
}) {
  const theme = THEMES.find((t) => t.id === themeId) || THEMES[0];
  const ThemeIcon = theme.icon;

  return (
    <div className="glass rounded-xl px-4 py-3">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl grid place-items-center" style={{ background: "var(--panel2)", border: "1px solid var(--border2)" }}>
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xl font-semibold tracking-wide" style={{ color: "var(--text)" }}>GMS Archiv Tool</div>
            <div className="text-sm" style={{ color: "var(--muted2)" }}>
              v{APP_VERSION} • Themes • Zoom
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-end lg:gap-3">
          <div className="relative w-full lg:w-[360px]">
            <Search className="absolute left-3 top-2.5 h-4 w-4" style={{ color: "var(--muted)" }} />
            <input
              className="ui-input rounded-xl pl-10 pr-3 py-2 w-full"
              value={globalSearch}
              onChange={(e) => setGlobalSearch(e.target.value)}
              placeholder="Suche (Groß/Klein egal)"
              aria-label="Suche"
            />
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <div className="rounded-xl border px-3 py-2 flex items-center gap-2" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
              <label className="text-sm" style={{ color: "var(--muted)" }}>Nur Favoriten</label>
              <input
                type="checkbox"
                checked={!!favoritesOnly}
                onChange={(e) => {
                  setFavoritesOnly(e.target.checked);
                  pushLog("settings", "Nur-Favoriten Modus geändert", { value: e.target.checked });
                  showToast(e.target.checked ? "Favoriten: AN" : "Favoriten: AUS");
                }}
                aria-label="Nur Favoriten verwenden"
              />
            </div>

            <div className="rounded-xl border px-3 py-2 flex items-center gap-2" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
              <ThemeIcon className="h-4 w-4" />
              <select
                className="bg-transparent outline-none text-sm"
                style={{ color: "var(--text)" }}
                value={themeId}
                onChange={(e) => {
                  const id = applyTheme(e.target.value);
                  setThemeId(id);
                  pushLog("ui", "Theme geändert", { themeId: id });
                  showToast("Theme gesetzt");
                }}
                aria-label="Theme wählen"
              >
                {THEMES.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>

            <div className="rounded-xl border px-3 py-2 flex items-center gap-2" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
              <Scale className="h-4 w-4" />
              <span className="text-sm" style={{ color: "var(--muted)" }}>{Math.round(scale * 100)}%</span>
              <button type="button" className="btn btn-ghost px-2 py-1 text-xs" onClick={resetScale}>Reset</button>
            </div>

            <Button tone="primary" onClick={exportAll} className="flex items-center gap-2">
              <Download className="h-4 w-4" /> Export
            </Button>
            <Button tone="secondary" onClick={openImport} className="flex items-center gap-2">
              <Upload className="h-4 w-4" /> Import
            </Button>
          </div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <TonePill tone="blue">Einträge: {archiveStats.total.total}</TonePill>
        <TonePill tone="green">Favoriten: {archiveStats.total.favorites}</TonePill>
        <TonePill tone="amber">Unique: {archiveStats.uniqueTotal}</TonePill>
        <TonePill tone="slate">Dupes ignoriert: {archiveStats.duplicatesIgnored}</TonePill>
        <TonePill tone="slate">Profil: {activeProfileName}</TonePill>
        <TonePill tone="slate">Update: {humanTime(updatedAt)}</TonePill>
      </div>
    </div>
  );
}

function QuickInputs({ addInputs, setAddInputs, onSubmitType }) {
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {ITEM_TYPES.map((t) => {
        const Icon = t.icon;
        const submit = () => onSubmitType(t.id, addInputs[t.id]);
        return (
          <div key={t.id} className="space-y-2">
            <label className="text-sm font-semibold flex items-center gap-2" style={{ color: "var(--text)" }}>
              <Icon className="h-4 w-4" /> {t.label}
            </label>
            <div className="flex gap-2">
              <input
                className="ui-input rounded-xl px-3 py-2 w-full"
                value={addInputs[t.id]}
                onChange={(e) => setAddInputs((p) => ({ ...p, [t.id]: e.target.value }))}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    submit();
                  }
                }}
                placeholder="Komma-getrennt: a, b, c"
                aria-label={`${t.label} Eingabe`}
              />
              <Button tone="ok" onClick={submit} className="flex items-center gap-2">
                <Plus className="h-4 w-4" /> OK
              </Button>
            </div>
            <div className="text-xs" style={{ color: "var(--muted2)" }}>
              Enter bestätigt. Duplikate (Groß/Klein egal) werden ignoriert.
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ArchiveTable({ rows, showProfile, onToggleFav, onMove, onEdit, onDelete }) {
  return (
    <div className="space-y-2">
      <div className="overflow-hidden rounded-lg border" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
        <div
          className={`grid ${showProfile ? "grid-cols-[40px_120px_90px_1fr_220px]" : "grid-cols-[40px_90px_1fr_220px]"} px-3 py-3 border-b`}
          style={{ borderColor: "var(--border2)", background: "var(--panel2)" }}
        >
          <div className="text-xs uppercase tracking-wide" style={{ color: "var(--muted2)" }}>Fav</div>
          {showProfile ? <div className="text-xs uppercase tracking-wide" style={{ color: "var(--muted2)" }}>Profil</div> : null}
          <div className="text-xs uppercase tracking-wide" style={{ color: "var(--muted2)" }}>Typ</div>
          <div className="text-xs uppercase tracking-wide" style={{ color: "var(--muted2)" }}>Wert</div>
          <div className="text-xs uppercase tracking-wide text-right" style={{ color: "var(--muted2)" }}>Aktion</div>
        </div>

        <div className="divide-y" style={{ borderColor: "var(--border2)" }}>
          {rows.map((r) => (
            <div
              key={`${r.profile}-${r.id}`}
              className={`grid ${showProfile ? "grid-cols-[40px_120px_90px_1fr_220px]" : "grid-cols-[40px_90px_1fr_220px]"} px-3 py-3 items-center`}
              style={{ borderColor: "var(--border2)" }}
            >
              <div>
                <IconButton label={r.favorite ? "Favorit entfernen" : "Als Favorit"} onClick={() => onToggleFav(r.profile, r.id)}>
                  {r.favorite ? <Star className="h-4 w-4" /> : <StarOff className="h-4 w-4" />}
                </IconButton>
              </div>
              {showProfile ? <div className="text-sm truncate" style={{ color: "var(--muted)" }}>{r.profile}</div> : null}
              <div className="flex items-center gap-2"><TypeBadge type={r.type} /></div>
              <div className="min-w-0">
                <div className="truncate" style={{ color: "var(--text)" }}>{r.value}</div>
                <div className="text-xs" style={{ color: "var(--muted2)" }}>
                  {(r.createdAt ? new Date(r.createdAt).toLocaleDateString() : "–")} • key: {r.key}
                </div>
              </div>
              <div className="flex items-center justify-end gap-1">
                <IconButton label="Hoch" onClick={() => onMove(r.profile, r.id, -1)}><ArrowUp className="h-4 w-4" /></IconButton>
                <IconButton label="Runter" onClick={() => onMove(r.profile, r.id, +1)}><ArrowDown className="h-4 w-4" /></IconButton>
                <IconButton label="Bearbeiten" onClick={() => onEdit(r.profile, r)}><Pencil className="h-4 w-4" /></IconButton>
                <IconButton label="Löschen" onClick={() => onDelete(r.profile, r.id)}><Trash2 className="h-4 w-4" /></IconButton>
              </div>
            </div>
          ))}
          {rows.length === 0 ? <div className="px-3 py-8 text-sm" style={{ color: "var(--muted)" }}>Keine Treffer.</div> : null}
        </div>
      </div>
    </div>
  );
}

function GeneratorPanel({
  activeProfileName,
  favoritesOnly,
  generatorPoolLen,
  generatorResults,
  generatorError,
  lastCopiedAt,
  settingsGenerator,
  setGen,
  runGenerator,
  copyResults,
  formatResults,
  pushLog,
  showToast,
}) {
  const g = settingsGenerator;

  const quickPresets = useMemo(() => ([
    { id: "p8", label: "8", apply: () => setGen({ mode: "mix", count: 8 }) },
    { id: "p12", label: "12", apply: () => setGen({ mode: "mix", count: 12 }) },
    { id: "p16", label: "16", apply: () => setGen({ mode: "mix", count: 16 }) },
    { id: "bal", label: "Balanced 12", apply: () => setGen({ mode: "balanced", count: 12 }) },
    { id: "pt", label: "Pro Typ 6/4/6", apply: () => setGen({ mode: "perType", perType: { genre: 6, mood: 4, style: 6 } }) },
    { id: "rng", label: "Range 8-24", apply: () => setGen({ mode: "range", range: { min: 8, max: 24 } }) },
    { id: "shuf", label: "Shuffle All", apply: () => setGen({ mode: "shuffleAll" }) },
    { id: "fav", label: "Fav First 12", apply: () => setGen({ mode: "favFirst", count: 12 }) },
  ]), [setGen]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <TonePill tone={favoritesOnly ? "amber" : "slate"}>
            {favoritesOnly ? "Quelle: Favoriten" : `Quelle: Profil „${activeProfileName}“`}
          </TonePill>
          <TonePill tone="slate">Pool: {generatorPoolLen}</TonePill>
        </div>

        <div className="flex items-center gap-2">
          <Button tone="primary" onClick={runGenerator} className="flex items-center gap-2">
            <Dice5 className="h-4 w-4" /> Generieren
          </Button>
          <Button tone="secondary" onClick={copyResults} disabled={!generatorResults?.length} className="flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4" /> Kopieren
          </Button>
        </div>
      </div>

      <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
        <div className="flex items-center justify-between gap-2">
          <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>Schnell-Presets</div>
          <div className="text-xs" style={{ color: "var(--muted2)" }}>Setzt Modus + Werte</div>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          {quickPresets.map((p) => (
            <Button
              key={p.id}
              tone="secondary"
              onClick={() => { p.apply(); pushLog("generator", "Preset gesetzt", { preset: p.id }); showToast(`Preset: ${p.label}`); }}
              className="px-3 py-2"
            >
              {p.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm font-semibold flex items-center gap-2" style={{ color: "var(--text)" }}>
              <Filter className="h-4 w-4" /> Modus
            </div>
          </div>

          <div className="mt-2 grid grid-cols-2 gap-2">
            {[
              { id: "mix", label: "Mix" },
              { id: "balanced", label: "Balanced" },
              { id: "perType", label: "Pro Typ" },
              { id: "range", label: "Range" },
              { id: "shuffleAll", label: "Shuffle" },
              { id: "favFirst", label: "Fav First" },
            ].map((m) => (
              <button
                key={m.id}
                type="button"
                className={`btn px-3 py-2 text-sm ${g.mode === m.id ? "btn-primary" : "btn-secondary"}`}
                onClick={() => { setGen({ mode: m.id }); pushLog("generator", "Modus gesetzt", { mode: m.id }); }}
              >
                {m.label}
              </button>
            ))}
          </div>

          <div className="mt-3">
            <div className="text-xs uppercase tracking-wide" style={{ color: "var(--muted2)" }}>Typen im Pool</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {["genre", "mood", "style"].map((t) => (
                <label
                  key={t}
                  className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm"
                  style={{ borderColor: "var(--border2)", background: "var(--panel2)" }}
                >
                  <input
                    type="checkbox"
                    checked={g.includeTypes?.[t] !== false}
                    onChange={(e) => setGen({ includeTypes: { ...g.includeTypes, [t]: e.target.checked } })}
                    aria-label={`${t} einbeziehen`}
                  />
                  <span style={{ color: "var(--text)" }}>{t}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
          <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>Parameter</div>

          {(g.mode === "mix" || g.mode === "balanced" || g.mode === "favFirst") ? (
            <div className="mt-2 space-y-2">
              <label className="text-sm" style={{ color: "var(--muted)" }}>Anzahl (N)</label>
              <input
                type="number"
                className="ui-input rounded-lg px-3 py-2 w-full"
                min={0}
                max={999}
                value={g.count}
                onChange={(e) => setGen({ count: clamp(Number(e.target.value || 0), 0, 999) })}
              />
            </div>
          ) : null}

          {g.mode === "perType" ? (
            <div className="mt-2 grid grid-cols-3 gap-2">
              {["genre", "mood", "style"].map((t) => (
                <div key={t} className="space-y-2">
                  <label className="text-sm" style={{ color: "var(--muted)" }}>{t}</label>
                  <input
                    type="number"
                    className="ui-input rounded-lg px-3 py-2 w-full"
                    min={0}
                    max={999}
                    value={g.perType?.[t] ?? 0}
                    onChange={(e) => setGen({ perType: { ...g.perType, [t]: clamp(Number(e.target.value || 0), 0, 999) } })}
                  />
                </div>
              ))}
            </div>
          ) : null}

          {g.mode === "range" ? (
            <div className="mt-2 grid grid-cols-2 gap-2">
              <div className="space-y-2">
                <label className="text-sm" style={{ color: "var(--muted)" }}>Min</label>
                <input
                  type="number"
                  className="ui-input rounded-lg px-3 py-2 w-full"
                  min={0}
                  max={999}
                  value={g.range?.min ?? 0}
                  onChange={(e) => {
                    const v = clamp(Number(e.target.value || 0), 0, 999);
                    setGen({ range: { ...g.range, min: v, max: Math.max(v, Number(g.range?.max ?? v)) } });
                  }}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm" style={{ color: "var(--muted)" }}>Max</label>
                <input
                  type="number"
                  className="ui-input rounded-lg px-3 py-2 w-full"
                  min={0}
                  max={999}
                  value={g.range?.max ?? 0}
                  onChange={(e) => {
                    const v = clamp(Number(e.target.value || 0), 0, 999);
                    setGen({ range: { ...g.range, max: Math.max(v, Number(g.range?.min ?? 0)) } });
                  }}
                />
              </div>
            </div>
          ) : null}

          <div className="mt-3 space-y-2">
            <label className="text-sm" style={{ color: "var(--muted)" }}>Delimiter</label>
            <input
              className="ui-input rounded-lg px-3 py-2 w-full"
              value={g.delimiter}
              onChange={(e) => setGen({ delimiter: e.target.value })}
              placeholder=", "
            />
            <label className="flex items-center gap-2 text-sm" style={{ color: "var(--muted)" }}>
              <input type="checkbox" checked={!!g.showTypeLabels} onChange={(e) => setGen({ showTypeLabels: e.target.checked })} />
              Typ-Labels (genre:value)
            </label>
          </div>
        </div>
      </div>

      {generatorError ? (
        <div className="rounded-lg border p-3 text-sm" style={{ borderColor: "var(--dangerBorder)", background: "rgba(244,63,94,0.14)", color: "var(--text)" }}>
          {generatorError}
        </div>
      ) : null}

      <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
        <div className="flex items-center justify-between gap-2">
          <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>Ergebnis</div>
          <div className="flex items-center gap-2">
            <TonePill tone="slate">Count: {generatorResults?.length || 0}</TonePill>
            <TonePill tone="slate">Kopiert: {lastCopiedAt ? humanTime(lastCopiedAt) : "–"}</TonePill>
          </div>
        </div>

        <div className="mt-2">
          <textarea readOnly className="ui-input rounded-lg p-3 w-full min-h-[120px]" value={formatResults(generatorResults || [])} aria-label="Generator Ergebnis" />
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {(generatorResults || []).slice(0, 24).map((x, idx) => (
            <span key={`${x.type}-${x.key}-${idx}`} className="badge">{x.value}</span>
          ))}
          {(generatorResults || []).length > 24 ? <span className="badge">+{(generatorResults || []).length - 24}</span> : null}
        </div>
      </div>
    </div>
  );
}

function ProfileManager({
  profiles,
  activeProfileName,
  onSelect,
  onCreate,
  onRename,
  onDelete,
}) {
  const [newName, setNewName] = useState("");
  const [renameFrom, setRenameFrom] = useState(activeProfileName);
  const [renameTo, setRenameTo] = useState("");

  useEffect(() => { setRenameFrom(activeProfileName); }, [activeProfileName]);

  return (
    <div className="space-y-4">
      <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
        <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>Profil wählen</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {profiles.map((p) => (
            <button key={p} type="button" className={`btn px-3 py-2 text-sm ${p === activeProfileName ? "btn-primary" : "btn-secondary"}`} onClick={() => onSelect(p)}>
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
          <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>Neues Profil</div>
          <div className="mt-2 flex gap-2">
            <input className="ui-input rounded-lg px-3 py-2 w-full" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="z.B. EDM, Film, Dark" />
            <Button tone="ok" onClick={() => { onCreate(newName); setNewName(""); }} className="flex items-center gap-2">
              <FolderPlus className="h-4 w-4" /> Erstellen
            </Button>
          </div>
        </div>

        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
          <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>Umbenennen</div>
          <div className="mt-2 space-y-2">
            <select className="ui-input rounded-lg px-3 py-2 w-full" value={renameFrom} onChange={(e) => setRenameFrom(e.target.value)} aria-label="Quelle Profil">
              {profiles.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
            <div className="flex gap-2">
              <input className="ui-input rounded-lg px-3 py-2 w-full" value={renameTo} onChange={(e) => setRenameTo(e.target.value)} placeholder="Neuer Name" />
              <Button tone="primary" onClick={() => { onRename(renameFrom, renameTo); setRenameTo(""); }} className="flex items-center gap-2">
                <Pencil className="h-4 w-4" /> OK
              </Button>
            </div>
          </div>
        </div>

        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
          <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>Löschen</div>
          <div className="mt-2 space-y-2">
            <div className="text-sm" style={{ color: "var(--muted)" }}>Löscht Profil inkl. aller Einträge.</div>
            <Button tone="danger" onClick={() => onDelete(activeProfileName)} className="w-full flex items-center justify-center gap-2">
              <Trash2 className="h-4 w-4" /> Aktives Profil löschen
            </Button>
          </div>
        </div>
      </div>

      <div className="rounded-lg border p-3 text-sm" style={{ borderColor: "var(--border2)", background: "var(--panel)", color: "var(--muted)" }}>
        Tipp: Favoriten sind global. „Nur Favoriten“ macht den Generator profil-übergreifend.
      </div>
    </div>
  );
}

function ImportExport({
  importText, setImportText,
  onFilePick,
  onImportMerge,
  onImportReplace,
  exportAll,
  exportProfile,
  activeProfileName,
  onSelfTest,
  fileRef,
}) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_1fr]">
      <Card title="Export" icon={Download}>
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Button tone="primary" onClick={exportAll} className="flex items-center gap-2">
              <Download className="h-4 w-4" /> Gesamt JSON
            </Button>
            <Button tone="secondary" onClick={() => exportProfile(activeProfileName)} className="flex items-center gap-2">
              <Download className="h-4 w-4" /> Profil JSON
            </Button>
          </div>
        </div>
      </Card>

      <Card title="Import" icon={Upload}>
        <div className="space-y-3">
          <input ref={fileRef} type="file" accept="application/json,.json" className="hidden" onChange={(e) => onFilePick(e.target.files?.[0])} />
          <div className="flex flex-wrap items-center gap-2">
            <Button tone="primary" onClick={() => fileRef.current?.click()} className="flex items-center gap-2">
              <Upload className="h-4 w-4" /> Datei wählen
            </Button>
            <Button tone="secondary" onClick={() => setImportText("")} className="flex items-center gap-2">
              <Trash2 className="h-4 w-4" /> Leeren
            </Button>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold" style={{ color: "var(--text)" }}>JSON einfügen</label>
            <textarea
              className="ui-input rounded-xl p-3 w-full min-h-[260px]"
              value={importText}
              onChange={(e) => setImportText(e.target.value)}
              placeholder="Gesamt-Export oder Profil-Export hier rein"
              aria-label="Import JSON"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button tone="ok" onClick={onImportMerge} className="flex items-center gap-2">
              <RefreshCcw className="h-4 w-4" /> Import (Merge)
            </Button>
            <Button tone="danger" onClick={onImportReplace} className="flex items-center gap-2">
              <Trash2 className="h-4 w-4" /> Import (Ersetzen)
            </Button>
          </div>
        </div>
      </Card>

      <Card title="Diagnose" icon={ShieldCheck} actions={<Button tone="primary" onClick={onSelfTest}>Self-Test</Button>}>
        <div className="text-sm" style={{ color: "var(--muted)" }}>
          Self-Test prüft State + Export-Roundtrip.
        </div>
      </Card>
    </div>
  );
}

function SettingsPanel({ onResetStorage }) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_1fr]">
      <Card title="UI" icon={Settings}>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
          <div className="text-sm" style={{ color: "var(--muted)" }}>
            Ctrl + Mausrad zoomt UI. Themes sind kontrastig. Fokus-Ring ist stark sichtbar.
          </div>
        </div>
      </Card>

      <Card title="Daten" icon={FileJson}>
        <div className="flex flex-wrap gap-2">
          <Button tone="danger" onClick={onResetStorage}>
            Reset (LocalStorage)
          </Button>
        </div>
      </Card>
    </div>
  );
}

function DashboardView({
  state,
  activeProfileName,
  listPreviewRows,
  addInputs,
  setAddInputs,
  addCommaSeparated,
  exportProfile,
  setNav,
  generatorPoolLen,
  generator,
  generatorSettings,
  setGen,
  runGenerator,
  copyResults,
  formatResults,
  pushLog,
  showToast,
  archiveStats,
  profiles,
  allItemsLen,
  chartAll,
  chartProfile,
  toggleFavorite,
  moveItem,
  openEdit,
  removeItem,
}) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.25fr_0.75fr]">
      <div className="space-y-4">
        <Card
          title="Schnell-Eingabe"
          icon={Plus}
          actions={
            <div className="flex items-center gap-2">
              <TonePill tone="slate">Zuletzt: {humanTime(state.updatedAt)}</TonePill>
              <TonePill tone="slate">Profil: {activeProfileName}</TonePill>
            </div>
          }
        >
          <QuickInputs addInputs={addInputs} setAddInputs={setAddInputs} onSubmitType={addCommaSeparated} />
        </Card>

        <Card
          title="Archiv Übersicht"
          icon={Library}
          actions={
            <div className="flex items-center gap-2">
              <Button tone="primary" onClick={() => setNav("archiv")}>Öffnen</Button>
              <Button tone="secondary" onClick={() => exportProfile(activeProfileName)}>Profil Export</Button>
            </div>
          }
        >
          <div className="text-sm mb-2" style={{ color: "var(--muted)" }}>
            Dashboard zeigt max. 10 Treffer (Filter über Suche oben). Vollansicht im Tab Archiv.
          </div>
          <ArchiveTable
            rows={listPreviewRows}
            showProfile={false}
            onToggleFav={toggleFavorite}
            onMove={moveItem}
            onEdit={openEdit}
            onDelete={removeItem}
          />
        </Card>

        <Card
          title="Generator Schnellstart"
          icon={Dice5}
          actions={
            <div className="flex items-center gap-2">
              <TonePill tone="slate">Runs: {state.stats.generatorRuns}</TonePill>
              <TonePill tone="slate">Letzter: {humanTime(state.stats.lastRunAt)}</TonePill>
            </div>
          }
        >
          <GeneratorPanel
            activeProfileName={activeProfileName}
            favoritesOnly={state.settings.favoritesOnly}
            generatorPoolLen={generatorPoolLen}
            generatorResults={generator.results}
            generatorError={generator.error}
            lastCopiedAt={generator.lastCopiedAt}
            settingsGenerator={generatorSettings}
            setGen={setGen}
            runGenerator={runGenerator}
            copyResults={copyResults}
            formatResults={formatResults}
            pushLog={pushLog}
            showToast={showToast}
          />
        </Card>
      </div>

      <div className="space-y-4">
        <Card title="Statistik" icon={SlidersHorizontal}>
          <div className="grid grid-cols-2 gap-3">
            <StatTile label="Gesamt" value={archiveStats.total.total} />
            <StatTile label="Unique" value={archiveStats.uniqueTotal} />
            <StatTile label="Favoriten" value={archiveStats.total.favorites} />
            <StatTile label="Profile" value={profiles.length} />
            <StatTile label="Adds" value={state.stats.itemsAdded} hint="seit Start (Stats)" />
            <StatTile label="Dupes" value={state.stats.duplicatesIgnored} hint="ignoriert" />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4">
            <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
              <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>Typen Gesamt (Graph)</div>
              <div className="h-52 mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartAll}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border2)" />
                    <XAxis dataKey="name" stroke="var(--muted)" />
                    <YAxis stroke="var(--muted)" />
                    <RTooltip contentStyle={{ background: "var(--panel2)", border: "1px solid var(--border2)", color: "var(--text)" }} />
                    <Bar dataKey="value" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-lg border p-3" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
              <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>Aktives Profil (Graph)</div>
              <div className="h-44 mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartProfile}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border2)" />
                    <XAxis dataKey="name" stroke="var(--muted)" />
                    <YAxis stroke="var(--muted)" />
                    <RTooltip contentStyle={{ background: "var(--panel2)", border: "1px solid var(--border2)", color: "var(--text)" }} />
                    <Bar dataKey="value" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </Card>

        <Card title="Letzte Logs" icon={Activity}>
          <div className="space-y-2">
            {(state.logs || []).slice(0, 8).map((l) => (
              <div key={l.id} className="rounded-lg border px-3 py-2" style={{ borderColor: "var(--border2)", background: "var(--panel)" }}>
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs" style={{ color: "var(--muted2)" }}>{humanTime(l.at)}</div>
                  <span className="badge">{l.type}</span>
                </div>
                <div className="text-sm mt-1" style={{ color: "var(--text)" }}>{l.message}</div>
              </div>
            ))}
            {(!state.logs || state.logs.length === 0) ? <div className="text-sm" style={{ color: "var(--muted)" }}>Noch keine Logs.</div> : null}
          </div>
        </Card>
      </div>
    </div>
  );
}

function ArchivView({
  activeProfileName,
  profiles,
  setActiveProfile,
  pushLog,
  archiveStats,
  listRows,
  addInputs,
  setAddInputs,
  addCommaSeparated,
  exportProfile,
  sortItems,
  toggleFavorite,
  moveItem,
  openEdit,
  removeItem,
  ensureProfile,
  renameProfile,
  deleteProfile,
}) {
  return (
    <div className="space-y-4">
      <Card
        title="Archiv"
        icon={Library}
        actions={
          <div className="flex items-center gap-2">
            <select
              className="ui-input rounded-xl px-3 py-2 text-sm"
              value=""
              onChange={(e) => sortItems(activeProfileName, e.target.value)}
              aria-label="Sortieren"
            >
              <option value="" disabled>Sortieren</option>
              <option value="az">A-Z</option>
              <option value="type">Typ + A-Z</option>
              <option value="new">Neu zuerst</option>
              <option value="fav">Favoriten zuerst</option>
            </select>
            <Button tone="primary" onClick={() => exportProfile(activeProfileName)} className="flex items-center gap-2">
              <Download className="h-4 w-4" /> Profil Export
            </Button>
          </div>
        }
      >
        <div className="mb-3 flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap">
            <TonePill tone="blue">Profil: {activeProfileName}</TonePill>
            <TonePill tone="slate">Einträge: {archiveStats.perProfile[activeProfileName]?.total ?? 0}</TonePill>
            <TonePill tone="slate">Favoriten: {archiveStats.perProfile[activeProfileName]?.favorites ?? 0}</TonePill>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm" style={{ color: "var(--muted)" }}>Profil</label>
            <select
              className="ui-input rounded-xl px-3 py-2"
              value={activeProfileName}
              onChange={(e) => {
                const v = e.target.value;
                setActiveProfile(v);
                pushLog("profile", "Aktives Profil gewechselt", { profile: v });
              }}
              aria-label="Profil wählen"
            >
              {profiles.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>

        <QuickInputs addInputs={addInputs} setAddInputs={setAddInputs} onSubmitType={addCommaSeparated} />

        <div className="mt-4">
          <ArchiveTable
            rows={listRows}
            showProfile={true}
            onToggleFav={toggleFavorite}
            onMove={moveItem}
            onEdit={openEdit}
            onDelete={removeItem}
          />
        </div>
      </Card>

      <Card title="Profilverwaltung" icon={FolderPlus}>
        <ProfileManager
          profiles={profiles}
          activeProfileName={activeProfileName}
          onSelect={(p) => { setActiveProfile(p); pushLog("profile", "Aktives Profil gewechselt", { profile: p }); }}
          onCreate={ensureProfile}
          onRename={renameProfile}
          onDelete={deleteProfile}
        />
      </Card>
    </div>
  );
}

export default function App() {
  const [state, setState] = useState(() => {
    const raw = safeLsGet(LS_KEY);
    if (!raw) return makeDefaultState();
    const parsed = safeJsonParse(raw);
    return parsed.ok ? coerceState(parsed.value) : makeDefaultState();
  });

  const stateRef = useRef(state);
  useEffect(() => { stateRef.current = state; }, [state]);

  const [nav, setNav] = useState("dashboard");
  const [globalSearch, setGlobalSearch] = useState("");
  const [addInputs, setAddInputs] = useState({ genre: "", mood: "", style: "" });

  const [editDialog, setEditDialog] = useState({ open: false, itemId: null, profile: null, value: "" });

  const [importText, setImportText] = useState("");
  const fileRef = useRef(null);

  const [generator, setGenerator] = useState({ results: [], error: null, lastCopiedAt: null });
  const [toast, setToast] = useState(null);
  const toastTimerRef = useRef(null);

  const showToast = (text) => {
    setToast({ id: makeId(), text });
    if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 1700);
  };
  useEffect(() => () => { if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current); }, []);

  const pushLog = (type, message, meta = {}) => {
    setState((prev) => {
      const maxLogs = prev.settings?.maxLogs ?? 500;
      const entry = { id: makeId(), at: nowIso(), type, message, meta };
      const nextLogs = [entry, ...(prev.logs || [])].slice(0, maxLogs);
      return { ...prev, logs: nextLogs, updatedAt: nowIso() };
    });
  };

  const scale = state.settings.uiScale ?? DEFAULT_SCALE;
  useCtrlWheelZoom(scale, (updater) => {
    setState((prev) => {
      const next = typeof updater === "function" ? updater(prev.settings.uiScale ?? DEFAULT_SCALE) : updater;
      return { ...prev, settings: { ...prev.settings, uiScale: next }, updatedAt: nowIso() };
    });
  });

  useEffect(() => { applyTheme(state.settings.themeId); }, [state.settings.themeId]);

  const saveTimerRef = useRef(null);
  useEffect(() => {
    if (saveTimerRef.current) window.clearTimeout(saveTimerRef.current);
    saveTimerRef.current = window.setTimeout(() => {
      const snapshot = stateRef.current;
      safeLsSet(LS_KEY, JSON.stringify({ ...snapshot, updatedAt: nowIso() }));
    }, 350);
    return () => { if (saveTimerRef.current) window.clearTimeout(saveTimerRef.current); };
  }, [state]);

  useEffect(() => {
    const minutes = state.settings.autosaveMinutes ?? 10;
    const intervalMs = clamp(minutes, 1, 120) * 60 * 1000;
    const id = window.setInterval(() => {
      const snapshot = stateRef.current;
      const ok = safeLsSet(LS_KEY, JSON.stringify({ ...snapshot, updatedAt: nowIso() }));
      pushLog(ok ? "autosave" : "error", ok ? "Autosave ausgeführt" : "Autosave fehlgeschlagen", { minutes });
    }, intervalMs);
    return () => window.clearInterval(id);
  }, [state.settings.autosaveMinutes]);

  const profiles = useMemo(() => Object.keys(state.profiles).sort((a, b) => a.localeCompare(b)), [state.profiles]);
  const activeProfileName = state.settings.activeProfile;
  const activeProfile = state.profiles[activeProfileName] || state.profiles[profiles[0]];

  const allItems = useMemo(() => {
    const rows = [];
    for (const [pname, p] of Object.entries(state.profiles)) for (const it of p.items || []) rows.push({ ...it, profile: pname });
    return rows;
  }, [state.profiles]);

  const favoritesGlobal = useMemo(() => allItems.filter((x) => !!x.favorite), [allItems]);

  const archiveStats = useMemo(() => {
    const perProfile = {};
    for (const pname of Object.keys(state.profiles)) perProfile[pname] = { genre: 0, mood: 0, style: 0, total: 0, favorites: 0 };
    for (const it of allItems) {
      const b = perProfile[it.profile] || (perProfile[it.profile] = { genre: 0, mood: 0, style: 0, total: 0, favorites: 0 });
      b[it.type] = (b[it.type] || 0) + 1;
      b.total += 1;
      if (it.favorite) b.favorites += 1;
    }
    const total = Object.values(perProfile).reduce((acc, v) => {
      acc.genre += v.genre; acc.mood += v.mood; acc.style += v.style; acc.total += v.total; acc.favorites += v.favorites;
      return acc;
    }, { genre: 0, mood: 0, style: 0, total: 0, favorites: 0 });

    const uniq = { genre: new Set(), mood: new Set(), style: new Set() };
    for (const it of allItems) if (uniq[it.type]) uniq[it.type].add(it.key);
    const uniqueTotal = uniq.genre.size + uniq.mood.size + uniq.style.size;

    return { perProfile, total, uniqueTotal, uniqueByType: { genre: uniq.genre.size, mood: uniq.mood.size, style: uniq.style.size }, duplicatesIgnored: state.stats.duplicatesIgnored };
  }, [allItems, state.profiles, state.stats.duplicatesIgnored]);

  const listViewItems = useMemo(() => {
    const q = normKey(globalSearch);
    let rows = allItems;
    if (nav === "archiv") rows = rows.filter((x) => x.profile === activeProfileName);
    if (q) rows = rows.filter((x) => normKey(x.value).includes(q));
    return rows;
  }, [allItems, globalSearch, nav, activeProfileName]);

  const generatorPool = useMemo(() => {
    const g = state.settings.generator;
    if (state.settings.favoritesOnly) {
      const filtered = favoritesGlobal.filter((x) => g.includeTypes?.[x.type] !== false);
      return dedupeByKey(filtered, (x) => `${x.type}:${x.key}`);
    }
    const base = (activeProfile?.items || []).filter((x) => g.includeTypes?.[x.type] !== false);
    return dedupeByKey(base, (x) => `${x.type}:${x.key}`);
  }, [state.settings.favoritesOnly, state.settings.generator, favoritesGlobal, activeProfile]);

  const bumpStat = (patch) => {
    setState((prev) => ({ ...prev, stats: { ...(prev.stats || {}), ...patch }, updatedAt: nowIso() }));
  };

  const setActiveProfile = (p) => setState((prev) => ({ ...prev, settings: { ...prev.settings, activeProfile: p }, updatedAt: nowIso() }));

  const ensureProfile = (name) => {
    const pname = norm(name);
    if (!pname) { showToast("Profilname fehlt"); return; }
    if (state.profiles[pname]) { showToast("Profil existiert bereits"); return; }
    setState((prev) => {
      if (prev.profiles[pname]) return prev;
      const createdAt = nowIso();
      return {
        ...prev,
        profiles: { ...prev.profiles, [pname]: { createdAt, updatedAt: createdAt, items: [] } },
        settings: { ...prev.settings, activeProfile: pname },
        updatedAt: nowIso(),
      };
    });
    pushLog("profile", "Profil erstellt", { profile: pname });
    showToast(`Profil „${pname}“ erstellt`);
  };

  const renameProfile = (from, to) => {
    const src = norm(from), dst = norm(to);
    if (!src || !dst || src === dst) { showToast("Ungültiger Name"); return; }
    if (!state.profiles[src]) { showToast("Quelle nicht gefunden"); return; }
    if (state.profiles[dst]) { showToast("Zielname existiert bereits"); return; }
    setState((prev) => {
      if (!prev.profiles[src] || prev.profiles[dst]) return prev;
      const { [src]: moving, ...rest } = prev.profiles;
      const nextProfiles = { ...rest, [dst]: { ...moving, updatedAt: nowIso() } };
      const active = prev.settings.activeProfile === src ? dst : prev.settings.activeProfile;
      return { ...prev, profiles: nextProfiles, settings: { ...prev.settings, activeProfile: active }, updatedAt: nowIso() };
    });
    pushLog("profile", "Profil umbenannt", { from: src, to: dst });
    showToast(`Profil umbenannt: ${src} → ${dst}`);
  };

  const deleteProfile = (name) => {
    const pname = norm(name);
    if (!pname) return;
    if (!state.profiles[pname]) { showToast("Profil nicht gefunden"); return; }
    if (Object.keys(state.profiles).length <= 1) { showToast("Mindestens 1 Profil muss bleiben"); return; }
    setState((prev) => {
      const { [pname]: _, ...rest } = prev.profiles;
      const remaining = Object.keys(rest).sort((a, b) => a.localeCompare(b));
      const nextActive = prev.settings.activeProfile === pname ? remaining[0] : prev.settings.activeProfile;
      return { ...prev, profiles: rest, settings: { ...prev.settings, activeProfile: nextActive }, updatedAt: nowIso() };
    });
    pushLog("profile", "Profil gelöscht", { profile: pname });
    showToast(`Profil gelöscht: ${pname}`);
  };

  const addCommaSeparated = (type, raw) => {
    const input = norm(raw);
    if (!input) return;
    const tokens = input.split(",").map((s) => norm(s)).filter(Boolean);
    if (!tokens.length) return;

    const currentProfile = state.profiles[activeProfileName];
    if (!currentProfile) { showToast("Profil nicht verfügbar"); return; }

    const existingKeysNow = new Set((currentProfile.items || []).filter((x) => x.type === type).map((x) => x.key));
    const newOnes = tokens.filter((t) => {
      const k = normKey(t);
      return k && !existingKeysNow.has(k);
    });

    const dupes = tokens.length - newOnes.length;
    if (!newOnes.length) {
      showToast("Nur Duplikate, nichts hinzugefügt");
      pushLog("add", `Keine neuen Einträge (${type})`, { profile: activeProfileName, raw });
      setAddInputs((p) => ({ ...p, [type]: "" }));
      bumpStat({ duplicatesIgnored: Number(state.stats.duplicatesIgnored || 0) + dupes });
      return;
    }

    setState((prev) => {
      const pname = prev.settings.activeProfile;
      const profile = prev.profiles[pname];
      if (!profile) return prev;

      const existingKeys = new Set((profile.items || []).filter((x) => x.type === type).map((x) => x.key));
      const createdAt = nowIso();
      const toAdd = [];
      for (const t of tokens) {
        const k = normKey(t);
        if (!k) continue;
        if (existingKeys.has(k)) continue;
        existingKeys.add(k);
        toAdd.push({ id: makeId(), type, value: t, key: k, favorite: false, createdAt, updatedAt: createdAt });
      }
      if (!toAdd.length) return prev;

      const nextProfile = { ...profile, updatedAt: nowIso(), items: [...(profile.items || []), ...toAdd] };
      return { ...prev, profiles: { ...prev.profiles, [pname]: nextProfile }, updatedAt: nowIso() };
    });

    pushLog("add", `Einträge hinzugefügt (${type})`, { profile: activeProfileName, added: newOnes.length, dupes });
    showToast(`${newOnes.length} hinzugefügt (${type})`);
    bumpStat({
      itemsAdded: Number(state.stats.itemsAdded || 0) + newOnes.length,
      duplicatesIgnored: Number(state.stats.duplicatesIgnored || 0) + dupes,
    });
    setAddInputs((p) => ({ ...p, [type]: "" }));
  };

  const toggleFavorite = (profile, itemId) => {
    setState((prev) => {
      const p = prev.profiles[profile];
      if (!p) return prev;
      const items = (p.items || []).map((it) => it.id === itemId ? { ...it, favorite: !it.favorite, updatedAt: nowIso() } : it);
      return { ...prev, profiles: { ...prev.profiles, [profile]: { ...p, items, updatedAt: nowIso() } }, updatedAt: nowIso() };
    });
    pushLog("favorite", "Favorit umgeschaltet", { profile, itemId });
  };

  const removeItem = (profile, itemId) => {
    setState((prev) => {
      const p = prev.profiles[profile];
      if (!p) return prev;
      const after = (p.items || []).filter((x) => x.id !== itemId);
      return { ...prev, profiles: { ...prev.profiles, [profile]: { ...p, items: after, updatedAt: nowIso() } }, updatedAt: nowIso() };
    });
    pushLog("delete", "Eintrag gelöscht", { profile, itemId });
  };

  const moveItem = (profile, itemId, dir) => {
    setState((prev) => {
      const p = prev.profiles[profile];
      if (!p) return prev;
      const arr = [...(p.items || [])];
      const idx = arr.findIndex((x) => x.id === itemId);
      if (idx < 0) return prev;
      const j = idx + dir;
      if (j < 0 || j >= arr.length) return prev;
      [arr[idx], arr[j]] = [arr[j], arr[idx]];
      return { ...prev, profiles: { ...prev.profiles, [profile]: { ...p, items: arr, updatedAt: nowIso() } }, updatedAt: nowIso() };
    });
    pushLog("order", "Eintrag verschoben", { profile, itemId, dir });
  };

  const sortItems = (profile, by) => {
    setState((prev) => {
      const p = prev.profiles[profile];
      if (!p) return prev;
      const arr = [...(p.items || [])];
      if (by === "az") arr.sort((a, b) => a.value.localeCompare(b.value));
      if (by === "type") arr.sort((a, b) => (a.type + a.value).localeCompare(b.type + b.value));
      if (by === "new") arr.sort((a, b) => (b.createdAt || "").localeCompare(a.createdAt || ""));
      if (by === "fav") arr.sort((a, b) => Number(b.favorite) - Number(a.favorite) || a.value.localeCompare(b.value));
      return { ...prev, profiles: { ...prev.profiles, [profile]: { ...p, items: arr, updatedAt: nowIso() } }, updatedAt: nowIso() };
    });
    pushLog("order", "Liste sortiert", { profile, by });
    showToast("Sortiert");
  };

  const openEdit = (profile, item) => setEditDialog({ open: true, itemId: item.id, profile, value: item.value });

  const saveEdit = () => {
    const newValue = norm(editDialog.value);
    if (!newValue) { showToast("Wert darf nicht leer sein"); return; }
    const p = state.profiles[editDialog.profile];
    if (!p) { showToast("Profil nicht gefunden"); return; }
    const idx = (p.items || []).findIndex((x) => x.id === editDialog.itemId);
    if (idx < 0) { showToast("Eintrag nicht gefunden"); return; }
    const it = p.items[idx];
    const k = normKey(newValue);
    const exists = (p.items || []).some((x) => x.id !== it.id && x.type === it.type && x.key === k);
    if (exists) { showToast("Duplikat im gleichen Typ"); return; }

    setState((prev) => {
      const pp = prev.profiles[editDialog.profile];
      if (!pp) return prev;
      const ii = (pp.items || []).findIndex((x) => x.id === editDialog.itemId);
      if (ii < 0) return prev;
      const nextItems = [...pp.items];
      nextItems[ii] = { ...nextItems[ii], value: newValue, key: k, updatedAt: nowIso() };
      return { ...prev, profiles: { ...prev.profiles, [editDialog.profile]: { ...pp, items: nextItems, updatedAt: nowIso() } }, updatedAt: nowIso() };
    });

    pushLog("edit", "Eintrag bearbeitet", { profile: editDialog.profile, itemId: editDialog.itemId });
    showToast("Gespeichert");
    setEditDialog({ open: false, itemId: null, profile: null, value: "" });
  };

  const formatResults = (items) => {
    const g = state.settings.generator;
    const delim = g.delimiter ?? ", ";
    if (g.showTypeLabels) return items.map((x) => `${x.type}:${x.value}`).join(delim);
    return items.map((x) => x.value).join(delim);
  };

  const runGenerator = () => {
    const g = state.settings.generator;
    const mode = g.mode;
    const pool = generatorPool;

    if (!pool.length) {
      setGenerator((s) => ({ ...s, results: [], error: "Pool leer. Erst Einträge hinzufügen oder Favoriten aktivieren." }));
      pushLog("generator", "Generator: Pool leer", { mode });
      showToast("Pool leer");
      return;
    }

    let picks = [];
    if (mode === "mix") picks = pickUnique(pool, Number(g.count || 0));

    if (mode === "balanced") {
      const types = ["genre", "mood", "style"].filter((t) => g.includeTypes?.[t] !== false);
      const target = clamp(Number(g.count || 0), 0, pool.length);
      const per = types.length ? Math.max(1, Math.floor(target / types.length)) : target;
      const leftover = target - per * types.length;
      const perType = {};
      for (let i = 0; i < types.length; i++) perType[types[i]] = per + (i < leftover ? 1 : 0);
      const out = [];
      for (const t of types) out.push(...pickUnique(pool.filter((x) => x.type === t), perType[t]));
      picks = dedupeByKey(out, (x) => `${x.type}:${x.key}`).slice(0, target);
    }

    if (mode === "perType") {
      const out = [];
      const wanted = g.perType || { genre: 0, mood: 0, style: 0 };
      for (const t of ["genre", "mood", "style"]) {
        if (g.includeTypes?.[t] === false) continue;
        out.push(...pickUnique(pool.filter((x) => x.type === t), Number(wanted[t] || 0)));
      }
      picks = dedupeByKey(out, (x) => `${x.type}:${x.key}`);
    }

    if (mode === "range") {
      const min = clamp(Number(g.range?.min || 0), 0, 999);
      const max = clamp(Number(g.range?.max || 0), min, 999);
      const n = Math.floor(min + Math.random() * (max - min + 1));
      picks = pickUnique(pool, n);
    }

    if (mode === "shuffleAll") picks = pickUnique(pool, pool.length);

    if (mode === "favFirst") {
      const favs = pool.filter((x) => x.favorite);
      const others = pool.filter((x) => !x.favorite);
      const want = clamp(Number(g.count || 0), 0, pool.length);
      const first = pickUnique(favs, Math.min(want, favs.length));
      const remaining = want - first.length;
      const rest = remaining > 0 ? pickUnique(others, remaining) : [];
      picks = [...first, ...rest];
    }

    picks = dedupeByKey(picks, (x) => `${x.type}:${x.key}`);

    setGenerator((s) => ({ ...s, results: picks, error: null }));

    setState((prev) => {
      const stats = prev.stats || {};
      return {
        ...prev,
        stats: {
          ...stats,
          generatorRuns: Number(stats.generatorRuns || 0) + 1,
          lastRunAt: nowIso(),
          lastRunMode: mode,
          lastRunCount: picks.length,
          totalGeneratedTokens: Number(stats.totalGeneratedTokens || 0) + picks.length,
        },
        updatedAt: nowIso(),
      };
    });

    pushLog("generator", "Generator ausgeführt", { mode, count: picks.length, favoritesOnly: state.settings.favoritesOnly, activeProfile: state.settings.activeProfile });
    showToast(`Generiert: ${picks.length}`);
  };

  const copyResults = async () => {
    const txt = formatResults(generator.results || []);
    if (!txt) { showToast("Nichts zu kopieren"); return; }
    try {
      if (!navigator?.clipboard?.writeText) throw new Error("Clipboard API fehlt");
      await navigator.clipboard.writeText(txt);
      setGenerator((s) => ({ ...s, lastCopiedAt: nowIso() }));
      pushLog("clipboard", "Generator-Ergebnis kopiert", { chars: txt.length, items: (generator.results || []).length });
      showToast("Kopiert ✅");
    } catch (e) {
      pushLog("error", "Clipboard fehlgeschlagen", { error: String(e) });
      showToast("Clipboard nicht verfügbar");
    }
  };

  const exportAll = () => {
    const payloadObj = { ...state, exportedAt: nowIso() };
    const v = validateState(payloadObj);
    if (!v.ok) {
      pushLog("error", "Export blockiert: State invalid", { errors: v.errors });
      showToast("Export blockiert: Daten invalid");
      return;
    }
    const payload = JSON.stringify(payloadObj, null, 2);

    const round = safeJsonParse(payload);
    const v2 = round.ok ? validateState(coerceState(round.value)) : { ok: false, errors: ["Roundtrip Parse fehlgeschlagen"] };
    if (!v2.ok) {
      pushLog("error", "Export Roundtrip fehlgeschlagen", { errors: v2.errors });
      showToast("Export Roundtrip FAIL");
      return;
    }

    const fn = `gms-archiv-gesamt_v${APP_VERSION}_${new Date().toISOString().slice(0, 10)}.json`;
    downloadText(fn, payload);
    pushLog("export", "Gesamt-Export erstellt", { bytes: payload.length });
    setState((prev) => ({ ...prev, stats: { ...prev.stats, exports: Number(prev.stats.exports || 0) + 1, lastExportAt: nowIso() }, updatedAt: nowIso() }));
    showToast("Export geladen");
  };

  const exportProfile = (pname) => {
    const p = state.profiles[pname];
    if (!p) { showToast("Profil nicht gefunden"); return; }
    const bundle = { version: 1, exportedAt: nowIso(), profile: pname, data: { ...p, items: (p.items || []).map((x) => normalizeItem(x, x.type)) } };
    const payload = JSON.stringify(bundle, null, 2);

    const round = safeJsonParse(payload);
    if (!round.ok || !round.value?.profile || !round.value?.data) {
      pushLog("error", "Profil-Export Roundtrip fehlgeschlagen", {});
      showToast("Profil-Export FAIL");
      return;
    }

    const fn = `gms-archiv-profil_${pname}_v${APP_VERSION}_${new Date().toISOString().slice(0, 10)}.json`;
    downloadText(fn, payload);
    pushLog("export", "Profil-Export erstellt", { profile: pname, bytes: payload.length });
    setState((prev) => ({ ...prev, stats: { ...prev.stats, exports: Number(prev.stats.exports || 0) + 1, lastExportAt: nowIso() }, updatedAt: nowIso() }));
    showToast("Profil exportiert");
  };

  const importFromText = (mode) => {
    const parsed = safeJsonParse(importText);
    if (!parsed.ok) {
      showToast("Ungültiges JSON");
      pushLog("error", "Import JSON ungültig", { error: String(parsed.error) });
      return;
    }
    const data = parsed.value;

    if (data?.profiles && typeof data.profiles === "object") {
      const incoming = coerceState(data);
      const vin = validateState(incoming);
      if (!vin.ok) {
        showToast("Import blockiert: Daten invalid");
        pushLog("error", "Gesamt-Import invalid", { errors: vin.errors });
        return;
      }

      if (mode === "replace") {
        setState(incoming);
        pushLog("import", "Gesamt-Import (Ersetzen)", { profiles: Object.keys(incoming.profiles).length });
        setState((prev) => ({ ...prev, stats: { ...prev.stats, imports: Number(prev.stats.imports || 0) + 1, lastImportAt: nowIso() }, updatedAt: nowIso() }));
        showToast("Import: ersetzt");
        return;
      }

      setState((prev) => {
        const next = coerceState(prev);
        for (const [pname, p] of Object.entries(incoming.profiles)) {
          if (!next.profiles[pname]) { next.profiles[pname] = p; continue; }
          const existing = next.profiles[pname].items || [];
          const seen = new Set(existing.map((x) => `${x.type}:${x.key}`));
          const add = (p.items || []).map((x) => normalizeItem(x, x?.type)).filter((x) => x.key && x.value && !seen.has(`${x.type}:${x.key}`));
          next.profiles[pname] = { ...next.profiles[pname], items: [...existing, ...add], updatedAt: nowIso() };
        }
        next.updatedAt = nowIso();
        return next;
      });

      pushLog("import", "Gesamt-Import (Merge)", { profiles: Object.keys(incoming.profiles).length });
      setState((prev) => ({ ...prev, stats: { ...prev.stats, imports: Number(prev.stats.imports || 0) + 1, lastImportAt: nowIso() }, updatedAt: nowIso() }));
      showToast("Import: gemerged");
      return;
    }

    if (data?.profile && data?.data) {
      const pname = norm(data.profile);
      const p = data.data;
      if (!pname) { showToast("Profilname fehlt"); return; }

      setState((prev) => {
        const next = coerceState(prev);
        const incomingItems = (Array.isArray(p.items) ? p.items : []).map((x) => normalizeItem(x, x?.type)).filter((x) => x.key && x.value);

        if (mode === "replace") {
          next.profiles[pname] = { createdAt: p.createdAt || nowIso(), updatedAt: nowIso(), items: incomingItems };
        } else {
          if (!next.profiles[pname]) next.profiles[pname] = { createdAt: nowIso(), updatedAt: nowIso(), items: [] };
          const existing = next.profiles[pname].items || [];
          const seen = new Set(existing.map((x) => `${x.type}:${x.key}`));
          const add = incomingItems.filter((x) => !seen.has(`${x.type}:${x.key}`));
          next.profiles[pname] = { ...next.profiles[pname], items: [...existing, ...add], updatedAt: nowIso() };
        }
        next.settings.activeProfile = pname;
        next.updatedAt = nowIso();
        return next;
      });

      pushLog("import", "Profil-Import", { profile: pname, mode });
      setState((prev) => ({ ...prev, stats: { ...prev.stats, imports: Number(prev.stats.imports || 0) + 1, lastImportAt: nowIso() }, updatedAt: nowIso() }));
      showToast("Profil importiert");
      return;
    }

    showToast("Unbekanntes Import-Format");
    pushLog("error", "Import-Format unbekannt", { keys: Object.keys(data || {}) });
  };

  const importFromFile = async (file) => {
    if (!file) return;
    try {
      const text = await file.text();
      setImportText(text);
      pushLog("import", "Import-Datei geladen", { name: file.name, bytes: text.length });
      showToast("Datei geladen");
    } catch (e) {
      pushLog("error", "Datei lesen fehlgeschlagen", { error: String(e) });
      showToast("Dateifehler");
    }
  };

  const runSelfTest = () => {
    const v = validateState(state);
    if (!v.ok) {
      pushLog("diagnose", "Self-Test FAIL", { errors: v.errors });
      showToast("Self-Test FAIL");
      return;
    }
    const payload = JSON.stringify({ ...state, exportedAt: nowIso() });
    const parsed = safeJsonParse(payload);
    const v2 = parsed.ok ? validateState(coerceState(parsed.value)) : { ok: false, errors: ["Parse fail"] };
    if (!v2.ok) {
      pushLog("diagnose", "Self-Test Roundtrip FAIL", { errors: v2.errors });
      showToast("Roundtrip FAIL");
      return;
    }
    pushLog("diagnose", "Self-Test OK", { profiles: profiles.length, items: allItems.length });
    showToast("Self-Test OK");
  };

  const chartAll = useMemo(() => [
    { name: "Genre", value: archiveStats.total.genre },
    { name: "Mood", value: archiveStats.total.mood },
    { name: "Stil", value: archiveStats.total.style },
  ], [archiveStats]);

  const chartProfile = useMemo(() => {
    const p = archiveStats.perProfile[activeProfileName] || { genre: 0, mood: 0, style: 0 };
    return [
      { name: "Genre", value: p.genre },
      { name: "Mood", value: p.mood },
      { name: "Stil", value: p.style },
    ];
  }, [archiveStats, activeProfileName]);

  const setFavoritesOnly = (v) => setState((prev) => ({ ...prev, settings: { ...prev.settings, favoritesOnly: v }, updatedAt: nowIso() }));
  const setThemeId = (id) => setState((prev) => ({ ...prev, settings: { ...prev.settings, themeId: id }, updatedAt: nowIso() }));
  const setGen = (patch) => setState((prev) => ({ ...prev, settings: { ...prev.settings, generator: { ...prev.settings.generator, ...patch } }, updatedAt: nowIso() }));
  const resetScale = () => { setState((prev) => ({ ...prev, settings: { ...prev.settings, uiScale: DEFAULT_SCALE }, updatedAt: nowIso() })); pushLog("ui", "Zoom Reset", {}); showToast("Zoom Reset"); };

  const onResetStorage = () => {
    safeLsRemove(LS_KEY);
    setState(makeDefaultState());
    showToast("Reset");
  };

  const listPreviewRows = useMemo(() => {
    const q = normKey(globalSearch);
    let rows = (activeProfile?.items || []).map((x) => ({ ...x, profile: activeProfileName }));
    if (q) rows = rows.filter((x) => normKey(x.value).includes(q));
    return rows.slice(0, 10);
  }, [activeProfile, activeProfileName, globalSearch]);

  const modalOpen = editDialog.open;

  return (
    <div
      className="min-h-screen w-full"
      style={{
        background:
          "radial-gradient(1200px 700px at 20% 90%, rgba(59,130,246,0.22), rgba(0,0,0,0) 60%), radial-gradient(900px 600px at 85% 80%, rgba(244,63,94,0.18), rgba(0,0,0,0) 55%), radial-gradient(1000px 700px at 55% 30%, rgba(245,158,11,0.16), rgba(0,0,0,0) 55%), linear-gradient(180deg, var(--bg2), var(--bg) 55%, var(--bg))",
        color: "var(--text)",
      }}
    >
      <div
        className="pointer-events-none fixed inset-0 opacity-35"
        style={{
          backgroundImage:
            "radial-gradient(circle at 10% 20%, var(--star) 0 1px, rgba(0,0,0,0) 2px), radial-gradient(circle at 40% 80%, rgba(255,255,255,0.14) 0 1px, rgba(0,0,0,0) 2px), radial-gradient(circle at 70% 35%, rgba(255,255,255,0.12) 0 1px, rgba(0,0,0,0) 2px), radial-gradient(circle at 85% 60%, rgba(255,255,255,0.10) 0 1px, rgba(0,0,0,0) 2px)",
          backgroundSize: "420px 420px",
        }}
      />

      <div className="relative mx-auto max-w-[1500px] pad-page">
        <div className="grid grid-cols-[78px_1fr] gap-4">
          <Sidebar nav={nav} setNav={setNav} />

          <main className="stack-md">
            <Topbar
              globalSearch={globalSearch}
              setGlobalSearch={setGlobalSearch}
              themeId={state.settings.themeId}
              setThemeId={setThemeId}
              favoritesOnly={state.settings.favoritesOnly}
              setFavoritesOnly={setFavoritesOnly}
              scale={scale}
              resetScale={resetScale}
              exportAll={exportAll}
              openImport={() => { setNav("importexport"); showToast("Import/Export geöffnet"); }}
              archiveStats={archiveStats}
              activeProfileName={activeProfileName}
              updatedAt={state.updatedAt}
              pushLog={pushLog}
              showToast={showToast}
            />

            {nav === "dashboard" ? (
              <DashboardView
                state={state}
                activeProfileName={activeProfileName}
                listPreviewRows={listPreviewRows}
                addInputs={addInputs}
                setAddInputs={setAddInputs}
                addCommaSeparated={addCommaSeparated}
                exportProfile={exportProfile}
                setNav={setNav}
                generatorPoolLen={generatorPool.length}
                generator={generator}
                generatorSettings={state.settings.generator}
                setGen={setGen}
                runGenerator={runGenerator}
                copyResults={copyResults}
                formatResults={formatResults}
                pushLog={pushLog}
                showToast={showToast}
                archiveStats={archiveStats}
                profiles={profiles}
                allItemsLen={allItems.length}
                chartAll={chartAll}
                chartProfile={chartProfile}
                toggleFavorite={toggleFavorite}
                moveItem={moveItem}
                openEdit={openEdit}
                removeItem={removeItem}
              />
            ) : null}

            {nav === "archiv" ? (
              <ArchivView
                activeProfileName={activeProfileName}
                profiles={profiles}
                setActiveProfile={setActiveProfile}
                pushLog={pushLog}
                archiveStats={archiveStats}
                listRows={listViewItems}
                addInputs={addInputs}
                setAddInputs={setAddInputs}
                addCommaSeparated={addCommaSeparated}
                exportProfile={exportProfile}
                sortItems={sortItems}
                toggleFavorite={toggleFavorite}
                moveItem={moveItem}
                openEdit={openEdit}
                removeItem={removeItem}
                ensureProfile={ensureProfile}
                renameProfile={renameProfile}
                deleteProfile={deleteProfile}
              />
            ) : null}

            {nav === "generator" ? (
              <div className="glass rounded-xl p-4">
                <GeneratorPanel
                  activeProfileName={activeProfileName}
                  favoritesOnly={state.settings.favoritesOnly}
                  generatorPoolLen={generatorPool.length}
                  generatorResults={generator.results}
                  generatorError={generator.error}
                  lastCopiedAt={generator.lastCopiedAt}
                  settingsGenerator={state.settings.generator}
                  setGen={setGen}
                  runGenerator={runGenerator}
                  copyResults={copyResults}
                  formatResults={formatResults}
                  pushLog={pushLog}
                  showToast={showToast}
                />
              </div>
            ) : null}

            {nav === "importexport" ? (
              <ImportExport
                importText={importText}
                setImportText={setImportText}
                onFilePick={importFromFile}
                onImportMerge={() => importFromText("merge")}
                onImportReplace={() => importFromText("replace")}
                exportAll={exportAll}
                exportProfile={exportProfile}
                activeProfileName={activeProfileName}
                onSelfTest={runSelfTest}
                fileRef={fileRef}
              />
            ) : null}

            {nav === "settings" ? <SettingsPanel onResetStorage={onResetStorage} /> : null}
          </main>
        </div>
      </div>

      {modalOpen ? (
        <div className="fixed inset-0 z-50 grid place-items-center px-4" role="dialog" aria-modal="true" aria-label="Eintrag bearbeiten">
          <div className="absolute inset-0" style={{ background: "rgba(0,0,0,0.55)" }} onClick={() => setEditDialog({ open: false, itemId: null, profile: null, value: "" })} />
          <div className="relative glass rounded-xl w-full max-w-[560px]">
            <div className="px-4 py-3 border-b flex items-center justify-between" style={{ borderColor: "var(--border2)" }}>
              <div className="font-semibold" style={{ color: "var(--text)" }}>Eintrag bearbeiten</div>
              <IconButton label="Schließen" onClick={() => setEditDialog({ open: false, itemId: null, profile: null, value: "" })} tone="secondary">
                <Trash2 className="h-4 w-4" />
              </IconButton>
            </div>
            <div className="px-4 py-4 space-y-2">
              <label className="text-sm font-semibold" style={{ color: "var(--text)" }}>Wert</label>
              <input
                className="ui-input rounded-xl px-3 py-2 w-full"
                value={editDialog.value}
                onChange={(e) => setEditDialog((p) => ({ ...p, value: e.target.value }))}
              />
              <div className="text-xs" style={{ color: "var(--muted2)" }}>
                Duplikate im gleichen Profil+Typ sind nicht erlaubt (Groß/Klein egal).
              </div>
            </div>
            <div className="px-4 py-4 border-t flex items-center justify-end gap-2" style={{ borderColor: "var(--border2)" }}>
              <Button tone="secondary" onClick={() => setEditDialog({ open: false, itemId: null, profile: null, value: "" })}>Abbrechen</Button>
              <Button tone="ok" onClick={saveEdit}>Speichern</Button>
            </div>
          </div>
        </div>
      ) : null}

      {toast ? (
        <div className="fixed bottom-5 right-5 z-50" aria-live="polite" aria-atomic="true">
          <div className="toast rounded-xl px-4 py-3 shadow-[0_20px_70px_rgba(0,0,0,0.55)]">
            <div className="text-sm">{toast.text}</div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
