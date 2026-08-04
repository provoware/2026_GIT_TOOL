from module_history import create_history_entry, format_history


def test_history_keeps_version_status_and_plain_text():
    entry = create_history_entry("1.2.0", "ok", "Modul aktiviert.")

    assert entry.version == "1.2.0"
    assert "Version 1.2.0 · ok: Modul aktiviert." in format_history([entry])


def test_empty_history_has_clear_message():
    assert format_history([]) == "Noch keine Änderungen in dieser Sitzung."
