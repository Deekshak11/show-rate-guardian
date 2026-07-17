from __future__ import annotations

import sys
from pathlib import Path

FACTORY_SCRIPTS = Path(__file__).resolve().parents[2] / "showrate-guardian-factory" / "scripts"
sys.path.insert(0, str(FACTORY_SCRIPTS))

from validate_profile import main  # type: ignore


if __name__ == "__main__":
    default_profile = Path(__file__).resolve().parents[1] / "references" / "profile.yaml"
    raise SystemExit(main(default_profile=default_profile))
