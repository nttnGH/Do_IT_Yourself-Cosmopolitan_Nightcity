#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CVLPV language filter — Option B (config-driven languages) — res/ layout

Layout:
  /PolyglotV/
     filter_cvlpv.py  (or CVLPV_Filter.exe)
     /res/
         CVLPV_cdt_data.json
         CVLPV_cnc_data.json
         CVLPV_id_info.json
         CVLPV_languages_config.json   <-- controls languages & prompts
         (outputs:)
         CVLPV_filter_report.json
         /backup_originals/      <-- originals moved here

Behavior:
- Loads language definitions from res/CVLPV_languages_config.json:
    {
      "languages": [
        { "code": "jpn", "aliases": ["jpn","jp","japanese"], "prompt": "....?" },
        { "code": "mex", "aliases": ["mex","es","spa","spanish"], "prompt": "....?" },
        ...
      ]
    }
- Builds ID -> language map by scanning CDT & CNC (recursive 'Language' search).
- Prompts (English, strict Yes/Y or No/N) once per configured language.
- Allowed languages = the set of languages answered "Yes".
- Filtering preserves schema:
    * CDT/CNC: keep unknown-language IDs; remove disallowed IDs.
    * ID_INFO: remove unknown-language IDs and disallowed IDs.
- Safe replace: write temps → move originals to res/backup_originals → promote temps.
- Writes a detailed JSON report in res/.

Run:
  python filter_cvlpv.py
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Set, Tuple, Optional, List, Union

Json = Union[dict, list, str, int, float, bool, None]

# ---------------------------
# Base / paths (works for script or PyInstaller .exe)
# ---------------------------

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "executable"):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

BASE_DIR = get_base_dir()
RES_DIR = BASE_DIR / "res"
CONFIG_PATH = RES_DIR / "CVLPV_languages_config.json"

# ---------------------------
# Language config & aliases
# ---------------------------

LANGS_CFG: List[dict] = []          # list of {"code","aliases","prompt"}
LANG_ALIASES: Dict[str, str] = {}   # alias(lower) -> code(lower)

def load_language_config() -> None:
    """
    Load CVLPV_languages_config.json. If missing or invalid, fall back to jpn/mex defaults.
    """
    global LANGS_CFG, LANG_ALIASES
    default_cfg = [
        {"code": "jpn", "aliases": ["jpn","jp","japanese"],
         "prompt": "Do you want V to speak their native language + Japanese?"},
        {"code": "mex", "aliases": ["mex","es","spa","spanish"],
         "prompt": "Do you want V to speak their native language + Spanish?"}
    ]
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        langs = cfg.get("languages", [])
        if not isinstance(langs, list) or not langs:
            LANGS_CFG = default_cfg
        else:
            # normalize entries
            norm: List[dict] = []
            for e in langs:
                if not isinstance(e, dict): continue
                code = str(e.get("code","")).strip().lower()
                if not code: continue
                aliases = [str(a).strip().lower() for a in e.get("aliases", []) if isinstance(a, (str,int,float))]
                prompt = e.get("prompt", f"Allow language '{code}'?")
                norm.append({"code": code, "aliases": aliases, "prompt": prompt})
            LANGS_CFG = norm or default_cfg
    except Exception:
        LANGS_CFG = default_cfg

    # Build alias map
    LANG_ALIASES.clear()
    for e in LANGS_CFG:
        code = e["code"]
        # map the code itself too
        LANG_ALIASES[code] = code
        for a in e.get("aliases", []):
            LANG_ALIASES[a] = code

# ---------------------------
# I/O utilities
# ---------------------------

def load_json(path: Path) -> Json:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: Path, data: Json, sort_keys: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=sort_keys)

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def is_id_key(s: str) -> bool:
    return isinstance(s, str) and s.isdigit()

def normalize_lang(val: Any) -> Optional[str]:
    """
    Use aliases from config. Returns normalized language code, or None if unknown.
    """
    if not isinstance(val, str):
        return None
    return LANG_ALIASES.get(val.strip().lower())

def find_language_recursive(obj: Json) -> Optional[str]:
    """Recursively search for 'Language' and return normalized code if found."""
    if isinstance(obj, dict):
        if "Language" in obj:
            lang = normalize_lang(obj["Language"])
            if lang:
                return lang
        for v in obj.values():
            res = find_language_recursive(v)
            if res:
                return res
    elif isinstance(obj, list):
        for v in obj:
            res = find_language_recursive(v)
            if res:
                return res
    return None

