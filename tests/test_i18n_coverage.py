"""Every T('key') / flash key referenced in templates and code must exist in
the string table — otherwise it renders as a raw key."""
import re
from pathlib import Path

from app.i18n import STRINGS

ROOT = Path(__file__).parent.parent / "app"

TEMPLATE_RE = re.compile(r"T\('([A-Za-z0-9_]+)'")
FLASH_RE = re.compile(r"flash\(request,\s*[\"']([A-Za-z0-9_]+)[\"']")


def collected_keys():
    keys = set()
    for tpl in (ROOT / "templates").glob("*.html"):
        for m in TEMPLATE_RE.finditer(tpl.read_text(encoding="utf-8")):
            keys.add(m.group(1))
    for py in ROOT.rglob("*.py"):
        for m in FLASH_RE.finditer(py.read_text(encoding="utf-8")):
            keys.add(m.group(1))
    return keys


def test_static_keys_exist():
    missing = set()
    for key in collected_keys():
        # dynamic prefixes like T('int_' + s) are checked separately below
        if key.endswith("_"):
            continue
        if key in STRINGS:
            continue
        missing.add(key)
    assert not missing, f"missing i18n keys: {sorted(missing)}"


def test_dynamic_prefix_keys_exist():
    from app import models
    from app.services import matching  # noqa: F401

    for role in models.ROLES:
        assert f"role_{role}" in STRINGS
    for s in models.TRAINING_SKILLS + ["other", "any"]:
        assert f"skill_{s}" in STRINGS
    for s in models.MARKET_STATUSES:
        assert f"status_{s}" in STRINGS
    for s in models.NT_SQUADS:
        assert f"squad_{s}" in STRINGS
    for tm in models.DECLARATION_TIMINGS:
        assert f"timing_{tm}" in STRINGS
    for st in ("open", "accepted", "declined", "withdrawn"):
        assert f"int_{st}" in STRINGS
    for i in range(9):
        assert f"spec_id_{i}" in STRINGS
    for i in range(5):
        assert f"band_{i}" in STRINGS
    assert "band_unknown" in STRINGS


def test_every_string_has_bg():
    missing = [k for k, v in STRINGS.items() if "bg" not in v or "en" not in v]
    assert not missing, f"strings missing a locale: {missing}"
