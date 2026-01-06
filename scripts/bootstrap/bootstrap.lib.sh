#!/usr/bin/env bash

bootstrap_require_value() {
  local value="${1:-}"
  local label="${2:-}"

  if [[ -z "$label" ]]; then
    printf "[ERROR] Interner Fehler: Label fehlt.\n" >&2
    return 1
  fi

  if [[ -z "$value" ]]; then
    printf "[ERROR] Interner Fehler: %s fehlt.\n" "$label" >&2
    return 1
  fi

  return 0
}

bootstrap_set_defaults() {
  BOOTSTRAP_PROJECT_ROOT="${BOOTSTRAP_PROJECT_ROOT:-$(pwd)}"
  BOOTSTRAP_THEME="${BOOTSTRAP_THEME:-contrast-dark}"
  BOOTSTRAP_LOG_PATH="${BOOTSTRAP_LOG_PATH:-$BOOTSTRAP_PROJECT_ROOT/data/logs/bootstrap.log}"
  BOOTSTRAP_DEBUG="${BOOTSTRAP_DEBUG:-0}"
  BOOTSTRAP_DRY_RUN="${BOOTSTRAP_DRY_RUN:-0}"
  BOOTSTRAP_SKIP_QUALITY="${BOOTSTRAP_SKIP_QUALITY:-0}"
  BOOTSTRAP_SKIP_START="${BOOTSTRAP_SKIP_START:-0}"
  BOOTSTRAP_AUTO_INSTALL="${BOOTSTRAP_AUTO_INSTALL:-1}"
}

bootstrap_init_theme() {
  local theme="$BOOTSTRAP_THEME"
  local enable_color=1

  if [[ "${NO_COLOR:-}" != "" ]] || [[ ! -t 1 ]]; then
    enable_color=0
  fi

  case "$theme" in
    contrast-dark)
      BOOTSTRAP_COLOR_INFO="\033[1;96m"
      BOOTSTRAP_COLOR_SUCCESS="\033[1;92m"
      BOOTSTRAP_COLOR_WARN="\033[1;93m"
      BOOTSTRAP_COLOR_ERROR="\033[1;91m"
      ;;
    contrast-light)
      BOOTSTRAP_COLOR_INFO="\033[1;34m"
      BOOTSTRAP_COLOR_SUCCESS="\033[1;32m"
      BOOTSTRAP_COLOR_WARN="\033[1;33m"
      BOOTSTRAP_COLOR_ERROR="\033[1;31m"
      ;;
    mono|none)
      enable_color=0
      ;;
    *)
      enable_color=0
      BOOTSTRAP_THEME="none"
      ;;
  esac

  if [[ "$enable_color" -eq 1 ]]; then
    BOOTSTRAP_USE_COLOR=1
    BOOTSTRAP_COLOR_RESET="\033[0m"
  else
    BOOTSTRAP_USE_COLOR=0
    BOOTSTRAP_COLOR_INFO=""
    BOOTSTRAP_COLOR_SUCCESS=""
    BOOTSTRAP_COLOR_WARN=""
    BOOTSTRAP_COLOR_ERROR=""
    BOOTSTRAP_COLOR_RESET=""
  fi
}

bootstrap_prepare_logging() {
  bootstrap_require_value "$BOOTSTRAP_LOG_PATH" "BOOTSTRAP_LOG_PATH" || return 1

  local log_dir
  log_dir="$(dirname "$BOOTSTRAP_LOG_PATH")"
  if [[ ! -d "$log_dir" ]]; then
    mkdir -p "$log_dir"
  fi

  if [[ ! -f "$BOOTSTRAP_LOG_PATH" ]]; then
    touch "$BOOTSTRAP_LOG_PATH"
  fi
}

bootstrap_timestamp() {
  date -u "+%Y-%m-%dT%H:%M:%SZ"
}

bootstrap_log_line() {
  local level="${1:-}"
  local message="${2:-}"

  bootstrap_require_value "$level" "level" || return 1
  bootstrap_require_value "$message" "message" || return 1

  local timestamp
  timestamp="$(bootstrap_timestamp)"
  local line="[$timestamp] [$level] $message"

  printf "%s\n" "$line" >>"$BOOTSTRAP_LOG_PATH"

  local color=""
  case "$level" in
    INFO) color="$BOOTSTRAP_COLOR_INFO" ;;
    SUCCESS) color="$BOOTSTRAP_COLOR_SUCCESS" ;;
    WARN) color="$BOOTSTRAP_COLOR_WARN" ;;
    ERROR) color="$BOOTSTRAP_COLOR_ERROR" ;;
    DEBUG) color="$BOOTSTRAP_COLOR_INFO" ;;
  esac

  if [[ "$BOOTSTRAP_USE_COLOR" -eq 1 ]]; then
    printf "%b%s%b\n" "$color" "$line" "$BOOTSTRAP_COLOR_RESET"
  else
    printf "%s\n" "$line"
  fi
}