def collect_ids_in_doc(data: Json) -> Set[str]:
    """
    Collect ID-like strings from:
      - dict keys that look like IDs
      - items inside any "Ids": [ ... ] lists
    """
    found: Set[str] = set()
    def walk(x: Json):
        if isinstance(x, dict):
            for k, v in x.items():
                if is_id_key(k):
                    found.add(k)
                if k == "Ids" and isinstance(v, list):
                    for it in v:
                        if isinstance(it, str) and is_id_key(it):
                            found.add(it)
                walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)
    walk(data)
    return found

# ---------------------------
# Step 1: Build ID -> Language map
# ---------------------------

def build_id_language_map(*sources: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Set[str]]]:
    """
    Consider only dicts keyed by IDs at top-level when mapping:
      { "<id>": { ... "Language": "jpn" ... }, ... }
    """
    id_to_lang: Dict[str, str] = {}
    conflicts: Dict[str, Set[str]] = {}

    for src in sources:
        if not isinstance(src, dict):
            continue
        for k, v in src.items():
            if is_id_key(k):
                lang = find_language_recursive(v)
                if lang:
                    prev = id_to_lang.get(k)
                    if prev and prev != lang:
                        conflicts.setdefault(k, set([prev])).add(lang)
                    else:
                        id_to_lang[k] = lang

    # Deterministic pick for unresolved conflicts
    for cid, langs in conflicts.items():
        if cid not in id_to_lang and langs:
            id_to_lang[cid] = sorted(langs)[0]
    return id_to_lang, conflicts

# ---------------------------
# Step 2: Prompts (English, strict Y/N)
# ---------------------------

def prompt_yes_no(en_prompt: str) -> bool:
    while True:
        ans = input(en_prompt + " (Yes/Y or No/N): ").strip().lower()
        if ans in ("yes", "y"):
            return True
        if ans in ("no", "n"):
            return False
        print("Response not understood. Please answer with Yes/Y or No/N.")

def compute_allowed_languages() -> Set[str]:
    """
    Ask a Yes/No question for every configured language (LANGS_CFG).
    Returns the set of allowed codes.
    """
    allowed: Set[str] = set()
    for e in LANGS_CFG:
        code = e["code"]
        prompt = e.get("prompt", f"Allow language '{code}'?")
        if prompt_yes_no(prompt):
            allowed.add(code)
    return allowed

# ---------------------------
# Filtering while preserving schema
# ---------------------------

class FileStats:
    def __init__(self) -> None:
        self.kept_allowed_ids: List[str] = []
        self.kept_unknown_ids: List[str] = []
        self.removed_disallowed_ids: List[str] = []
        self.removed_unknown_ids: List[str] = []

    def as_dict(self) -> Dict[str, Any]:
        return {
            "kept_allowed_ids": self.kept_allowed_ids,
            "kept_unknown_ids": self.kept_unknown_ids,
            "removed_disallowed_ids": self.removed_disallowed_ids,
            "removed_unknown_ids": self.removed_unknown_ids,
            "counts": {
                "kept_allowed": len(self.kept_allowed_ids),
                "kept_unknown": len(self.kept_unknown_ids),
                "removed_disallowed": len(self.removed_disallowed_ids),
                "removed_unknown": len(self.removed_unknown_ids),
            }
        }

