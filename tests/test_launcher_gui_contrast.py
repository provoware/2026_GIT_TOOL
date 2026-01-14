import json
import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from color_utils import contrast_ratio


class LauncherGuiContrastTests(unittest.TestCase):
    def test_launcher_gui_theme_contrast_is_accessible(self):
        config_path = Path(__file__).resolve().parents[1] / "config" / "launcher_gui.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        themes = data.get("themes", {})

        for name, entry in themes.items():
            colors = entry.get("colors", {})
            bg = colors.get("background")
            fg = colors.get("foreground")
            button_bg = colors.get("button_background")
            button_fg = colors.get("button_foreground")
            accent = colors.get("accent")
            with self.subTest(theme=name):
                self.assertGreaterEqual(contrast_ratio(bg, fg), 4.5)
                self.assertGreaterEqual(contrast_ratio(button_bg, button_fg), 4.5)
                self.assertGreaterEqual(contrast_ratio(accent, bg), 4.5)


if __name__ == "__main__":
    unittest.main()
