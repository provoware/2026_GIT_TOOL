import React, { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import {
  Menu,
  Settings,
  Home,
  Boxes,
  Puzzle,
  User,
  Filter,
  Search,
  Plus,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Download,
  Upload,
  Copy,
  Trash2,
  Info,
  X,
  Star,
  StarOff,
  Sun,
  Moon,
  Sparkles,
  StickyNote,
} from "lucide-react";

/**
 * Projekt-Dashboard Tool (robust für ~1000 Einträge)
 * - Keine TZ-Fallen: Datum-Strings werden ohne Date-Parsen formatiert
 * - Suche optimiert: normalisierte Suchstrings werden einmalig pro entries-Change gebaut
 * - Persistenz robust: localStorage Zugriff ist abgesichert (try/catch) + beforeunload Save
 * - Autosave: periodisch alle 10 Minuten
 */

type EntryType = "Fund" | "Studie" | "Theorie" | "Quelle";

type Entry = {
  id: string;
  title: string;
  date: string; // ISO YYYY-MM-DD
  category: string;
  comment: string;
  sourceUrl: string;
  type: EntryType;
};

type ThemeMode = "auto" | "hell" | "dunkel";

type ResolvedTheme = "hell" | "dunkel";

type QuickNote = {
  id: string;
  text: string;
  createdAt: number;
};

type AppStateV1 = {
  v: 1;
  entries: Entry[];
  selectedTypes: EntryType[];
  tagMode: "Alle" | EntryType;
  monthKey: string; // YYYY-MM
  favoriteModules: string[];
  quickNotes: QuickNote[];
  themeMode: ThemeMode;
};

type TypeMeta = {
  label: EntryType;
  key: EntryType;
  chip: string;
  glow: string;
  ring: string;
  icon: React.ReactNode;
};

type UiError = {
  title: string;
  explanation: string;
  solution: string;
};

type ModuleItem = {
  id: string;
  label: string;
  description: string;
  keywords: string[];
  target: "dashboard" | "extensions" | "plugins" | "data" | "help";
};

type QuickAction = {
  id: string;
  label: string;
  description: string;
  keywords: string[];
};

const STORAGE_KEY = "provoware.projekt-dashboard.v1";
const AUTOSAVE_EVERY_MS = 10 * 60 * 1000;

const TYPE_META: Record<EntryType, TypeMeta> = {
  Fund: {
    label: "Fund",
    key: "Fund",
    chip: "bg-blue-500/30 border-blue-300/40 text-blue-100 hover:bg-blue-500/40",
    glow: "shadow-[0_0_28px_rgba(59,130,246,0.45)]",
    ring: "ring-blue-300/50",
    icon: <span aria-hidden className="inline-block size-2.5 rounded-sm bg-blue-400/90" />,
  },
  Studie: {
    label: "Studie",
    key: "Studie",
    chip:
      "bg-emerald-500/30 border-emerald-300/40 text-emerald-100 hover:bg-emerald-500/40",
    glow: "shadow-[0_0_28px_rgba(16,185,129,0.45)]",
    ring: "ring-emerald-300/50",
    icon: (
      <span aria-hidden className="inline-block size-2.5 rounded-sm bg-emerald-400/90" />
    ),
  },
  Theorie: {
    label: "Theorie",
    key: "Theorie",
    chip:
      "bg-amber-500/30 border-amber-300/40 text-amber-100 hover:bg-amber-500/40",
    glow: "shadow-[0_0_28px_rgba(245,158,11,0.45)]",
    ring: "ring-amber-300/50",
    icon: <span aria-hidden className="inline-block size-2.5 rounded-sm bg-amber-400/90" />,
  },
  Quelle: {
    label: "Quelle",
    key: "Quelle",
    chip: "bg-rose-500/30 border-rose-300/40 text-rose-100 hover:bg-rose-500/40",
    glow: "shadow-[0_0_28px_rgba(244,63,94,0.45)]",
    ring: "ring-rose-300/50",
    icon: <span aria-hidden className="inline-block size-2.5 rounded-sm bg-rose-400/90" />,
  },
};

const MODULE_ITEMS: ModuleItem[] = [
  {
    id: "dashboard",
    label: "Übersicht",
    description: "Projekt-Dashboard mit Einträgen, Timeline und Filtern.",
    keywords: ["dashboard", "übersicht", "einträge", "timeline"],
    target: "dashboard",
  },
  {
    id: "extensions",
    label: "Erweiterungen",
    description: "Zusatzfunktionen und optionale Features im Überblick.",
    keywords: ["erweiterung", "zusatz", "funktionen"],
    target: "extensions",
  },
  {
    id: "plugins",
    label: "Zusatzmodule",
    description: "Module verwalten und starten.",
    keywords: ["modul", "plugin", "zusatzmodul"],
    target: "plugins",
  },
  {
    id: "data",
    label: "Daten & Export",
    description: "Export, Import und Backup-Optionen.",
    keywords: ["daten", "export", "import", "backup"],
    target: "data",
  },
  {
    id: "help",
    label: "Hilfe",
    description: "Kurze Hilfe mit Tipps und Erklärungen.",
    keywords: ["hilfe", "faq", "tipps"],
    target: "help",
  },
];

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: "action-export",
    label: "Export öffnen",
    description: "Öffnet den Export/Import-Dialog.",
    keywords: ["export", "download", "daten"],
  },
  {
    id: "action-backup",
    label: "Backup herunterladen",
    description: "Speichert ein Backup als JSON-Datei.",
    keywords: ["backup", "sicherung", "download"],
  },
  {
    id: "action-new-entry",
    label: "Neuen Eintrag anlegen",
    description: "Springt zum Formular für einen neuen Eintrag.",
    keywords: ["neu", "eintrag", "formular"],
  },
];

const DEFAULT_FAVORITE_MODULES = ["dashboard", "data"];
const DEFAULT_THEME_MODE: ThemeMode = "auto";

const uid = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? // @ts-ignore
      crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

function clamp(n: number, a: number, b: number) {
  return Math.min(b, Math.max(a, n));
}

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

function toYMD(d: Date) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

const DATE_FORMAT_REGEX = /^\d{4}-\d{2}-\d{2}$/;
const DATE_FORMAT_HINT = "JJJJ-MM-TT (z. B. 2026-01-07)";

function isYMD(ymd: string) {
  return DATE_FORMAT_REGEX.test(ymd);
}

function isMonthKey(mk: string) {
  return /^\d{4}-\d{2}$/.test(mk);
}

function monthKeyFromYMD(ymd: string) {
  return isYMD(ymd) ? ymd.slice(0, 7) : toYMD(new Date()).slice(0, 7);
}

function dayOfMonthFromYMD(ymd: string) {
  if (!isYMD(ymd)) return 1;
  const d = Number(ymd.slice(8, 10));
  return Number.isFinite(d) && d >= 1 && d <= 31 ? d : 1;
}

function formatDE(ymd: string) {
  if (!isYMD(ymd)) return "–";
  return `${ymd.slice(8, 10)}.${ymd.slice(5, 7)}.${ymd.slice(0, 4)}`;
}

function monthLabelDE(monthKey: string) {
  const mk = isMonthKey(monthKey) ? monthKey : toYMD(new Date()).slice(0, 7);
  const y = Number(mk.slice(0, 4));
  const m = Number(mk.slice(5, 7));
  const date = new Date(y, (m || 1) - 1, 1);
  const months = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
  ];
  return `${months[date.getMonth()]} ${date.getFullYear()}`;
}

function addMonths(monthKey: string, delta: number) {
  const mk = isMonthKey(monthKey) ? monthKey : toYMD(new Date()).slice(0, 7);
  const y = Number(mk.slice(0, 4));
  const m = Number(mk.slice(5, 7));
  const d = new Date(y, (m || 1) - 1 + delta, 1);
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}`;
}

function daysInMonth(year: number, monthIndex0: number) {
  return new Date(year, monthIndex0 + 1, 0).getDate();
}

function ensureUrlLike(input: string) {
  const s = input.trim();
  if (!s) return "";
  if (/^https?:\/\//i.test(s)) return s;
  if (/^[\w.-]+\.[a-z]{2,}(\/.*)?$/i.test(s)) return `https://${s}`;
  return s;
}

function safeJsonParse<T>(
  s: string
): { ok: true; value: T } | { ok: false; error: string } {
  try {
    const value = JSON.parse(s);
    return { ok: true, value };
  } catch (_e: any) {
    return { ok: false, error: "Ungültiges JSON" };
  }
}

function formatErrorMessage({ title, explanation, solution }: UiError) {
  return `Titel: ${title}. Erklärung: ${explanation} Lösung: ${solution}`;
}

function importErrorFor(reason: string): UiError {
  const base = {
    title: "Import nicht möglich",
    solution: "Bitte eine exportierte JSON-Datei (Datenformat) verwenden und erneut importieren.",
  };

  switch (reason) {
    case "Kein Objekt":
      return {
        ...base,
        explanation:
          "Die Datei enthält kein JSON-Objekt (Datenpaket) für dieses Tool.",
      };
    case "Falsche Version":
      return {
        ...base,
        explanation:
          "Die Datei passt nicht zur erwarteten Version des Tools.",
      };
    case "Einträge fehlen":
      return {
        ...base,
        explanation:
          "In der Datei fehlen die Einträge, die für den Import nötig sind.",
      };
    case "Ungültiges JSON":
      return {
        ...base,
        explanation:
          "Die Datei ist kein gültiges JSON (Datenformat) und kann nicht gelesen werden.",
      };
    default:
      return {
        ...base,
        explanation:
          "Die Datei hat nicht das erwartete Format oder enthält unvollständige Daten.",
      };
  }
}