def filter_structure_preserving_ids(
    data: Json,
    id_to_lang: Dict[str, str],
    allowed_langs: Set[str],
    stats: FileStats,
    unknown_ids_accumulator: Set[str],
    drop_unknown_in_info: bool = False
) -> Json:
    """
    Deep-copy structure while:
      - Filtering dict entries keyed by ID (drop if not allowed/unknown per policy),
      - Filtering "Ids": [ ... ] lists (drop items if not allowed/unknown per policy),
      - Everything else unchanged.
    """
    if not isinstance(data, (dict, list)):
        return data

    if isinstance(data, list):
        return [
            filter_structure_preserving_ids(
                x, id_to_lang, allowed_langs, stats, unknown_ids_accumulator, drop_unknown_in_info
            )
            for x in data
        ]

    out: Dict[str, Any] = {}

    # Filter "Ids" lists
    for k, v in data.items():
        if k == "Ids" and isinstance(v, list):
            kept_items: List[Any] = []
            for item in v:
                if isinstance(item, str) and is_id_key(item):
                    lang = id_to_lang.get(item)
                    if lang is None:
                        if drop_unknown_in_info:
                            stats.removed_unknown_ids.append(item)
                            unknown_ids_accumulator.add(item)
                            continue
                        kept_items.append(item)
                        stats.kept_unknown_ids.append(item)
                        unknown_ids_accumulator.add(item)
                    else:
                        if lang in allowed_langs:
                            kept_items.append(item)
                            stats.kept_allowed_ids.append(item)
                        else:
                            stats.removed_disallowed_ids.append(item)
                else:
                    kept_items.append(item)
            out[k] = kept_items
        else:
            out[k] = v

    # Filter ID-keyed dict entries
    result: Dict[str, Any] = {}
    for k, v in out.items():
        if is_id_key(k):
            lang = id_to_lang.get(k)
            if lang is None:
                if drop_unknown_in_info:
                    stats.removed_unknown_ids.append(k)
                    unknown_ids_accumulator.add(k)
                    continue
                result[k] = filter_structure_preserving_ids(
                    v, id_to_lang, allowed_langs, stats, unknown_ids_accumulator, drop_unknown_in_info
                )
                stats.kept_unknown_ids.append(k)
                unknown_ids_accumulator.add(k)
            else:
                if lang in allowed_langs:
                    result[k] = filter_structure_preserving_ids(
                        v, id_to_lang, allowed_langs, stats, unknown_ids_accumulator, drop_unknown_in_info
                    )
                    stats.kept_allowed_ids.append(k)
                else:
                    stats.removed_disallowed_ids.append(k)
        else:
            result[k] = filter_structure_preserving_ids(
                v, id_to_lang, allowed_langs, stats, unknown_ids_accumulator, drop_unknown_in_info
            )

    return result

# ---------------------------
# Atomic replacement helpers
# ---------------------------

def write_temp_then_swap(
    originals: Dict[str, Path],
    new_contents: Dict[str, Json],
    backup_dir: Path,
    sort_keys: bool = False
) -> None:
    temps: Dict[str, Path] = {}
    try:
        # 1) Write temps
        for label, orig_path in originals.items():
            tmp_path = orig_path.with_suffix(orig_path.suffix + ".tmp.new")
            write_json(tmp_path, new_contents[label], sort_keys=sort_keys)
            temps[label] = tmp_path

        # 2) Backup originals
        ensure_dir(backup_dir)
        for _, orig_path in originals.items():
            dest = backup_dir / orig_path.name
            if dest.exists():
                i = 1
                while True:
                    alt = backup_dir / f"{orig_path.stem}.bak{str(i)}{orig_path.suffix}"
                    if not alt.exists():
                        dest = alt
                        break
                    i += 1
            shutil.move(str(orig_path), str(dest))

        # 3) Promote temps
        for label, orig_path in originals.items():
            shutil.move(str(temps[label]), str(orig_path))

    except Exception as e:
        # best-effort cleanup
        for p in temps.values():
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        raise RuntimeError(f"Atomic swap failed: {e}") from e

# ---------------------------
# Main
# ---------------------------