bootstrap_log_info() {
  bootstrap_log_line "INFO" "$1"
}

bootstrap_log_success() {
  bootstrap_log_line "SUCCESS" "$1"
}

bootstrap_log_warn() {
  bootstrap_log_line "WARN" "$1"
}

bootstrap_log_error() {
  bootstrap_log_line "ERROR" "$1"
}

bootstrap_log_debug() {
  if [[ "$BOOTSTRAP_DEBUG" -eq 1 ]]; then
    bootstrap_log_line "DEBUG" "$1"
  fi
}

bootstrap_fail() {
  bootstrap_log_error "$1"
  bootstrap_log_error "Stopp. Bitte Hinweis lesen und Schritt wiederholen."
  exit 1
}

bootstrap_run_command() {
  local label="${1:-}"
  shift || true

  bootstrap_require_value "$label" "label" || return 1
  if [[ "$#" -eq 0 ]]; then
    bootstrap_fail "Interner Fehler: Kein Kommando für $label."
  fi

  bootstrap_log_info "$label startet."
  bootstrap_log_debug "Befehl: $*"

  if [[ "$BOOTSTRAP_DRY_RUN" -eq 1 ]]; then
    bootstrap_log_warn "Dry-Run aktiv. Befehl wird übersprungen."
    bootstrap_log_success "$label übersprungen (Dry-Run)."
    return 0
  fi

  "$@" 2>&1 | tee -a "$BOOTSTRAP_LOG_PATH"
  local exit_code=${PIPESTATUS[0]}
  if [[ "$exit_code" -ne 0 ]]; then
    bootstrap_fail "$label fehlgeschlagen. Code: $exit_code."
  fi

  bootstrap_log_success "$label abgeschlossen."
}

bootstrap_check_command() {
  local cmd="${1:-}"
  local hint="${2:-}"
  bootstrap_require_value "$cmd" "command" || return 1
  bootstrap_require_value "$hint" "hint" || return 1

  local resolved
  resolved="$(command -v "$cmd" || true)"
  if [[ -z "$resolved" ]]; then
    bootstrap_fail "$hint"
  fi

  bootstrap_log_success "Werkzeug gefunden: $cmd."
}

bootstrap_version_ge() {
  local current="${1:-}"
  local minimum="${2:-}"
  bootstrap_require_value "$current" "current version" || return 1
  bootstrap_require_value "$minimum" "minimum version" || return 1

  IFS=. read -r c_major c_minor c_patch <<<"$current"
  IFS=. read -r m_major m_minor m_patch <<<"$minimum"

  c_patch=${c_patch:-0}
  m_patch=${m_patch:-0}

  if ((c_major > m_major)); then
    return 0
  fi
  if ((c_major < m_major)); then
    return 1
  fi
  if ((c_minor > m_minor)); then
    return 0
  fi
  if ((c_minor < m_minor)); then
    return 1
  fi
  if ((c_patch >= m_patch)); then
    return 0
  fi
  return 1
}

bootstrap_check_node_version() {
  local minimum_version="${1:-}"
  bootstrap_require_value "$minimum_version" "minimum_version" || return 1

  local current_version
  current_version="$(node -p "process.versions.node" 2>/dev/null || true)"
  bootstrap_require_value "$current_version" "node version" || return 1

  if ! bootstrap_version_ge "$current_version" "$minimum_version"; then
    bootstrap_fail "Node.js ist zu alt. Gefunden: $current_version. Benötigt: $minimum_version."
  fi

  bootstrap_log_success "Node.js Version OK: $current_version."
}

