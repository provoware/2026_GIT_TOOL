#!/usr/bin/env python3
"""Headless Google-Chrome interaction probe for the complete Provoware Memo web UI."""

from __future__ import annotations

import argparse
import dataclasses
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from system import web_server


PROBE_JS = r'''
(() => {
  const finish = (status, detail) => {
    const marker = document.createElement("div");
    marker.id = "provoware-e2e-result";
    marker.dataset.status = status;
    marker.textContent = detail;
    document.body.appendChild(marker);
  };
  const wait = (attempt = 0) => {
    if (document.documentElement.dataset.appReady !== "true") {
      if (attempt > 120) return finish("failed", `App nicht bereit: ${document.documentElement.dataset.appReady || "leer"}`);
      return setTimeout(() => wait(attempt + 1), 100);
    }
    try {
      const buttons = [...document.querySelectorAll("[data-view]")];
      const views = [...new Set(buttons.map((button) => button.dataset.view))];
      for (const view of views) {
        const button = buttons.find((item) => item.dataset.view === view);
        button.click();
        const panel = document.querySelector(`[data-panel="${view}"]`);
        if (!panel || !panel.classList.contains("active")) throw new Error(`Navigation ohne Wirkung: ${view}`);
      }
      const moduleButton = document.querySelector("[data-module-id][data-module-action]");
      if (!moduleButton) throw new Error("Keine Modulaktion vorhanden");
      moduleButton.click();
      const dialog = document.getElementById("actionDialog");
      if (!dialog || !dialog.hasAttribute("open")) throw new Error("Modulaktionsdialog öffnet nicht");
      document.querySelector('[data-action="close-action-dialog"]').click();
      if (dialog.hasAttribute("open")) throw new Error("Modulaktionsdialog schließt nicht");
      const fileView = document.querySelector('[data-view="files"]');
      fileView.click();
      if (!document.getElementById("fileTableBody")) throw new Error("Datei-Manager fehlt");
      if (document.getElementById("fatalError") && !document.getElementById("fatalError").hidden) {
        throw new Error(document.getElementById("fatalErrorText").textContent || "Fataler Oberflächenfehler");
      }
      finish("passed", `${views.length} Navigationen und Moduldialog geprüft`);
    } catch (error) {
      finish("failed", error.message || String(error));
    }
  };
  wait();
})();
'''


def find_chrome() -> str:
    for candidate in ("google-chrome", "google-chrome-stable"):
        executable = shutil.which(candidate)
        if executable:
            return executable
    raise RuntimeError("Google Chrome ist für den E2E-Test nicht installiert.")


def run_probe(root: Path, timeout: int) -> None:
    chrome = find_chrome()
    with tempfile.TemporaryDirectory(prefix="provoware_web_probe_") as temp:
        static_dir = Path(temp) / "web"
        shutil.copytree(root / "web", static_dir)
        index = static_dir / "index.html"
        html = index.read_text(encoding="utf-8").replace(
            "</body>", '<script src="/e2e-probe.js" defer></script></body>'
        )
        index.write_text(html, encoding="utf-8")
        (static_dir / "e2e-probe.js").write_text(PROBE_JS, encoding="utf-8")

        config = web_server.load_config(root / "config" / "web_server.json", root=root)
        config = dataclasses.replace(config, static_dir=static_dir)
        api = web_server.ProvowareApi(root)
        server, port, _preferred = web_server.bind_server(config, api, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{port}/"
        try:
            completed = subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--hide-scrollbars",
                    f"--virtual-time-budget={timeout * 1000}",
                    "--dump-dom",
                    url,
                ],
                text=True,
                capture_output=True,
                timeout=timeout + 20,
                check=False,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        output = completed.stdout
        if completed.returncode != 0:
            raise RuntimeError(f"Google-Chrome-Probe fehlgeschlagen: {completed.stderr[-4000:]}")
        if 'id="provoware-e2e-result"' not in output or 'data-status="passed"' not in output:
            marker = output.rsplit("provoware-e2e-result", 1)[-1][:1000]
            raise RuntimeError(f"Oberflächeninteraktion nicht bestanden: {marker or completed.stderr[-2000:]}")
        print("Webinteraktions-Probe: OK — Navigation, Moduldialog und Datei-Manager reagieren.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--timeout", type=int, default=15)
    args = parser.parse_args()
    run_probe(args.root.resolve(), args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
