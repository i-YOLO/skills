#!/usr/bin/env python3
"""Validate MADEM's top-level reusable asset registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {"candidate", "project-proven", "library-approved"}


def add_check(
    checks: list[dict[str, Any]],
    condition: bool,
    check_id: str,
    detail: str,
    **extra: Any,
) -> None:
    checks.append(
        {
            "id": check_id,
            "status": "pass" if condition else "fail",
            "detail": detail,
            **extra,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    registry_path = args.registry.expanduser().resolve()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    root = registry_path.parent
    checks: list[dict[str, Any]] = []

    packs = registry.get("packs")
    add_check(
        checks,
        isinstance(packs, list) and bool(packs),
        "packs-present",
        "registry contains at least one asset pack",
    )
    packs = packs if isinstance(packs, list) else []
    pack_ids = [pack.get("id") for pack in packs if isinstance(pack, dict)]
    add_check(
        checks,
        len(pack_ids) == len(set(pack_ids)) and all(isinstance(item, str) for item in pack_ids),
        "pack-ids",
        "pack IDs are non-empty strings and unique",
        pack_ids=pack_ids,
    )

    allowed_defaults = set(
        registry.get("selection_policy", {}).get("default_allowed_statuses", [])
    )
    add_check(
        checks,
        allowed_defaults <= {"project-proven", "library-approved"}
        and "candidate" not in allowed_defaults,
        "default-status-policy",
        "candidate packs are excluded from default automatic selection",
        default_allowed_statuses=sorted(allowed_defaults),
    )

    for pack in packs:
        if not isinstance(pack, dict):
            add_check(checks, False, "pack-object", "every pack entry is an object")
            continue
        pack_id = str(pack.get("id", "<missing>"))
        status = pack.get("status")
        add_check(
            checks,
            status in ALLOWED_STATUSES,
            "pack-status",
            f"{pack_id} uses an allowed status",
            pack_id=pack_id,
            value=status,
        )
        relative_path = pack.get("path")
        pack_path = root / str(relative_path)
        add_check(
            checks,
            isinstance(relative_path, str) and pack_path.exists(),
            "pack-path",
            f"{pack_id} pack path exists",
            pack_id=pack_id,
            path=str(relative_path),
        )
        catalog = pack.get("catalog")
        if catalog is not None:
            catalog_path = root / str(catalog)
            add_check(
                checks,
                isinstance(catalog, str) and catalog_path.is_file(),
                "pack-catalog",
                f"{pack_id} catalog exists",
                pack_id=pack_id,
                catalog=str(catalog),
            )
            if catalog_path.is_file():
                catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))
                catalog_status = catalog_data.get("status")
                if catalog_status is not None:
                    add_check(
                        checks,
                        catalog_status == status,
                        "catalog-status-match",
                        f"{pack_id} registry and catalog statuses match",
                        pack_id=pack_id,
                        registry_status=status,
                        catalog_status=catalog_status,
                    )
        for entrypoint in pack.get("entrypoints", []):
            entrypoint_path = root / str(entrypoint)
            add_check(
                checks,
                isinstance(entrypoint, str) and entrypoint_path.is_file(),
                "entrypoint",
                f"{pack_id} entrypoint exists",
                pack_id=pack_id,
                entrypoint=str(entrypoint),
            )
        if status == "candidate":
            add_check(
                checks,
                pack.get("default_selectable") is False,
                "candidate-selection",
                f"{pack_id} candidate is not default-selectable",
                pack_id=pack_id,
            )

    failures = [check for check in checks if check["status"] == "fail"]
    result = {
        "status": "pass" if not failures else "fail",
        "registry": str(registry_path),
        "summary": {
            "pack_count": len(packs),
            "check_count": len(checks),
            "failure_count": len(failures),
        },
        "checks": checks,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = args.out.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