bootstrap_check_configs() {
  local missing=0
  local required_paths=(
    "$BOOTSTRAP_PROJECT_ROOT/config/system/standards.manifest.json"
    "$BOOTSTRAP_PROJECT_ROOT/config/system/quality.manifest.json"
    "$BOOTSTRAP_PROJECT_ROOT/config/user/app.config.json"
    "$BOOTSTRAP_PROJECT_ROOT/config/user/quality.config.json"
    "$BOOTSTRAP_PROJECT_ROOT/data/templates_seed.json"
    "$BOOTSTRAP_PROJECT_ROOT/data/templates.json"
    "$BOOTSTRAP_PROJECT_ROOT/data/templates_stats.json"
    "$BOOTSTRAP_PROJECT_ROOT/data/templates_stats_schema.json"
  )

  for file_path in "${required_paths[@]}"; do
    if [[ ! -f "$file_path" ]]; then
      bootstrap_log_warn "Fehlende Datei: $file_path."
      missing=1
    fi
  done

  if [[ "$missing" -eq 1 ]]; then
    bootstrap_log_warn "Es fehlen Konfigurationen oder Daten. Ich repariere das jetzt."
    bootstrap_run_command "Startprüfung (Bootstrap) Initialisierung" \
      node "$BOOTSTRAP_PROJECT_ROOT/scripts/bootstrap/init.mjs"
  else
    bootstrap_log_success "Konfigurationen und Daten sind vorhanden."
  fi
}

bootstrap_install_dependencies() {
  if [[ -d "$BOOTSTRAP_PROJECT_ROOT/node_modules" ]]; then
    bootstrap_log_info "node_modules vorhanden. Ich prüfe die Abhängigkeiten."
    if npm ls --depth=0 >/dev/null 2>&1; then
      bootstrap_log_success "Abhängigkeiten sind vollständig."
      return 0
    fi
    bootstrap_log_warn "npm meldet fehlende oder kaputte Abhängigkeiten."
  else
    bootstrap_log_warn "node_modules fehlt."
  fi

  if [[ "$BOOTSTRAP_AUTO_INSTALL" -eq 1 ]]; then
    bootstrap_run_command "Abhängigkeiten installieren" npm install
  else
    bootstrap_fail "Abhängigkeiten fehlen. Bitte 'npm install' ausführen."
  fi
}

bootstrap_print_help() {
  bootstrap_log_info "Hilfe in einfacher Sprache:"
  bootstrap_log_info "- BOOTSTRAP_THEME: contrast-dark | contrast-light | none"
  bootstrap_log_info "- BOOTSTRAP_DEBUG=1 aktiviert Debug-Ausgaben (Fehlersuche)."
  bootstrap_log_info "- BOOTSTRAP_DRY_RUN=1 simuliert Schritte ohne Ausführung."
  bootstrap_log_info "- BOOTSTRAP_AUTO_INSTALL=0 deaktiviert Auto-Installation."
  bootstrap_log_info "- BOOTSTRAP_SKIP_QUALITY=1 überspringt Qualitätsprüfung."
  bootstrap_log_info "- BOOTSTRAP_SKIP_START=1 überspringt App-Start."
}

bootstrap_main() {
  bootstrap_set_defaults
  bootstrap_init_theme
  bootstrap_prepare_logging

  if [[ "$BOOTSTRAP_DEBUG" -eq 1 ]]; then
    set -x
  fi

  bootstrap_log_info "Bootstrap-Check startet. Ich prüfe alles Schritt für Schritt."
  bootstrap_log_info "Aktives Farbthema (Theme): $BOOTSTRAP_THEME."
  bootstrap_log_info "Logs liegen unter: $BOOTSTRAP_LOG_PATH."

  bootstrap_print_help

  bootstrap_check_command "node" "Node.js fehlt. Bitte Node.js installieren (JavaScript-Laufzeit). Beispiel: 'nvm install 20'."
  bootstrap_check_command "npm" "npm fehlt. Bitte npm installieren (Paketmanager). Beispiel: Node.js neu installieren."

  bootstrap_check_node_version "18.0.0"

  bootstrap_check_configs

  bootstrap_install_dependencies

  if [[ "$BOOTSTRAP_SKIP_QUALITY" -eq 1 ]]; then
    bootstrap_log_warn "Qualitätsprüfung ist deaktiviert."
  else
    bootstrap_run_command "Qualitätsprüfung (Code-Check)" npm run quality:auto
  fi

  if [[ "$BOOTSTRAP_SKIP_START" -eq 1 ]]; then
    bootstrap_log_warn "App-Start ist deaktiviert."
  else
    bootstrap_run_command "Electron-Anwendung starten" npm run start
  fi

  bootstrap_log_success "Bootstrap abgeschlossen. Alles bereit."
}
