from __future__ import annotations

import json
from pathlib import Path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_translation_keys_match_strings_definition() -> None:
    root = Path(__file__).resolve().parents[1]
    strings = _load_json(
        root / "custom_components" / "lueftungsempfehlung" / "strings.json"
    )
    de = _load_json(
        root / "custom_components" / "lueftungsempfehlung" / "translations" / "de.json"
    )
    en = _load_json(
        root / "custom_components" / "lueftungsempfehlung" / "translations" / "en.json"
    )

    sections = [
        ("config", "step", "user", "data"),
        ("config", "step", "notifications", "data"),
        ("config", "step", "advanced", "data"),
        ("options", "step", "init", "data"),
        ("options", "step", "notifications", "data"),
        ("options", "step", "advanced", "data"),
    ]

    for section in sections:
        ref = strings
        de_ref = de
        en_ref = en
        for key in section:
            ref = ref[key]
            de_ref = de_ref[key]
            en_ref = en_ref[key]

        assert set(de_ref.keys()) == set(ref.keys())
        assert set(en_ref.keys()) == set(ref.keys())