def main() -> int:
    # Load language config first (so normalize_lang works)
    load_language_config()

    # Defaults under ./res/
    default_cdt    = RES_DIR / "CVLPV_cdt_data.json"
    default_cnc    = RES_DIR / "CVLPV_cnc_data.json"
    default_info   = RES_DIR / "CVLPV_id_info.json"
    default_report = RES_DIR / "CVLPV_filter_report.json"
    default_backup = RES_DIR / "backup_originals"

    parser = argparse.ArgumentParser(
        description="Filter CVLPV JSONs by language (config-driven) while preserving original structure. Uses ./res/ by default."
    )
    parser.add_argument("--cdt", default=str(default_cdt))
    parser.add_argument("--cnc", default=str(default_cnc))
    parser.add_argument("--info", default=str(default_info))
    parser.add_argument("--report", default=str(default_report))
    parser.add_argument("--backup-dir", default=str(default_backup))
    parser.add_argument("--sort-keys", action="store_true")
    args = parser.parse_args()

    # Resolve paths
    cdt_path   = Path(args.cdt).resolve()
    cnc_path   = Path(args.cnc).resolve()
    info_path  = Path(args.info).resolve()
    report_path = Path(args.report).resolve()
    backup_dir  = Path(args.backup_dir).resolve()

    # Sanity check
    if not cdt_path.exists() or not cnc_path.exists() or not info_path.exists():
        print("ERROR: One or more input files do not exist. Expected default layout under ./res/ or pass explicit paths.\n"
              f"  CDT : {cdt_path}\n  CNC : {cnc_path}\n  INFO: {info_path}", file=sys.stderr)
        return 1

    # Load sources
    try:
        cdt = load_json(cdt_path)
        cnc = load_json(cnc_path)
        info = load_json(info_path)
    except Exception as e:
        print(f"ERROR: failed to load input JSON(s): {e}", file=sys.stderr)
        return 1

    # Build ID -> language map
    id_to_lang, conflicts = build_id_language_map(cdt, cnc)

    # Ask prompts from config
    allowed_langs = compute_allowed_languages()
    print(f"Allowed languages: {sorted(list(allowed_langs)) or 'none'}")

    # Inventory for cross-checks
    ids_in_cdt = collect_ids_in_doc(cdt)
    ids_in_cnc = collect_ids_in_doc(cnc)
    ids_in_info = collect_ids_in_doc(info)
    ids_in_sources = ids_in_cdt | ids_in_cnc

    # Filtering
    unknown_ids_global: Set[str] = set()

    cdt_stats = FileStats()
    cnc_stats = FileStats()
    info_stats = FileStats()

    cdt_new = filter_structure_preserving_ids(
        cdt, id_to_lang, allowed_langs, cdt_stats, unknown_ids_global, drop_unknown_in_info=False
    )
    cnc_new = filter_structure_preserving_ids(
        cnc, id_to_lang, allowed_langs, cnc_stats, unknown_ids_global, drop_unknown_in_info=False
    )
    info_new = filter_structure_preserving_ids(
        info, id_to_lang, allowed_langs, info_stats, unknown_ids_global, drop_unknown_in_info=True
    )

    # Replace originals in res/
    originals = {"cdt": cdt_path, "cnc": cnc_path, "info": info_path}
    new_contents = {"cdt": cdt_new, "cnc": cnc_new, "info": info_new}

    try:
        write_temp_then_swap(originals, new_contents, backup_dir, sort_keys=args.sort_keys)
    except Exception as e:
        print(f"ERROR: failed to replace originals: {e}", file=sys.stderr)
        return 1

    # Report
    report = {
        "summary": {
            "allowed_languages": sorted(list(allowed_langs)),
            "configured_languages": [e["code"] for e in LANGS_CFG],
            "total_ids_mapped": len(id_to_lang),
            "conflict_count": len(conflicts),
            "backup_dir": str(backup_dir),
            "config_path": str(CONFIG_PATH),
        },
        "conflicting_ids": {k: sorted(list(v)) for k, v in conflicts.items()},
        "unknown_language_ids": sorted(list(unknown_ids_global)),
        "cross_checks": {
            "ids_in_cdt_not_in_info": sorted(list(ids_in_cdt - ids_in_info)),
            "ids_in_cnc_not_in_info": sorted(list(ids_in_cnc - ids_in_info)),
            "ids_in_info_not_in_sources": sorted(list(ids_in_info - ids_in_sources)),
        },
        "files": {
            "cdt": cdt_stats.as_dict(),
            "cnc": cnc_stats.as_dict(),
            "id_info": info_stats.as_dict(),
        },
        "notes": [
            "Languages, aliases and prompts are driven by res/CVLPV_languages_config.json.",
            "Exact schema preserved; only ID entries are removed per policy.",
            "CDT/CNC keep unknown-language IDs; ID_INFO removes unknown-language IDs.",
            "Original files are moved into res/backup_originals/ and replaced by filtered versions with original names."
        ]
    }

    try:
        write_json(report_path, report, sort_keys=args.sort_keys)
    except Exception as e:
        print(f"WARNING: failed to write report {report_path}: {e}", file=sys.stderr)

    # Console summary
    print("\n=== Done ===")
    print(f"Replaced originals in place (in res/):")
    print(f"  {cdt_path.name}, {cnc_path.name}, {info_path.name}")
    print(f"Backed up originals -> {backup_dir}")
    print(f"Report -> {report_path}")
    print("\nCounts (see report for full ID lists):")
    for label, st in (("CDT", cdt_stats), ("CNC", cnc_stats), ("IDINFO", info_stats)):
        d = st.as_dict()["counts"]
        print(f"  {label} -> kept_allowed={d['kept_allowed']} | kept_unknown={d['kept_unknown']} | "
              f"removed_disallowed={d['removed_disallowed']} | removed_unknown={d['removed_unknown']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