function downloadText(filename: string, text: string) {
  const blob = new Blob([text], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function classNames(...xs: Array<string | false | null | undefined>) {
  return xs.filter(Boolean).join(" ");
}

function normalizeText(s: string) {
  return (s || "").trim().toLowerCase();
}

function safeLocalStorageGet(key: string) {
  try {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeLocalStorageSet(key: string, value: string) {
  try {
    if (typeof window === "undefined") return false;
    window.localStorage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

function safeLocalStorageRemove(key: string) {
  try {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

function resolveTheme(mode: ThemeMode, prefersDark: boolean): ResolvedTheme {
  if (mode === "auto") return prefersDark ? "dunkel" : "hell";
  return mode === "dunkel" ? "dunkel" : "hell";
}

function normalizeNoteText(input: string) {
  return input.replace(/\s+/g, " ").trim();
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!mq) return;
    const onChange = () => setReduced(!!mq.matches);
    onChange();
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);
  return reduced;
}

function usePrefersDarkMode() {
  const [prefersDark, setPrefersDark] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return;
    const onChange = () => setPrefersDark(!!mq.matches);
    onChange();
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);
  return prefersDark;
}

function useIntervalAutosave<T>(
  getValue: () => T,
  onSave: (v: T) => void,
  everyMs: number
): { lastSavedAt: number | null; saving: boolean } {
  const [lastSavedAt, setLastSavedAt] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  const onSaveRef = useRef(onSave);
  const getValueRef = useRef(getValue);
  useEffect(() => {
    onSaveRef.current = onSave;
    getValueRef.current = getValue;
  }, [onSave, getValue]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    let mounted = true;

    const tick = () => {
      if (!mounted) return;
      setSaving(true);
      try {
        onSaveRef.current(getValueRef.current());
        setLastSavedAt(Date.now());
      } finally {
        setSaving(false);
      }
    };

    const id = window.setInterval(tick, everyMs);

    const onBeforeUnload = () => {
      try {
        onSaveRef.current(getValueRef.current());
      } catch {
        // ignore
      }
    };

    window.addEventListener("beforeunload", onBeforeUnload);

    return () => {
      mounted = false;
      window.clearInterval(id);
      window.removeEventListener("beforeunload", onBeforeUnload);
    };
  }, [everyMs]);

  return { lastSavedAt, saving };
}

function GlassCard({
  title,
  children,
  className,
  actions,
  as,
  ariaLabel,
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
  actions?: React.ReactNode;
  as?: "section" | "div" | "aside";
  ariaLabel?: string;
}) {
  const Comp: any = as || "section";
  return (
    <Comp
      aria-label={ariaLabel}
      className={classNames(
        "rounded-2xl border border-white/12 bg-slate-950/45 backdrop-blur-2xl",
        "shadow-[0_22px_65px_rgba(0,0,0,0.6)] ring-1 ring-white/8",
        className
      )}
    >
      {(title || actions) && (
        <div className="flex items-center justify-between gap-3 px-4 pt-4">
          {title ? (
            <h2 className="text-sm font-semibold tracking-wide text-white/85">{title}</h2>
          ) : (
            <div />
          )}
          {actions}
        </div>
      )}
      <div className="p-4">{children}</div>
    </Comp>
  );
}

function IconButton({
  label,
  onClick,
  children,
  active,
  className,
  ariaCurrent,
}: {
  label: string;
  onClick?: () => void;
  children: React.ReactNode;
  active?: boolean;
  className?: string;
  ariaCurrent?: boolean;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-current={ariaCurrent ? "page" : undefined}
      onClick={onClick}
      className={classNames(
        "inline-flex items-center justify-center rounded-xl border border-white/12",
        "bg-slate-900/45 hover:bg-slate-900/60 active:bg-slate-900/70",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90",
        "transition",
        active && "bg-blue-500/15 border-blue-300/25",
        className
      )}
    >
      {children}
    </button>
  );
}

function ChipToggle({
  label,
  meta,
  pressed,
  onToggle,
  dense,
}: {
  label: string;
  meta: TypeMeta;
  pressed: boolean;
  onToggle: () => void;
  dense?: boolean;
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onToggle}
      className={classNames(
        "inline-flex items-center gap-2 rounded-xl border px-3",
        dense ? "py-1.5 text-xs" : "py-2 text-sm",
        "transition",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90",
        pressed ? meta.chip : "bg-slate-900/45 border-white/12 text-white/80 hover:bg-slate-900/60"
      )}
    >
      <span className="inline-flex items-center">{meta.icon}</span>
      <span className="font-medium">{label}</span>
      <span
        aria-hidden
        className={classNames(
          "ml-1 size-2 rounded-full",
          pressed ? "bg-white/55" : "bg-white/18"
        )}
      />
    </button>
  );
}

function LabeledField({
  label,
  htmlFor,
  hint,
  children,
  describedById,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  children: React.ReactNode;
  describedById?: string;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="text-xs font-semibold text-white/80">
        {label}
      </label>
      {children}
      {hint ? (
        <p id={describedById} className="text-[11px] text-white/50">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={classNames(
        "w-full rounded-xl border border-white/15 bg-slate-950/60 px-3 py-2 text-sm text-white/92",
        "placeholder:text-white/40",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90",
        "transition",
        props.className
      )}
    />
  );
}

function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={classNames(
        "w-full rounded-xl border border-white/15 bg-slate-950/60 px-3 py-2 text-sm text-white/92",
        "placeholder:text-white/40",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90",
        "transition",
        props.className
      )}
    />
  );
}

function Select({
  value,
  onChange,
  options,
  id,
  describedBy,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  options: Array<{ value: string; label: string }>;
  describedBy?: string;
}) {
  return (
    <div className="relative">
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-describedby={describedBy}
        className="w-full appearance-none rounded-xl border border-white/15 bg-slate-950/60 px-3 py-2 pr-10 text-sm text-white/92 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value} className="bg-zinc-900">
            {o.label}
          </option>
        ))}
      </select>
      <span
        aria-hidden
        className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-white/55"
      >
        ▾
      </span>
    </div>
  );
}

function SidebarNav({
  active,
  onActive,
}: {
  active: "dashboard" | "extensions" | "plugins";
  onActive: (k: "dashboard" | "extensions" | "plugins") => void;
}) {
  return (
    <aside
      aria-label="Seitenleiste"
      className={classNames(
        "w-[88px] shrink-0",
        "rounded-2xl border border-white/12 bg-slate-950/45 backdrop-blur-2xl",
        "shadow-[0_22px_65px_rgba(0,0,0,0.6)] ring-1 ring-white/8",
        "overflow-hidden"
      )}
    >
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-center px-3 py-4">
          <IconButton label="Menü" className="h-12 w-12">
            <Menu className="h-5 w-5 text-white/90" />
          </IconButton>
        </div>

        <nav aria-label="Navigation" className="flex-1 px-3 pb-3">
          <div className="space-y-3">
            <SideItem
              icon={<Settings className="h-5 w-5" />}
              label=""
              sub=""
              active={false}
              onClick={() => {}}
              ariaLabel="Einstellungen"
              compact
            />

            <div className="space-y-3">
              <SideItem
                icon={<Home className="h-5 w-5" />}
                label="Übersicht"
                sub=""
                active={active === "dashboard"}
                onClick={() => onActive("dashboard")}
                ariaLabel="Übersicht"
              />
              <SideItem
                icon={<Boxes className="h-5 w-5" />}
                label="Erweiterungen"
                sub=""
                active={active === "extensions"}
                onClick={() => onActive("extensions")}
                ariaLabel="Erweiterungen"
              />
              <SideItem
                icon={<Puzzle className="h-5 w-5" />}
                label="Zusatzmodule"
                sub=""
                active={active === "plugins"}
                onClick={() => onActive("plugins")}
                ariaLabel="Zusatzmodule"
              />
            </div>
          </div>
        </nav>

        <div className="px-3 pb-4">
          <IconButton label="Profil" className="h-12 w-full">
            <User className="h-5 w-5 text-white/90" />
          </IconButton>
        </div>
      </div>
    </aside>
  );
}

function SideItem({
  icon,
  label,
  sub,
  active,
  onClick,
  ariaLabel,
}: {
  icon: React.ReactNode;
  label: string;
  sub: string;
  active: boolean;
  onClick: () => void;
  ariaLabel: string;
  compact?: boolean;
}) {
  return (
    <button
      type="button"
      aria-label={ariaLabel}
      aria-current={active ? "page" : undefined}
      onClick={onClick}
      className={classNames(
        "group w-full rounded-2xl border border-white/12 bg-slate-900/45",
        "hover:bg-slate-900/60 active:bg-slate-900/70",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90",
        "transition",
        active && "bg-blue-500/15 border-blue-300/25"
      )}
    >
      <div className="flex flex-col items-center gap-2 py-3">
        <div
          className={classNames(
            "flex h-10 w-10 items-center justify-center rounded-2xl",
            active ? "bg-blue-500/15" : "bg-black/15",
            "text-white/90"
          )}
        >
          {icon}
        </div>
        {label ? (
          <div className="text-center">
            <div
              className={classNames(
                "text-[11px] font-semibold",
                active ? "text-blue-100" : "text-white/80"
              )}
            >
              {label}
            </div>
            {sub ? <div className="text-[10px] text-white/45">{sub}</div> : null}
          </div>
        ) : null}
      </div>
    </button>
  );
}

function StatusPill({
  saving,
  lastSavedAt,
}: {
  saving: boolean;
  lastSavedAt: number | null;
}) {
  const text = saving
    ? "Speichert…"
    : lastSavedAt
    ? `Gespeichert: ${new Date(lastSavedAt).toLocaleTimeString()}`
    : "Noch nicht gespeichert";

  return (
    <div
      role="status"
      aria-live="polite"
      className={classNames(
        "hidden md:inline-flex items-center gap-2 rounded-xl border border-white/12 bg-slate-900/45",
        "px-3 py-2 text-xs text-white/75"
      )}
    >
      <span
        aria-hidden
        className={classNames(
          "size-2 rounded-full",
          saving ? "bg-amber-300/70" : "bg-emerald-300/70"
        )}
      />
      {text}
    </div>
  );
}

function TopBar({
  projectName,
  view,
  onView,
  search,
  onSearch,
  onOpenData,
  onOpenHelp,
  onCreateProject,
  saving,
  lastSavedAt,
}: {
  projectName: string;
  view: "Alle Einträge" | "Filter";
  onView: (v: "Alle Einträge" | "Filter") => void;
  search: string;
  onSearch: (v: string) => void;
  onOpenData: () => void;
  onOpenHelp: () => void;
  onCreateProject: () => void;
  saving: boolean;
  lastSavedAt: number | null;
}) {
  const searchId = useId();

  return (
    <header
      className={classNames(
        "rounded-2xl border border-white/12 bg-slate-950/45 backdrop-blur-2xl",
        "shadow-[0_22px_65px_rgba(0,0,0,0.6)] ring-1 ring-white/8",
        "px-4 py-3"
      )}
    >
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-wide text-white/92">{projectName}</h1>

        <div className="ml-0 md:ml-2 flex items-center gap-2">
          <button
            type="button"
            onClick={() => onView("Alle Einträge")}
            className={classNames(
              "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90",
              view === "Alle Einträge"
                ? "border-blue-300/25 bg-blue-500/20 text-blue-100"
                : "border-white/12 bg-slate-900/45 text-white/80 hover:bg-slate-900/60"
            )}
          >
            <User className="h-4 w-4" aria-hidden />
            Alle Einträge
          </button>
          <button
            type="button"
            onClick={() => onView("Filter")}
            className={classNames(
              "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90",
              view === "Filter"
                ? "border-white/20 bg-slate-900/60 text-white/92"
                : "border-white/12 bg-slate-900/45 text-white/80 hover:bg-slate-900/60"
            )}
          >
            <Filter className="h-4 w-4" aria-hidden />
            Filter
          </button>
        </div>

        <div className="flex-1" />

        <div className="relative w-full md:w-[520px] md:max-w-[48vw]">
          <label htmlFor={searchId} className="sr-only">
            Suche
          </label>
          <Search
            aria-hidden
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/55"
          />
          <input
            id={searchId}
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Suche: Titel, Kategorie, Kommentar, URL"
            className={classNames(
              "w-full rounded-xl border border-white/15 bg-slate-950/60 pl-10 pr-3 py-2 text-sm text-white/92",
              "placeholder:text-white/40",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
            )}
          />
        </div>

        <StatusPill saving={saving} lastSavedAt={lastSavedAt} />

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCreateProject}
            className={classNames(
              "inline-flex items-center gap-2 rounded-xl border border-white/12",
              "bg-blue-500/25 px-3 py-2 text-sm text-blue-100 hover:bg-blue-500/35",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
            )}
          >
            <Plus className="h-4 w-4" aria-hidden />
            Projekt
          </button>
          <button
            type="button"
            onClick={onOpenHelp}
            className={classNames(
              "inline-flex items-center gap-2 rounded-xl border border-white/12 bg-slate-900/45",
              "px-3 py-2 text-sm text-white/85 hover:bg-slate-900/60",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
            )}
          >
            <Info className="h-4 w-4" aria-hidden />
            Hilfe
          </button>

          <button
            type="button"
            onClick={onOpenData}
            className={classNames(
              "inline-flex items-center gap-2 rounded-xl border border-white/12 bg-slate-900/45",
              "px-3 py-2 text-sm text-white/85 hover:bg-slate-900/60",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
            )}
          >
            <Download className="h-4 w-4" aria-hidden />
            Daten
          </button>

          <IconButton label="Einstellungen" className="h-10 w-10">
            <Settings className="h-5 w-5 text-white/90" />
          </IconButton>
        </div>
      </div>
    </header>
  );
}

