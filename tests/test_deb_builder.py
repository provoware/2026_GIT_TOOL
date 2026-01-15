import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from deb_builder import DebPackageConfig, build_control_content, prepare_deb_structure


class DebBuilderTests(unittest.TestCase):
    def test_prepare_deb_structure_writes_control_and_desktop(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir()
            (repo_root / "scripts").mkdir()
            (repo_root / "scripts" / "start.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (repo_root / "assets" / "icons").mkdir(parents=True)
            (repo_root / "assets" / "icons" / "icon.svg").write_text(
                "<svg></svg>", encoding="utf-8"
            )
            (repo_root / "config").mkdir()
            (repo_root / "config" / "desktop_entry.json").write_text(
                json.dumps(
                    {
                        "app_name": "Demo",
                        "app_id": "demo_app",
                        "comment": "Demo",
                        "exec": "./scripts/start.sh",
                        "icon_name": "demo_icon",
                        "categories": ["Utility"],
                        "keywords": [],
                        "terminal": False,
                    }
                ),
                encoding="utf-8",
            )

            config = DebPackageConfig(
                package_name="demo",
                version="0.1.0",
                maintainer="Demo <demo@example.com>",
                description="Demo",
                architecture="amd64",
                depends=["python3"],
                install_root="/opt/demo",
                desktop_entry_config=Path("config/desktop_entry.json"),
                icon_source=Path("assets/icons/icon.svg"),
                exclude_paths=[],
                output_dir=Path("dist"),
                postinst_script=None,
            )
            staging_root = Path(tmpdir) / "staging"
            prepare_deb_structure(repo_root, config, staging_root)

            control_path = staging_root / "DEBIAN" / "control"
            desktop_path = staging_root / "usr" / "share" / "applications" / "demo_app.desktop"
            icon_path = (
                staging_root
                / "usr"
                / "share"
                / "icons"
                / "hicolor"
                / "scalable"
                / "apps"
                / "demo_icon.svg"
            )

            self.assertTrue(control_path.exists())
            self.assertTrue(desktop_path.exists())
            self.assertTrue(icon_path.exists())

    def test_build_control_content_contains_metadata(self):
        config = DebPackageConfig(
            package_name="demo",
            version="1.0.0",
            maintainer="Demo <demo@example.com>",
            description="Demo Paket",
            architecture="amd64",
            depends=["python3"],
            install_root="/opt/demo",
            desktop_entry_config=Path("config/desktop_entry.json"),
            icon_source=Path("assets/icons/icon.svg"),
            exclude_paths=[],
            output_dir=Path("dist"),
            postinst_script=None,
        )
        control = build_control_content(config)
        self.assertIn("Package: demo", control)
        self.assertIn("Version: 1.0.0", control)
        self.assertIn("Depends: python3", control)


if __name__ == "__main__":
    unittest.main()