function FavoritesPanel({
  favorites,
  onSelectModule,
  onToggleFavorite,
}: {
  favorites: Set<string>;
  onSelectModule: (target: ModuleItem["target"]) => void;
  onToggleFavorite: (id: string) => void;
}) {
  const favoriteItems = MODULE_ITEMS.filter((item) => favorites.has(item.id));

  return (
    <GlassCard title="Favoriten & Module" ariaLabel="Favoritenleiste">
      <div className="space-y-4">
        <div>
          <p className="text-xs text-white/55">Schnellzugriff auf oft genutzte Module.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {favoriteItems.length ? (
              favoriteItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectModule(item.target)}
                  className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/85 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
                >
                  <Star className="h-4 w-4 text-amber-200" aria-hidden />
                  {item.label}
                </button>
              ))
            ) : (
              <p className="text-xs text-white/55">
                Noch keine Favoriten. Bitte unten Module markieren.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/20 p-3">
          <p className="text-xs font-semibold text-white/80">Module</p>
          <div className="mt-3 space-y-2">
            {MODULE_ITEMS.map((item) => {
              const isFavorite = favorites.has(item.id);
              return (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2"
                >
                  <button
                    type="button"
                    onClick={() => onSelectModule(item.target)}
                    className="text-left"
                  >
                    <div className="text-sm font-semibold text-white/90">{item.label}</div>
                    <div className="text-xs text-white/55">{item.description}</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => onToggleFavorite(item.id)}
                    className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/70 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
                    aria-pressed={isFavorite}
                    aria-label={
                      isFavorite
                        ? `Favorit entfernen: ${item.label}`
                        : `Als Favorit markieren: ${item.label}`
                    }
                  >
                    {isFavorite ? (
                      <Star className="h-4 w-4 text-amber-200" aria-hidden />
                    ) : (
                      <StarOff className="h-4 w-4" aria-hidden />
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

function GlobalSearchPanel({
  value,
  onChange,
  results,
  onSelectEntry,
  onSelectModule,
  onSelectAction,
  onSelectNote,
}: {
  value: string;
  onChange: (v: string) => void;
  results: {
    entries: Entry[];
    modules: ModuleItem[];
    actions: QuickAction[];
    notes: QuickNote[];
  };
  onSelectEntry: (entry: Entry) => void;
  onSelectModule: (target: ModuleItem["target"]) => void;
  onSelectAction: (actionId: QuickAction["id"]) => void;
  onSelectNote: (note: QuickNote) => void;
}) {
  const searchId = useId();
  const hasQuery = value.trim().length > 0;
  const empty =
    hasQuery &&
    !results.entries.length &&
    !results.modules.length &&
    !results.actions.length &&
    !results.notes.length;

  return (
    <GlassCard
      title="Globale Suche"
      ariaLabel="Globale Suche"
      actions={
        <button
          type="button"
          onClick={() => onChange("")}
          className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs text-white/70 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
        >
          <X className="h-3 w-3" aria-hidden />
          Zurücksetzen
        </button>
      }
    >
      <div className="space-y-4">
        <div className="relative">
          <label htmlFor={searchId} className="sr-only">
            Globale Suche
          </label>
          <Search
            aria-hidden
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/55"
          />
          <input
            id={searchId}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Suche: Module, Einträge, Aktionen, Notizen"
            className="w-full rounded-xl border border-white/12 bg-black/25 py-2 pl-10 pr-3 text-sm text-white/92 placeholder:text-white/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
          />
        </div>

        {empty ? <p className="text-xs text-white/55">Keine Treffer gefunden.</p> : null}

        {!hasQuery ? (
          <p className="text-xs text-white/55">
            Tipp: Suche nach „Export“, „Module“, „Fund“ oder „Notiz“.
          </p>
        ) : null}

        {results.modules.length ? (
          <div>
            <p className="text-xs font-semibold text-white/80">Module</p>
            <div className="mt-2 space-y-2">
              {results.modules.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectModule(item.target)}
                  className="flex w-full items-start justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left text-sm text-white/85 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
                >
                  <span>
                    <span className="block font-semibold">{item.label}</span>
                    <span className="block text-xs text-white/55">{item.description}</span>
                  </span>
                  <Sparkles className="mt-1 h-4 w-4 text-amber-200" aria-hidden />
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {results.actions.length ? (
          <div>
            <p className="text-xs font-semibold text-white/80">Aktionen</p>
            <div className="mt-2 space-y-2">
              {results.actions.map((action) => (
                <button
                  key={action.id}
                  type="button"
                  onClick={() => onSelectAction(action.id)}
                  className="flex w-full items-start justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left text-sm text-white/85 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
                >
                  <span>
                    <span className="block font-semibold">{action.label}</span>
                    <span className="block text-xs text-white/55">{action.description}</span>
                  </span>
                  <Sparkles className="mt-1 h-4 w-4 text-amber-200" aria-hidden />
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {results.entries.length ? (
          <div>
            <p className="text-xs font-semibold text-white/80">Einträge</p>
            <div className="mt-2 space-y-2">
              {results.entries.map((entry) => (
                <button
                  key={entry.id}
                  type="button"
                  onClick={() => onSelectEntry(entry)}
                  className="flex w-full items-start justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left text-sm text-white/85 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
                >
                  <span>
                    <span className="block font-semibold">{entry.title}</span>
                    <span className="block text-xs text-white/55">
                      {formatDE(entry.date)} · {entry.type}
                    </span>
                  </span>
                  <span className="text-xs text-white/55">Öffnen</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {results.notes.length ? (
          <div>
            <p className="text-xs font-semibold text-white/80">Notizen</p>
            <div className="mt-2 space-y-2">
              {results.notes.map((note) => (
                <button
                  key={note.id}
                  type="button"
                  onClick={() => onSelectNote(note)}
                  className="flex w-full items-start justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left text-sm text-white/85 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
                >
                  <span>
                    <span className="block font-semibold">Notiz</span>
                    <span className="block text-xs text-white/55">{note.text}</span>
                  </span>
                  <StickyNote className="mt-1 h-4 w-4 text-amber-200" aria-hidden />
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </GlassCard>
  );
}

function QuickActionsPanel({
  onOpenData,
  onBackup,
  noteDraft,
  onNoteDraft,
  notes,
  onAddNote,
  onRemoveNote,
  themeMode,
  onThemeMode,
}: {
  onOpenData: () => void;
  onBackup: () => void;
  noteDraft: string;
  onNoteDraft: (v: string) => void;
  notes: QuickNote[];
  onAddNote: () => void;
  onRemoveNote: (id: string) => void;
  themeMode: ThemeMode;
  onThemeMode: (mode: ThemeMode) => void;
}) {
  const noteInputId = useId();
  return (
    <GlassCard title="Schnellaktionen" ariaLabel="Schnellaktionen">
      <div className="space-y-4">
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <p className="text-xs font-semibold text-white/80">Export & Backup</p>
          <p className="mt-1 text-xs text-white/55">
            Für schnelle Sicherungen und Datentransfer.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onOpenData}
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/85 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
            >
              <Download className="h-4 w-4" aria-hidden />
              Export öffnen
            </button>
            <button
              type="button"
              onClick={onBackup}
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/85 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
            >
              <Download className="h-4 w-4" aria-hidden />
              Backup speichern
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <p className="text-xs font-semibold text-white/80">Theme</p>
          <p className="mt-1 text-xs text-white/55">
            Auto passt sich an Tag/Nacht an.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onThemeMode("auto")}
              className={classNames(
                "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm",
                themeMode === "auto"
                  ? "border-amber-200/60 bg-amber-500/15 text-amber-100"
                  : "border-white/10 bg-white/5 text-white/80 hover:bg-white/10"
              )}
            >
              <Sparkles className="h-4 w-4" aria-hidden />
              Auto
            </button>
            <button
              type="button"
              onClick={() => onThemeMode("hell")}
              className={classNames(
                "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm",
                themeMode === "hell"
                  ? "border-amber-200/60 bg-amber-500/15 text-amber-100"
                  : "border-white/10 bg-white/5 text-white/80 hover:bg-white/10"
              )}
            >
              <Sun className="h-4 w-4" aria-hidden />
              Hell
            </button>
            <button
              type="button"
              onClick={() => onThemeMode("dunkel")}
              className={classNames(
                "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm",
                themeMode === "dunkel"
                  ? "border-amber-200/60 bg-amber-500/15 text-amber-100"
                  : "border-white/10 bg-white/5 text-white/80 hover:bg-white/10"
              )}
            >
              <Moon className="h-4 w-4" aria-hidden />
              Dunkel
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <p className="text-xs font-semibold text-white/80">Notizen</p>
          <label htmlFor={noteInputId} className="sr-only">
            Schnellnotiz
          </label>
          <TextArea
            id={noteInputId}
            rows={3}
            value={noteDraft}
            onChange={(e) => onNoteDraft(e.target.value)}
            placeholder="Kurze Notiz (max. 200 Zeichen)"
            aria-label="Schnellnotiz"
          />
          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="text-xs text-white/55">
              {noteDraft.trim().length}/200 Zeichen
            </span>
            <button
              type="button"
              onClick={onAddNote}
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/85 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
            >
              <StickyNote className="h-4 w-4" aria-hidden />
              Notiz speichern
            </button>
          </div>
          {notes.length ? (
            <ul className="mt-3 space-y-2">
              {notes.slice(0, 3).map((note) => (
                <li
                  key={note.id}
                  className="flex items-start justify-between gap-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white/85"
                >
                  <span>{note.text}</span>
                  <button
                    type="button"
                    onClick={() => onRemoveNote(note.id)}
                    className="text-xs text-white/55 hover:text-white"
                    aria-label="Notiz entfernen"
                  >
                    Entfernen
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-xs text-white/55">Noch keine Notizen gespeichert.</p>
          )}
        </div>
      </div>
    </GlassCard>
  );
}

function LeftEntryPanel({
  onAdd,
  defaultDate,
  announce,
}: {
  onAdd: (e: Omit<Entry, "id">) => void;
  defaultDate: string;
  announce: (msg: string) => void;
}) {
  const dateId = useId();
  const catId = useId();
  const typeId = useId();
  const commentId = useId();
  const urlId = useId();

  const catHintId = useId();
  const urlHintId = useId();
  const commentHintId = useId();

  const [date, setDate] = useState(defaultDate);
  const [category, setCategory] = useState("");
  const [type, setType] = useState<EntryType>("Fund");
  const [comment, setComment] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [error, setError] = useState<UiError | null>(null);

  function submit() {
    setError(null);

    if (!date || !isYMD(date)) {
      const msg = `Datum fehlt oder ist falsch. Bitte ${DATE_FORMAT_HINT}.`;
      setError(msg);
      announce(`Fehler: ${msg}`);
      const dateError: UiError = {
        title: "Ungültiges Datum",
        explanation: "Das Datum fehlt oder hat kein gültiges Format.",
        solution: "Bitte ein Datum im Format JJJJ-MM-TT auswählen.",
      };
      setError(dateError);
      announce(formatErrorMessage(dateError));
      return;
    }

    const normalizedCategory = category.trim();
    const normalizedComment = comment.trim();

    const title =
      (normalizedComment || normalizedCategory || type).slice(0, 64) || `${type}-Eintrag`;

    onAdd({
      title,
      date,
      category: normalizedCategory,
      comment: normalizedComment,
      sourceUrl: ensureUrlLike(sourceUrl),
      type,
    });

    setCategory("");
    setComment("");
    setSourceUrl("");
    announce("Eintrag hinzugefügt.");
  }

  return (
    <GlassCard as="aside" className="p-0" ariaLabel="Neuen Eintrag anlegen">
      <div className="p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
          className="space-y-4"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-wide text-white/90">Neuer Eintrag</h2>
            <span className="text-[11px] text-white/55">Pflicht: Datum</span>
          </div>

          {error ? (
            <div
              role="alert"
              className="rounded-xl border border-rose-400/25 bg-rose-500/10 px-3 py-2 text-sm text-rose-100"
            >
              <p className="font-semibold">Titel: {error.title}</p>
              <p>Erklärung: {error.explanation}</p>
              <p>Lösung: {error.solution}</p>
            </div>
          ) : null}

          <LabeledField label="Datum" htmlFor={dateId}>
            <div className="relative">
              <TextInput
                id={dateId}
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
              />
              <span
                aria-hidden
                className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-white/55"
              >
                📅
              </span>
            </div>
          </LabeledField>

          <LabeledField
            label="Kategorie"
            htmlFor={catId}
            hint="Beispiel: Recherche, Idee, Todo"
            describedById={catHintId}
          >
            <div className="flex items-center gap-2">
              <span aria-hidden className="text-white/55">
                🏷️
              </span>
              <TextInput
                id={catId}
                aria-describedby={catHintId}
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="z.B. Recherche"
                autoComplete="off"
              />
            </div>
          </LabeledField>

          <LabeledField label="Typ" htmlFor={typeId}>
            <Select
              id={typeId}
              value={type}
              onChange={(v) => setType(v as EntryType)}
              options={(Object.keys(TYPE_META) as EntryType[]).map((k) => ({ value: k, label: k }))}
            />
          </LabeledField>

          <LabeledField
            label="Kommentar"
            htmlFor={commentId}
            hint="Kurz und klar. Beispiel: Warum relevant? Was als nächstes?"
            describedById={commentHintId}
          >
            <TextArea
              id={commentId}
              aria-describedby={commentHintId}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={4}
              placeholder="Was ist passiert, was ist wichtig, was ist der nächste Schritt?"
            />
          </LabeledField>

          <LabeledField
            label="Quelle / URL"
            htmlFor={urlId}
            hint="Optional. Du kannst auch nur example.com einfügen."
            describedById={urlHintId}
          >
            <TextInput
              id={urlId}
              aria-describedby={urlHintId}
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://"
              inputMode="url"
            />
          </LabeledField>

          <button
            type="submit"
            className={classNames(
              "mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl",
              "border border-white/10 bg-blue-500/15 px-3 py-2.5 text-sm font-semibold",
              "text-blue-100 hover:bg-blue-500/18 active:bg-blue-500/20",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
            )}
          >
            <Plus className="h-4 w-4" aria-hidden />
            Eintrag hinzufügen
          </button>

          <p className="text-[11px] text-white/45">Tipp: Drück Enter im Feld, um zu speichern.</p>
        </form>
      </div>
    </GlassCard>
  );
}

function TypeRow({
  selected,
  onToggle,
  compact,
}: {
  selected: Set<EntryType>;
  onToggle: (t: EntryType) => void;
  compact?: boolean;
}) {
  const types = Object.keys(TYPE_META) as EntryType[];
  return (
    <div className={classNames("flex flex-wrap gap-2", compact ? "" : "")}>
      {types.map((t) => (
        <ChipToggle
          key={t}
          label={TYPE_META[t].label}
          meta={TYPE_META[t]}
          pressed={selected.has(t)}
          onToggle={() => onToggle(t)}
          dense={compact}
        />
      ))}
    </div>
  );
}

function RightFilterPanel({
  selectedTypes,
  onToggleType,
  tagMode,
  onTagMode,
  search,
  onSearch,
}: {
  selectedTypes: Set<EntryType>;
  onToggleType: (t: EntryType) => void;
  tagMode: "Alle" | EntryType;
  onTagMode: (m: "Alle" | EntryType) => void;
  search: string;
  onSearch: (v: string) => void;
}) {
  const searchId = useId();

  return (
    <GlassCard as="aside" className="p-0" ariaLabel="Filter und Suche">
      <div className="p-4">
        <h2 className="text-sm font-semibold tracking-wide text-white/90">Filter</h2>

        <div className="mt-3 grid grid-cols-2 gap-2">
          {(Object.keys(TYPE_META) as EntryType[]).map((t) => (
            <ChipToggle
              key={t}
              label={t}
              meta={TYPE_META[t]}
              pressed={selectedTypes.has(t)}
              onToggle={() => onToggleType(t)}
              dense
            />
          ))}
        </div>

        <div className="mt-6">
          <h3 className="text-sm font-semibold tracking-wide text-white/90">Schnell-Tag</h3>
          <p className="mt-1 text-xs text-white/50">Optional: nur einen Typ anzeigen.</p>

          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              aria-pressed={tagMode === "Alle"}
              onClick={() => onTagMode("Alle")}
              className={classNames(
                "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-semibold",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90",
                tagMode === "Alle"
                  ? "border-blue-300/25 bg-blue-500/20 text-blue-100"
                  : "border-white/12 bg-slate-900/45 text-white/80 hover:bg-slate-900/60"
              )}
            >
              <Plus className="h-3.5 w-3.5" aria-hidden />
              Alle
            </button>

            {(Object.keys(TYPE_META) as EntryType[]).map((t) => (
              <button
                key={t}
                type="button"
                aria-pressed={tagMode === t}
                onClick={() => onTagMode(t)}
                className={classNames(
                  "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-semibold",
                  "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90",
                  tagMode === t
                    ? TYPE_META[t].chip
                    : "border-white/12 bg-slate-900/45 text-white/80 hover:bg-slate-900/60"
                )}
              >
                <span aria-hidden className="text-white/65">
                  #
                </span>
                {t}
              </button>
            ))}
          </div>

          <div className="relative mt-4">
            <label htmlFor={searchId} className="sr-only">
              Suche
            </label>
            <Search
              aria-hidden
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/55"
            />
            <input
              id={searchId}
              value={search}
              onChange={(e) => onSearch(e.target.value)}
              placeholder="Suche"
              className={classNames(
                "w-full rounded-xl border border-white/15 bg-slate-950/60 pl-10 pr-3 py-2 text-sm text-white/92",
                "placeholder:text-white/40",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
              )}
            />
          </div>
        </div>
      </div>

      <div className="border-t border-white/12 p-2">
        <button
          type="button"
          className={classNames(
            "ml-auto flex w-full items-center justify-center rounded-xl",
            "border border-white/12 bg-slate-900/45 px-3 py-2 text-sm text-white/80",
            "hover:bg-slate-900/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
          )}
          aria-label="Panel einklappen (Platzhalter)"
          disabled
        >
          <ChevronRight className="h-4 w-4" aria-hidden />
        </button>
      </div>
    </GlassCard>
  );
}

function CenterHeaderArea({
  selectedTypes,
  onToggleType,
  view,
}: {
  selectedTypes: Set<EntryType>;
  onToggleType: (t: EntryType) => void;
  view: "Alle Einträge" | "Filter";
}) {
  return (
    <GlassCard className="h-full p-0" ariaLabel="Übersicht und Filterchips">
      <div className="p-4">
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center gap-2 rounded-xl border border-white/12 bg-slate-900/50 px-3 py-2 text-sm text-white/85">
            <span className="font-semibold">Filter</span>
            <span aria-hidden className="text-white/45">▾</span>
          </div>
          <div className="ml-2 flex items-center gap-2 rounded-xl border border-white/12 bg-slate-900/50 px-3 py-2 text-sm text-white/75">
            <span aria-hidden>☰</span>
            <span aria-hidden className="text-white/45">▾</span>
          </div>
        </div>

        <div className="mt-4">
          <TypeRow selected={selectedTypes} onToggle={onToggleType} />
        </div>

        <div className="mt-6">
          <div className="h-[1px] w-full bg-white/10" />
          <div className="mt-4 grid gap-3">
            <p className="text-sm text-white/60">
              {view === "Alle Einträge"
                ? "Hier erscheinen deine Einträge. Klick auf einen Eintrag, um Details zu sehen."
                : "Aktive Filter steuern Liste und Zeitachse."}
            </p>
            <p className="text-xs text-white/45">Tipp: Suche + Typ-Buttons kombinieren.</p>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

function Timeline({
  entries,
  monthKey,
  onMonthKey,
  onOpen,
}: {
  entries: Entry[];
  monthKey: string;
  onMonthKey: (mk: string) => void;
  onOpen: (e: Entry) => void;
}) {
  const reducedMotion = usePrefersReducedMotion();
  const detailId = useId();
  const controlsId = useId();
  const [zoom, setZoom] = useState(1);
  const [rowSpacing, setRowSpacing] = useState(1);
  const [activeEntryId, setActiveEntryId] = useState<string | null>(null);

  const mk = isMonthKey(monthKey) ? monthKey : toYMD(new Date()).slice(0, 7);

  const monthEntries = useMemo(() => {
    return entries
      .filter((e) => monthKeyFromYMD(e.date) === mk)
      .slice()
      .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  }, [entries, mk]);

  const year = Number(mk.slice(0, 4));
  const monthIndex0 = Number(mk.slice(5, 7)) - 1;
  const dim = daysInMonth(year, monthIndex0);
  const safeZoom = clamp(zoom, 0.8, 1.6);
  const safeSpacing = clamp(rowSpacing, 0.8, 1.4);
  const trackWidth = `${Math.round(safeZoom * 100)}%`;
  const laneHeight = Math.round(130 * safeSpacing);
  const detailEntry = monthEntries.find((entry) => entry.id === activeEntryId) ?? null;
  const offsetTop = Math.round(-46 * safeSpacing);
  const offsetBottom = Math.round(18 * safeSpacing);

  function updateZoom(value: number) {
    if (!Number.isFinite(value)) return;
    setZoom(clamp(value, 0.8, 1.6));
  }

  function updateSpacing(value: number) {
    if (!Number.isFinite(value)) return;
    setRowSpacing(clamp(value, 0.8, 1.4));
  }

  function moveMonth(delta: number) {
    onMonthKey(addMonths(mk, delta));
  }

  const gradientLine =
    "bg-[linear-gradient(90deg,rgba(59,130,246,0.8),rgba(16,185,129,0.8),rgba(245,158,11,0.8),rgba(244,63,94,0.8))] shadow-[0_0_24px_rgba(96,165,250,0.45)]";

  return (
    <GlassCard className="p-0" ariaLabel="Zeitachse">
      <div className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => moveMonth(-12)}
              className="rounded-xl border border-white/12 bg-slate-900/45 px-2 py-2 text-white/85 hover:bg-slate-900/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
              aria-label="Ein Jahr zurück"
            >
              <ChevronsLeft className="h-4 w-4" aria-hidden />
            </button>
            <button
              type="button"
              onClick={() => moveMonth(-1)}
              className="rounded-xl border border-white/12 bg-slate-900/45 px-2 py-2 text-white/85 hover:bg-slate-900/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
              aria-label="Vormonat"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden />
            </button>
          </div>

          <div className="text-sm font-semibold text-white/90">
            <span className="text-white/55">·</span> {monthLabelDE(mk)}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => moveMonth(1)}
              className="rounded-xl border border-white/12 bg-slate-900/45 px-2 py-2 text-white/85 hover:bg-slate-900/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
              aria-label="Nächster Monat"
            >
              <ChevronRight className="h-4 w-4" aria-hidden />
            </button>
            <button
              type="button"
              onClick={() => moveMonth(12)}
              className="rounded-xl border border-white/12 bg-slate-900/45 px-2 py-2 text-white/85 hover:bg-slate-900/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
              aria-label="Ein Jahr vor"
            >
              <ChevronsRight className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </div>

        <div className="mt-4 rounded-2xl border border-white/12 bg-slate-950/55 p-4">
          <div className="flex flex-wrap items-center gap-3 text-xs text-white/65" id={controlsId}>
            <span className="font-semibold text-white/85">Ansicht</span>
            <label className="flex items-center gap-2">
              <span>Zoom</span>
              <input
                type="range"
                min={0.8}
                max={1.6}
                step={0.05}
                value={safeZoom}
                onChange={(event) => updateZoom(Number(event.target.value))}
                aria-label="Zoom der Zeitachse"
                className="h-1.5 w-28 accent-amber-200"
              />
              <span className="tabular-nums text-white/80">{Math.round(safeZoom * 100)}%</span>
            </label>
            <label className="flex items-center gap-2">
              <span>Abstand</span>
              <input
                type="range"
                min={0.8}
                max={1.4}
                step={0.05}
                value={safeSpacing}
                onChange={(event) => updateSpacing(Number(event.target.value))}
                aria-label="Abstand zwischen den Einträgen"
                className="h-1.5 w-28 accent-amber-200"
              />
              <span className="tabular-nums text-white/80">{Math.round(safeSpacing * 100)}%</span>
            </label>
            <button
              type="button"
              onClick={() => {
                updateZoom(1);
                updateSpacing(1);
              }}
              className="rounded-lg border border-white/12 bg-slate-900/50 px-2 py-1 text-white/80 hover:bg-slate-900/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950/90"
            >
              Standard
            </button>
            <span className="text-white/50">Tipp: Mit Tab erreichst du jeden Punkt.</span>
          </div>

          <div className="mt-4 overflow-x-auto pb-2" aria-describedby={controlsId}>
            <div className="relative min-w-[520px]" style={{ height: `${laneHeight}px`, width: trackWidth }}>
              <div className="absolute left-2 right-2 top-1/2 -translate-y-1/2">
                <div className={classNames("h-[4px] rounded-full", gradientLine)} />
                <div className="mt-2 h-[1px] w-full bg-white/12" />
              </div>

              <div className="absolute inset-0" role="list" aria-label="Zeitachse mit Einträgen" aria-describedby={detailId}>
                {monthEntries.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-sm text-white/60">
                    Keine Einträge in diesem Monat.
                  </div>
                ) : (
                  monthEntries.map((e, idx) => {
                    const day = dayOfMonthFromYMD(e.date);
                    const pos = dim <= 1 ? 50 : clamp(((day - 1) / (dim - 1)) * 100, 0, 100);
                    const meta = TYPE_META[e.type];
                    const isTop = idx % 2 === 0;

                    return (
                      <button
                        key={e.id}
                        type="button"
                        onClick={() => {
                          setActiveEntryId(e.id);
                          onOpen(e);
                        }}
                        onMouseEnter={() => setActiveEntryId(e.id)}
                        onMouseLeave={() => setActiveEntryId(null)}
                        onFocus={() => setActiveEntryId(e.id)}
                        onBlur={() => setActiveEntryId(null)}
                        className={classNames(
                          "absolute rounded-full focus:outline-none focus-visible:ring-2",
                          "focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
                        )}
                        style={{ left: `calc(${pos}% - 10px)` }}
                        role="listitem"
                        aria-label={`Eintrag öffnen: ${e.title}, ${e.type}, ${formatDE(e.date)}`}
                      >
                        <div className={classNames("relative", isTop ? "-translate-y-[6px]" : "translate-y-[64px]")}>
                          <div
                            aria-hidden
                            className={classNames(
                              "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
                              "size-4 rounded-full border border-white/30",
                              "bg-white/10",
                              meta.glow
                            )}
                          >
                            <div
                              className={classNames(
                                "absolute inset-[3px] rounded-full",
                                e.type === "Fund"
                                  ? "bg-blue-400"
                                  : e.type === "Studie"
                                  ? "bg-emerald-400"
                                  : e.type === "Theorie"
                                  ? "bg-amber-400"
                                  : "bg-rose-400"
                              )}
                            />
                          </div>

                          <div
                            className={classNames(
                              "min-w-[180px] max-w-[260px] rounded-xl border",
                              "bg-slate-900/60 backdrop-blur-2xl",
                              "px-3 py-2",
                              "shadow-[0_18px_55px_rgba(0,0,0,0.55)]",
                              "ring-1",
                              meta.ring,
                              reducedMotion ? "" : "transition hover:translate-y-[-1px]"
                            )}
                            style={{
                              transform: isTop
                                ? `translate(-50%, ${offsetTop}px)`
                                : `translate(-50%, ${offsetBottom}px)`,
                            }}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="text-sm font-semibold text-white/95">{e.title || `${e.type} Eintrag`}</div>
                              <div className="text-[11px] text-white/70 whitespace-nowrap">{formatDE(e.date)}</div>
                            </div>
                            {e.comment ? (
                              <div className="mt-1 line-clamp-2 text-xs text-white/75">{e.comment}</div>
                            ) : null}
                          </div>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-white/55">
            <span>{`01. ${pad2(monthIndex0 + 1)} ${year}`}</span>
            <span>{`${pad2(Math.floor(dim / 2))}. ${pad2(monthIndex0 + 1)} ${year}`}</span>
            <span>{`${pad2(dim)}. ${pad2(monthIndex0 + 1)} ${year}`}</span>
          </div>

          <div className="mt-3 rounded-xl border border-white/10 bg-white/5 p-3 text-xs text-white/70" id={detailId}>
            {detailEntry ? (
              <div className="grid gap-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-white/90">{detailEntry.title || `${detailEntry.type} Eintrag`}</span>
                  <span className="text-white/60">{formatDE(detailEntry.date)}</span>
                </div>
                <div>{detailEntry.comment || "Kein Kommentar vorhanden."}</div>
                <div className="text-white/55">Kategorie: {detailEntry.category || "–"}</div>
              </div>
            ) : (
              <span>Hover oder fokussiere einen Punkt, um Details zu lesen.</span>
            )}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

function EntriesList({
  entries,
  onOpen,
  onDelete,
}: {
  entries: Entry[];
  onOpen: (e: Entry) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <GlassCard className="p-0" ariaLabel="Eintragsliste">
      <div className="p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold tracking-wide text-white/90">Einträge</h2>
          <div className="text-xs text-white/55">{entries.length} sichtbar</div>
        </div>

        <div className="mt-3 space-y-2">
          {entries.length === 0 ? (
            <div className="rounded-xl border border-white/10 bg-white/4 p-4 text-sm text-white/50">
              Keine Treffer.
            </div>
          ) : (
            entries.slice(0, 10).map((e) => {
              const meta = TYPE_META[e.type];
              return (
                <div
                  key={e.id}
                  className="flex items-stretch gap-2 rounded-xl border border-white/10 bg-white/5 p-2"
                >
                  <button
                    type="button"
                    onClick={() => onOpen(e)}
                    className={classNames(
                      "flex-1 rounded-lg p-1.5 text-left",
                      "hover:bg-white/6 active:bg-white/8",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
                    )}
                    aria-label={`Eintrag öffnen: ${e.title}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className={classNames(
                              "inline-flex items-center gap-2 rounded-lg border px-2 py-1 text-[11px]",
                              meta.chip
                            )}
                          >
                            {meta.icon}
                            {e.type}
                          </span>
                          <span className="text-sm font-semibold text-white/92 line-clamp-1">{e.title}</span>
                        </div>
                        <div className="mt-1 text-xs text-white/60 line-clamp-1">
                          {e.category ? `Kategorie: ${e.category}` : "Kategorie: –"}
                        </div>
                      </div>
                      <div className="text-xs text-white/60 whitespace-nowrap">{formatDE(e.date)}</div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => onDelete(e.id)}
                    className={classNames(
                      "shrink-0 rounded-lg border border-white/10 bg-white/4 px-2",
                      "text-white/75 hover:bg-white/8",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
                    )}
                    aria-label={`Eintrag löschen: ${e.title}`}
                    title="Löschen"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {entries.length > 10 ? (
          <p className="mt-3 text-xs text-white/45">Hinweis: Liste zeigt maximal 10 Einträge. Nutze Suche, um einzugrenzen.</p>
        ) : null}
      </div>
    </GlassCard>
  );
}

function Modal({
  open,
  onClose,
  title,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  const dialogRef = useRef<HTMLDivElement | null>(null);
  const titleId = useId();
  const prevFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;

    prevFocus.current = document.activeElement as HTMLElement | null;

    const el = dialogRef.current;
    if (!el) return;

    const getFocusables = () =>
      Array.from(
        el.querySelectorAll<HTMLElement>(
          "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        )
      ).filter((x) => !x.hasAttribute("disabled") && !x.hasAttribute("data-focus-exclude"));

    const focusables = getFocusables();
    (focusables[0] || el).focus();

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const f = getFocusables();
        if (!f.length) return;
        const first = f[0];
        const last = f[f.length - 1];
        const active = document.activeElement as HTMLElement | null;
        if (e.shiftKey) {
          if (!active || active === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (active === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    }

    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      prevFocus.current?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div role="dialog" aria-modal="true" aria-labelledby={titleId} className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        onClick={onClose}
        className="absolute inset-0 bg-black/70"
        aria-label="Schließen"
        data-focus-exclude
      />
      <div ref={dialogRef} tabIndex={-1} className="relative w-full max-w-2xl rounded-2xl border border-white/10 bg-zinc-950/70 backdrop-blur-xl shadow-[0_30px_120px_rgba(0,0,0,0.8)]">
        <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3">
          <h3 id={titleId} className="text-sm font-semibold text-white/92">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/85 hover:bg-white/8 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
          >
            <span className="inline-flex items-center gap-2">
              <X className="h-4 w-4" aria-hidden /> Schließen
            </span>
          </button>
        </div>
        <div className="p-4">{children}</div>
        {footer ? <div className="border-t border-white/10 px-4 py-3">{footer}</div> : null}
      </div>
    </div>
  );
}

function EntryDetails({ entry }: { entry: Entry }) {
  const meta = TYPE_META[entry.type];
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className={classNames("inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-semibold", meta.chip)}>
          {meta.icon}
          {entry.type}
        </span>
        <span className="text-xs text-white/60">{formatDE(entry.date)}</span>
      </div>

      <div>
        <div className="text-lg font-semibold text-white/92">{entry.title}</div>
        <div className="mt-1 text-sm text-white/65">{entry.category ? `Kategorie: ${entry.category}` : "Kategorie: –"}</div>
      </div>

      {entry.comment ? (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/80">{entry.comment}</div>
      ) : (
        <div className="rounded-2xl border border-white/10 bg-white/4 p-4 text-sm text-white/55">Kein Kommentar.</div>
      )}

      {entry.sourceUrl ? (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="text-xs font-semibold text-white/75">Quelle</div>
          <a
            href={entry.sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-1 block break-all rounded text-sm text-blue-200 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
          >
            {entry.sourceUrl}
          </a>
        </div>
      ) : null}
    </div>
  );
}

function HelpContent() {
  return (
    <div className="space-y-3 text-sm text-white/80">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <h4 className="text-sm font-semibold text-white/90">So nutzt du das Tool</h4>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-white/75">
          <li>Links: neuen Eintrag anlegen. Pflicht ist nur das Datum.</li>
          <li>Mitte/Rechts: Typ-Filter und Suche. Steuert Liste und Zeitachse.</li>
          <li>Unten: Zeitachse. Klick auf einen Punkt öffnet Details.</li>
          <li>Oben: „Daten“ für Export/Import. Alles wird gespeichert.</li>
        </ul>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/4 p-4">
        <h4 className="text-sm font-semibold text-white/90">Speicherung</h4>
        <p className="mt-2 text-white/70">Deine Daten liegen im Browser. Export ist dein Backup.</p>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/4 p-4">
        <h4 className="text-sm font-semibold text-white/90">Tastatur</h4>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-white/75">
          <li>Tab: durch Elemente springen</li>
          <li>Enter: Buttons auslösen</li>
          <li>Esc: Modals schließen</li>
        </ul>
      </div>
    </div>
  );
}

function DataManager({
  state,
  onImportState,
  onReset,
  announce,
}: {
  state: AppStateV1;
  onImportState: (s: AppStateV1) => void;
  onReset: () => void;
  announce: (msg: string) => void;
}) {
  const exportJson = useMemo(() => JSON.stringify(state, null, 2), [state]);
  const [importText, setImportText] = useState("");
  const fileRef = useRef<HTMLInputElement | null>(null);

  function copyExport() {
    navigator.clipboard
      ?.writeText(exportJson)
      .then(() => announce("Export in Zwischenablage kopiert."))
      .catch(() => announce("Kopieren fehlgeschlagen."));
  }

  function downloadExport() {
    const stamp = new Date().toISOString().slice(0, 10);
    downloadText(`projekt-dashboard_${stamp}.json`, exportJson);
    announce("Export heruntergeladen.");
  }

  function validateState(
    candidate: any
  ):
    | { ok: true; value: AppStateV1 }
    | { ok: false; error: string } {
    if (!candidate || typeof candidate !== "object") {
      return { ok: false, error: "Datei passt nicht zu diesem Tool." };
    }
    if (candidate.v !== 1) {
      return { ok: false, error: "Datei-Version passt nicht. Bitte Export aus diesem Tool nutzen." };
    }
    if (!Array.isArray(candidate.entries)) {
      return { ok: false, error: "Einträge fehlen in der Datei." };
    }
    if (!candidate || typeof candidate !== "object") return { ok: false, error: "Kein Objekt" };
    if (candidate.v !== 1) return { ok: false, error: "Falsche Version" };
    if (!Array.isArray(candidate.entries)) return { ok: false, error: "Einträge fehlen" };

    const types = new Set(Object.keys(TYPE_META) as EntryType[]);
    const seenIds = new Set<string>();

    const entries: Entry[] = [];
    for (const [index, e] of candidate.entries.entries()) {
      if (typeof e?.date !== "string" || !isYMD(e.date)) {
        return {
          ok: false,
          error: `Eintrag ${index + 1}: Datum hat falsches Format. Bitte ${DATE_FORMAT_HINT}.`,
        };
      }

      const type: EntryType = types.has(e?.type) ? e.type : "Fund";
      const date = e.date;

      let id = typeof e?.id === "string" && e.id ? e.id : uid();
      if (seenIds.has(id)) id = uid();
      seenIds.add(id);

      entries.push({
        id,
        title: typeof e?.title === "string" && e.title.trim() ? e.title : `${type}-Eintrag`,
        date,
        category: typeof e?.category === "string" ? e.category : "",
        comment: typeof e?.comment === "string" ? e.comment : "",
        sourceUrl: typeof e?.sourceUrl === "string" ? ensureUrlLike(e.sourceUrl) : "",
        type,
      });
    }

    const selectedTypes: EntryType[] = Array.isArray(candidate.selectedTypes)
      ? candidate.selectedTypes.filter((t: any) => types.has(t))
      : (Object.keys(TYPE_META) as EntryType[]);

    const tagMode: "Alle" | EntryType =
      candidate.tagMode === "Alle" || types.has(candidate.tagMode) ? candidate.tagMode : "Alle";

    const monthKey =
      typeof candidate.monthKey === "string" && isMonthKey(candidate.monthKey)
        ? candidate.monthKey
        : monthKeyFromYMD(entries[0]?.date || toYMD(new Date()));

    return {
      ok: true,
      value: {
        v: 1,
        entries,
        selectedTypes: selectedTypes.length ? selectedTypes : (Object.keys(TYPE_META) as EntryType[]),
        tagMode,
        monthKey,
      },
    };
  }

  function importNow(text: string) {
    const parsed = safeJsonParse<any>(text);
    if (!parsed.ok) {
      const parseError = importErrorFor(parsed.error);
      announce(formatErrorMessage(parseError));
      return;
    }
    const validated = validateState(parsed.value);
    if (!validated.ok) {
      const validationError = importErrorFor(validated.error);
      announce(formatErrorMessage(validationError));
      return;
    }
    onImportState(validated.value);
    setImportText("");
    announce("Import erfolgreich.");
  }

  async function handleFile(file: File) {
    const text = await file.text();
    setImportText(text);
    announce("Datei geladen. Prüfe JSON und klicke Import.");
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <h4 className="text-sm font-semibold text-white/90">Export</h4>
        <p className="mt-1 text-xs text-white/55">Kopieren, herunterladen oder als Backup speichern.</p>

        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={copyExport}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/85 hover:bg-white/8 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
          >
            <Copy className="h-4 w-4" aria-hidden />
            Kopieren
          </button>

          <button
            type="button"
            onClick={downloadExport}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/85 hover:bg-white/8 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
          >
            <Download className="h-4 w-4" aria-hidden />
            Herunterladen
          </button>
        </div>

        <div className="mt-3">
          <TextArea value={exportJson} readOnly rows={8} aria-label="JSON-Export" />
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <h4 className="text-sm font-semibold text-white/90">Import</h4>
        <p className="mt-1 text-xs text-white/55">JSON einfügen oder Datei auswählen.</p>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/85 hover:bg-white/8 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
          >
            <Upload className="h-4 w-4" aria-hidden />
            Datei wählen
          </button>

          <input
            ref={fileRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
              e.currentTarget.value = "";
            }}
          />

          <button
            type="button"
            onClick={() => importNow(importText)}
            disabled={!importText.trim()}
            className={classNames(
              "inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80",
              !importText.trim() ? "bg-white/3 text-white/35" : "bg-blue-500/15 text-blue-100 hover:bg-blue-500/18"
            )}
          >
            <Upload className="h-4 w-4" aria-hidden />
            Import
          </button>
        </div>

        <div className="mt-3">
          <TextArea
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            rows={8}
            placeholder="JSON hier einfügen…"
            aria-label="JSON-Import"
          />
        </div>
      </div>

      <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 p-4">
        <h4 className="text-sm font-semibold text-rose-100">Zurücksetzen</h4>
        <p className="mt-1 text-xs text-rose-100/80">Löscht alle Einträge im Browser. Vorher Export machen.</p>
        <button
          type="button"
          onClick={onReset}
          className="mt-3 inline-flex items-center gap-2 rounded-xl border border-rose-300/25 bg-rose-500/10 px-3 py-2 text-sm font-semibold text-rose-100 hover:bg-rose-500/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/90 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950/80"
        >
          <Trash2 className="h-4 w-4" aria-hidden />
          Alles löschen
        </button>
      </div>
    </div>
  );
}

function assert(cond: any, msg: string) {
  if (!cond) throw new Error(`Selbsttest fehlgeschlagen: ${msg}`);
}

function runSelfTests() {
  assert(isYMD("2024-02-14"), "isYMD ok");
  assert(!isYMD("2024-2-14"), "isYMD reject");
  assert(monthKeyFromYMD("2024-02-14") === "2024-02", "monthKeyFromYMD");
  assert(formatDE("2024-02-14") === "14.02.2024", "formatDE");
  assert(dayOfMonthFromYMD("2024-02-14") === 14, "dayOfMonthFromYMD");
  assert(ensureUrlLike("example.com") === "https://example.com", "ensureUrlLike");
  assert(isMonthKey("2026-01"), "isMonthKey ok");
  assert(!isMonthKey("2026-1"), "isMonthKey reject");
  assert(addMonths("2026-01", 1) === "2026-02", "addMonths +1");
  assert(addMonths("2026-01", -1) === "2025-12", "addMonths -1");
  assert(resolveTheme("auto", true) === "dunkel", "resolveTheme auto dark");
  assert(resolveTheme("auto", false) === "hell", "resolveTheme auto light");
  assert(resolveTheme("dunkel", false) === "dunkel", "resolveTheme explicit dark");
  assert(normalizeNoteText("  Hallo   Welt ") === "Hallo Welt", "normalizeNoteText");
  const ok = safeJsonParse<{ a: number }>("{\"a\":1}");
  assert(ok.ok && ok.value.a === 1, "safeJsonParse ok");
  const bad = safeJsonParse("{");
  assert(!bad.ok, "safeJsonParse bad");
  const msgA = formatErrorMessage({
    title: "Test A",
    explanation: "Erklärung A.",
    solution: "Lösung A.",
  });
  const msgB = formatErrorMessage({
    title: "Test B",
    explanation: "Erklärung B.",
    solution: "Lösung B.",
  });
  assert(
    ["Titel:", "Erklärung:", "Lösung:"].every((part) => msgA.includes(part)),
    "error format structure A"
  );
  assert(
    ["Titel:", "Erklärung:", "Lösung:"].every((part) => msgB.includes(part)),
    "error format structure B"
  );
  return "ok" as const;
}

if (typeof window !== "undefined") {
  (window as any).__ProjektDashboardTests = runSelfTests;
}

export default function ProjektDashboardTool() {
  const mainId = useId();

  const prefersDark = usePrefersDarkMode();
  const [themeMode, setThemeMode] = useState<ThemeMode>(DEFAULT_THEME_MODE);
  const resolvedTheme = resolveTheme(themeMode, prefersDark);
  const themeStyle = useMemo(
    () =>
      ({
        "--page-bg":
          resolvedTheme === "dunkel"
            ? "radial-gradient(1200px 820px at 18% 8%, rgba(59,130,246,0.26), transparent 55%), radial-gradient(980px 780px at 82% 76%, rgba(244,63,94,0.22), transparent 55%), radial-gradient(900px 700px at 55% 38%, rgba(16,185,129,0.16), transparent 60%), linear-gradient(180deg, rgba(8,10,20,1), rgba(3,6,16,1))"
            : "radial-gradient(1000px 720px at 15% 12%, rgba(191,219,254,0.5), transparent 60%), radial-gradient(900px 650px at 85% 68%, rgba(252,231,243,0.38), transparent 55%), linear-gradient(180deg, rgba(15,23,42,1), rgba(2,6,23,1))",
      }) as React.CSSProperties,
    [resolvedTheme]
  );

  const [sidebar, setSidebar] = useState<"dashboard" | "extensions" | "plugins">("dashboard");
  const [view, setView] = useState<"Alle Einträge" | "Filter">("Alle Einträge");
  const [search, setSearch] = useState("");
  const [globalSearch, setGlobalSearch] = useState("");
  const [activeEntry, setActiveEntry] = useState<Entry | null>(null);
  const [openHelp, setOpenHelp] = useState(false);
  const [openData, setOpenData] = useState(false);
  const [favoriteModules, setFavoriteModules] = useState<Set<string>>(
    () => new Set(DEFAULT_FAVORITE_MODULES)
  );
  const [quickNotes, setQuickNotes] = useState<QuickNote[]>([]);
  const [noteDraft, setNoteDraft] = useState("");

  const liveRegionId = useId();
  const [liveMsg, setLiveMsg] = useState("");
  const announce = useCallback((msg: string) => {
    setLiveMsg("");
    window.setTimeout(() => setLiveMsg(msg), 10);
  }, []);

  const initialEntries: Entry[] = useMemo(
    () => [
      {
        id: uid(),
        title: "Fund X entdeckt",
        date: "2024-01-16",
        category: "Notiz",
        comment: "Erster Marker auf der Zeitachse.",
        sourceUrl: "",
        type: "Fund",
      },
      {
        id: uid(),
        title: "02. Feb 2024",
        date: "2024-02-02",
        category: "Dokument",
        comment: "Studie als Referenz hinzugefügt.",
        sourceUrl: "example.com",
        type: "Studie",
      },
      {
        id: uid(),
        title: "Theorie Y diskutiert",
        date: "2024-02-14",
        category: "Hypothese",
        comment: "These, Gegenargumente, nächste Schritte.",
        sourceUrl: "",
        type: "Theorie",
      },
      {
        id: uid(),
        title: "Webseite D gefunden",
        date: "2024-02-28",
        category: "Quelle",
        comment: "Link in Sammlung aufgenommen.",
        sourceUrl: "https://example.org",
        type: "Quelle",
      },
    ],
    []
  );

  const [entries, setEntries] = useState<Entry[]>(initialEntries);
  const [selectedTypes, setSelectedTypes] = useState<Set<EntryType>>(
    () => new Set(Object.keys(TYPE_META) as EntryType[])
  );
  const [tagMode, setTagMode] = useState<"Alle" | EntryType>("Alle");
  const [monthKey, setMonthKey] = useState<string>(() => monthKeyFromYMD("2024-01-16"));
  const moduleIdSet = useMemo(() => new Set(MODULE_ITEMS.map((item) => item.id)), []);

  useEffect(() => {
    const raw = safeLocalStorageGet(STORAGE_KEY);
    if (!raw) return;
    const parsed = safeJsonParse<AppStateV1>(raw);
    if (!parsed.ok) return;

    const candidate = parsed.value as any;
    if (!candidate || candidate.v !== 1 || !Array.isArray(candidate.entries)) return;

    try {
      const typesSet = new Set(Object.keys(TYPE_META) as EntryType[]);
      const seen = new Set<string>();

      const loadedEntries: Entry[] = candidate.entries.map((e: any) => {
        let id = typeof e?.id === "string" && e.id ? e.id : uid();
        if (seen.has(id)) id = uid();
        seen.add(id);

        return {
          id,
          title: typeof e?.title === "string" && e.title ? e.title : "Eintrag",
          date: typeof e?.date === "string" && isYMD(e.date) ? e.date : toYMD(new Date()),
          category: typeof e?.category === "string" ? e.category : "",
          comment: typeof e?.comment === "string" ? e.comment : "",
          sourceUrl: typeof e?.sourceUrl === "string" ? ensureUrlLike(e.sourceUrl) : "",
          type: typesSet.has(e?.type) ? e.type : "Fund",
        };
      });

      setEntries(loadedEntries.length ? loadedEntries : initialEntries);

      const st: EntryType[] = Array.isArray(candidate.selectedTypes)
        ? candidate.selectedTypes.filter((t: any) => typesSet.has(t))
        : (Object.keys(TYPE_META) as EntryType[]);
      setSelectedTypes(new Set(st.length ? st : (Object.keys(TYPE_META) as EntryType[])));

      const tm: "Alle" | EntryType =
        candidate.tagMode === "Alle" || typesSet.has(candidate.tagMode) ? candidate.tagMode : "Alle";
      setTagMode(tm);

      const mk =
        typeof candidate.monthKey === "string" && isMonthKey(candidate.monthKey)
          ? candidate.monthKey
          : monthKeyFromYMD(loadedEntries[0]?.date || toYMD(new Date()));
      setMonthKey(mk);

      const favorites = Array.isArray(candidate.favoriteModules)
        ? candidate.favoriteModules.filter((id: any) => moduleIdSet.has(id))
        : DEFAULT_FAVORITE_MODULES;
      setFavoriteModules(new Set(favorites.length ? favorites : DEFAULT_FAVORITE_MODULES));

      const notes = Array.isArray(candidate.quickNotes)
        ? candidate.quickNotes
            .map((note: any) => ({
              id: typeof note?.id === "string" && note.id ? note.id : uid(),
              text: normalizeNoteText(typeof note?.text === "string" ? note.text : ""),
              createdAt: typeof note?.createdAt === "number" ? note.createdAt : Date.now(),
            }))
            .filter((note: QuickNote) => note.text.length > 0)
        : [];
      setQuickNotes(notes);

      const tm: ThemeMode =
        candidate.themeMode === "hell" || candidate.themeMode === "dunkel" || candidate.themeMode === "auto"
          ? candidate.themeMode
          : DEFAULT_THEME_MODE;
      setThemeMode(tm);

      announce("Daten geladen.");
    } catch {
      // ignore
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleType = useCallback((t: EntryType) => {
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(t)) next.delete(t);
      else next.add(t);
      if (next.size === 0) return new Set([t]);
      return next;
    });
  }, []);

  const addEntry = useCallback((e: Omit<Entry, "id">) => {
    const next: Entry = { ...e, id: uid() };
    setEntries((prev) => [next, ...prev]);
    setMonthKey(monthKeyFromYMD(next.date));
    setActiveEntry(next);
  }, []);

  const deleteEntry = useCallback(
    (id: string) => {
      setEntries((prev) => prev.filter((x) => x.id !== id));
      setActiveEntry((cur) => (cur?.id === id ? null : cur));
      announce("Eintrag gelöscht.");
    },
    [announce]
  );

  const selectModule = useCallback(
    (target: ModuleItem["target"]) => {
      if (target === "data") {
        setOpenData(true);
        return;
      }
      if (target === "help") {
        setOpenHelp(true);
        return;
      }
      setSidebar(target);
      if (target === "dashboard") setView("Alle Einträge");
    },
    [setSidebar, setView]
  );

  const toggleFavoriteModule = useCallback(
    (id: string) => {
      if (!moduleIdSet.has(id)) {
        announce("Unbekanntes Modul. Favorit konnte nicht gesetzt werden.");
        return;
      }
      setFavoriteModules((prev) => {
        const next = new Set(prev);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return next;
      });
    },
    [announce, moduleIdSet]
  );

  const handleNoteDraft = useCallback((value: string) => {
    setNoteDraft(value.slice(0, 200));
  }, []);

  const addQuickNote = useCallback(() => {
    const normalized = normalizeNoteText(noteDraft);
    if (!normalized) {
      announce("Notiz ist leer. Bitte Text eingeben.");
      return;
    }
    if (normalized.length > 200) {
      announce("Notiz ist zu lang. Bitte auf 200 Zeichen kürzen.");
      return;
    }
    const note: QuickNote = { id: uid(), text: normalized, createdAt: Date.now() };
    setQuickNotes((prev) => [note, ...prev].slice(0, 20));
    setNoteDraft("");
    announce("Notiz gespeichert.");
  }, [announce, noteDraft]);

  const removeQuickNote = useCallback(
    (id: string) => {
      setQuickNotes((prev) => prev.filter((note) => note.id !== id));
      announce("Notiz entfernt.");
    },
    [announce]
  );

  const searchIndex = useMemo(() => {
    const map = new Map<string, string>();
    for (const e of entries) {
      map.set(e.id, normalizeText(`${e.title} ${e.category} ${e.comment} ${e.sourceUrl} ${e.type}`));
    }
    return map;
  }, [entries]);

  const filtered = useMemo(() => {
    const q = normalizeText(search);
    return entries.filter((e) => {
      if (!selectedTypes.has(e.type)) return false;
      if (tagMode !== "Alle" && e.type !== tagMode) return false;
      if (!q) return true;
      const blob = searchIndex.get(e.id) || "";
      return blob.includes(q);
    });
  }, [entries, selectedTypes, tagMode, search, searchIndex]);

  const globalResults = useMemo(() => {
    const q = normalizeText(globalSearch);
    if (!q) {
      return { entries: [], modules: [], actions: [], notes: [] };
    }
    const entriesMatch = entries
      .filter((entry) => (searchIndex.get(entry.id) || "").includes(q))
      .slice(0, 5);
    const moduleMatches = MODULE_ITEMS.filter((item) =>
      normalizeText(`${item.label} ${item.description} ${item.keywords.join(" ")}`).includes(q)
    ).slice(0, 4);
    const actionMatches = QUICK_ACTIONS.filter((action) =>
      normalizeText(`${action.label} ${action.description} ${action.keywords.join(" ")}`).includes(q)
    ).slice(0, 4);
    const noteMatches = quickNotes
      .filter((note) => normalizeText(note.text).includes(q))
      .slice(0, 3);
    return {
      entries: entriesMatch,
      modules: moduleMatches,
      actions: actionMatches,
      notes: noteMatches,
    };
  }, [entries, globalSearch, quickNotes, searchIndex]);

  useEffect(() => {
    const hasMonth = filtered.some((e) => monthKeyFromYMD(e.date) === monthKey);
    if (!hasMonth && filtered.length) setMonthKey(monthKeyFromYMD(filtered[0].date));
  }, [filtered, monthKey]);

  const defaultDate = useMemo(() => toYMD(new Date()), []);

  const appState: AppStateV1 = useMemo(
    () => ({
      v: 1,
      entries,
      selectedTypes: Array.from(selectedTypes),
      tagMode,
      monthKey: isMonthKey(monthKey) ? monthKey : toYMD(new Date()).slice(0, 7),
      favoriteModules: Array.from(favoriteModules),
      quickNotes,
      themeMode,
    }),
    [entries, favoriteModules, monthKey, quickNotes, selectedTypes, tagMode, themeMode]
  );

  const saveState = useCallback(
    (s: AppStateV1) => {
      const ok = safeLocalStorageSet(STORAGE_KEY, JSON.stringify(s));
      if (!ok) announce("Speichern fehlgeschlagen (Browser/Quota). Export als Backup nutzen.");
    },
    [announce]
  );

  const backupNow = useCallback(() => {
    try {
      const stamp = new Date().toISOString().slice(0, 16).replace(/[:T]/g, "-");
      downloadText(`projekt-dashboard_backup_${stamp}.json`, JSON.stringify(appState, null, 2));
      announce("Backup gespeichert.");
    } catch {
      announce("Backup fehlgeschlagen. Bitte Export nutzen.");
    }
  }, [announce, appState]);

  const getState = useCallback(() => appState, [appState]);
  const { saving, lastSavedAt } = useIntervalAutosave<AppStateV1>(getState, saveState, AUTOSAVE_EVERY_MS);

  const importState = useCallback((s: AppStateV1) => {
    setEntries(s.entries);
    setSelectedTypes(new Set(s.selectedTypes));
    setTagMode(s.tagMode);
    setMonthKey(s.monthKey);
    const favorites = Array.isArray(s.favoriteModules)
      ? s.favoriteModules.filter((id) => moduleIdSet.has(id))
      : DEFAULT_FAVORITE_MODULES;
    setFavoriteModules(new Set(favorites.length ? favorites : DEFAULT_FAVORITE_MODULES));
    setQuickNotes(Array.isArray(s.quickNotes) ? s.quickNotes : []);
    setThemeMode(s.themeMode || DEFAULT_THEME_MODE);
  }, [moduleIdSet]);

  const resetAll = useCallback(() => {
    safeLocalStorageRemove(STORAGE_KEY);
    setEntries(initialEntries);
    setSelectedTypes(new Set(Object.keys(TYPE_META) as EntryType[]));
    setTagMode("Alle");
    setMonthKey(monthKeyFromYMD(initialEntries[0]?.date || toYMD(new Date())));
    setFavoriteModules(new Set(DEFAULT_FAVORITE_MODULES));
    setQuickNotes([]);
    setNoteDraft("");
    setThemeMode(DEFAULT_THEME_MODE);
    setOpenData(false);
    announce("Zurückgesetzt.");
  }, [initialEntries, announce]);

  const handleGlobalAction = useCallback(
    (actionId: QuickAction["id"]) => {
      if (actionId === "action-export") {
        setOpenData(true);
        return;
      }
      if (actionId === "action-backup") {
        backupNow();
        return;
      }
      if (actionId === "action-new-entry") {
        setSidebar("dashboard");
        setView("Alle Einträge");
        announce("Formular für neuen Eintrag ist links bereit.");
      }
    },
    [announce, backupNow, setSidebar, setView]
  );

  return (
    <div
      className="min-h-screen w-full text-white"
      style={{ ...themeStyle, backgroundImage: "var(--page-bg)" }}
    >
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 opacity-[0.08]"
        style={{
          backgroundImage:
            "url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"220\" height=\"220\"><filter id=\"n\"><feTurbulence type=\"fractalNoise\" baseFrequency=\"0.85\" numOctaves=\"3\" stitchTiles=\"stitch\"/></filter><rect width=\"220\" height=\"220\" filter=\"url(%23n)\" opacity=\"0.45\"/></svg>')",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 opacity-[0.12]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.35) 1px, transparent 1px)",
          backgroundSize: "160px 160px",
        }}
      />

      <a
        href={`#${mainId}`}
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-black/80 focus:px-3 focus:py-2 focus:text-sm focus:text-white focus:outline-none focus:ring-2 focus:ring-white/40"
      >
        Zum Inhalt springen
      </a>

      <p id={liveRegionId} className="sr-only" role="status" aria-live="polite">
        {liveMsg}
      </p>

      <div className="mx-auto max-w-[1500px] px-6 py-8">
        <div className="flex gap-4">
          <SidebarNav active={sidebar} onActive={setSidebar} />

          <div className="flex-1 space-y-4">
            <TopBar
              projectName="Projekt C"
              view={view}
              onView={setView}
              search={search}
              onSearch={setSearch}
              onOpenData={() => setOpenData(true)}
              onOpenHelp={() => setOpenHelp(true)}
              onCreateProject={() => {
                setOpenData(true);
                announce("Projekt-Optionen geöffnet.");
              }}
              saving={saving}
              lastSavedAt={lastSavedAt}
            />

            <main id={mainId} className="space-y-4" aria-label="Inhalt">
              <div className="grid grid-cols-12 gap-4">
                <div className="col-span-12 lg:col-span-3">
                  <LeftEntryPanel onAdd={addEntry} defaultDate={defaultDate} announce={announce} />
                </div>

                <div className="col-span-12 lg:col-span-6">
                  <CenterHeaderArea selectedTypes={selectedTypes} onToggleType={toggleType} view={view} />
                </div>

                <div className="col-span-12 lg:col-span-3">
                  <RightFilterPanel
                    selectedTypes={selectedTypes}
                    onToggleType={toggleType}
                    tagMode={tagMode}
                    onTagMode={setTagMode}
                    search={search}
                    onSearch={setSearch}
                  />
                </div>
              </div>

              <div className="grid grid-cols-12 gap-4">
                <div className="col-span-12 lg:col-span-4">
                  <FavoritesPanel
                    favorites={favoriteModules}
                    onSelectModule={selectModule}
                    onToggleFavorite={toggleFavoriteModule}
                  />
                </div>
                <div className="col-span-12 lg:col-span-4">
                  <GlobalSearchPanel
                    value={globalSearch}
                    onChange={setGlobalSearch}
                    results={globalResults}
                    onSelectEntry={(entry) => {
                      setActiveEntry(entry);
                      setGlobalSearch("");
                    }}
                    onSelectModule={(target) => {
                      selectModule(target);
                      setGlobalSearch("");
                    }}
                    onSelectAction={(actionId) => {
                      handleGlobalAction(actionId);
                      setGlobalSearch("");
                    }}
                    onSelectNote={(note) => {
                      announce(`Notiz: ${note.text}`);
                      setGlobalSearch("");
                    }}
                  />
                </div>
                <div className="col-span-12 lg:col-span-4">
                  <QuickActionsPanel
                    onOpenData={() => setOpenData(true)}
                    onBackup={backupNow}
                    noteDraft={noteDraft}
                    onNoteDraft={handleNoteDraft}
                    notes={quickNotes}
                    onAddNote={addQuickNote}
                    onRemoveNote={removeQuickNote}
                    themeMode={themeMode}
                    onThemeMode={setThemeMode}
                  />
                </div>
              </div>

              <div className="grid grid-cols-12 gap-4">
                <div className="col-span-12 lg:col-span-4">
                  <EntriesList entries={filtered} onOpen={setActiveEntry} onDelete={deleteEntry} />
                </div>
                <div className="col-span-12 lg:col-span-8">
                  <Timeline entries={filtered} monthKey={monthKey} onMonthKey={setMonthKey} onOpen={setActiveEntry} />
                </div>
              </div>
            </main>
          </div>
        </div>
      </div>

      <Modal open={!!activeEntry} onClose={() => setActiveEntry(null)} title={activeEntry ? activeEntry.title : "Eintrag"}>
        {activeEntry ? <EntryDetails entry={activeEntry} /> : null}
      </Modal>

      <Modal open={openHelp} onClose={() => setOpenHelp(false)} title="Hilfe">
        <HelpContent />
      </Modal>

      <Modal open={openData} onClose={() => setOpenData(false)} title="Daten (Export / Import)">
        <DataManager
          state={appState}
          onImportState={(s) => {
            importState(s);
            setOpenData(false);
          }}
          onReset={resetAll}
          announce={announce}
        />
      </Modal>
    </div>
  );
}
