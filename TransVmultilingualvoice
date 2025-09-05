#!/usr/bin/env python3
import os
import json
from datetime import datetime

# Files to process inside the "res" folder
# - For ALL_IDS_FILES: process ALL IDs (unchanged behavior)
# - For FILTERED_IDS_FILES: process ONLY IDs where "NPC" starts with "PolyglotV_"
ALL_IDS_FILES = ["CVLPV_cnc_data.json", "CVLPV_cdt_data.json"]
FILTERED_IDS_FILES = ["CNC_cnc_data.json", "CNC_cdt_data.json"]

# Build processing plan
files = [(fname, "all") for fname in ALL_IDS_FILES] + [(fname, "filtered") for fname in FILTERED_IDS_FILES]

# Logging utilities
log_entries = []
now_str = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_entries.append(f"{now_str()} - Start processing.")

# === 1) Process data files (CVLPV_* unfiltered, CNC_* filtered on NPC) ===
for filename, mode in files:
    filepath = os.path.join("res", filename)
    log_entries.append(f"{now_str()} - Working on: '{filepath}' (mode: {mode}).")

    # Read JSON
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log_entries.append(f"{now_str()} - ERROR reading '{filepath}': {e}")
        continue

    processed_count = 0
    skipped_count = 0

    # Iterate IDs
    for id_entry, values in data.items():
        # Filter for CNC_* files: NPC must start with "PolyglotV_"
        if mode == "filtered":
            npc_value = values.get("NPC", "")
            if not (isinstance(npc_value, str) and npc_value.startswith("PolyglotV_")):
                skipped_count += 1
                log_entries.append(
                    f"{now_str()} - Skipped ID '{id_entry}' (NPC='{npc_value}' does not start with 'PolyglotV_')."
                )
                continue

        processed_count += 1
        log_entries.append(f"{now_str()} - Processing ID '{id_entry}'.")

        # --- Swap translated_femaleLength <-> translated_maleLength ---
        if "translated_femaleLength" in values and "translated_maleLength" in values:
            f_len = values["translated_femaleLength"]
            m_len = values["translated_maleLength"]
            log_entries.append(
                f"    Before length swap: translated_femaleLength='{f_len}', translated_maleLength='{m_len}'."
            )
            values["translated_femaleLength"], values["translated_maleLength"] = m_len, f_len
            log_entries.append(
                f"    After length swap: translated_femaleLength='{values['translated_femaleLength']}', translated_maleLength='{values['translated_maleLength']}'."
            )
        else:
            log_entries.append("    Missing keys: translated_femaleLength and/or translated_maleLength.")

        # --- Swap femaleResPath$value <-> maleResPath$value ---
        if "femaleResPath$value" in values and "maleResPath$value" in values:
            f_path = values["femaleResPath$value"]
            m_path = values["maleResPath$value"]
            log_entries.append(
                f"    Before path swap: femaleResPath$value='{f_path}', maleResPath$value='{m_path}'."
            )
            values["femaleResPath$value"], values["maleResPath$value"] = m_path, f_path
            log_entries.append(
                f"    After path swap: femaleResPath$value='{values['femaleResPath$value']}', maleResPath$value='{values['maleResPath$value']}'."
            )
        else:
            log_entries.append("    Missing keys: femaleResPath$value and/or maleResPath$value.")

        # --- Swap language variants: *_femaleVariant <-> *_maleVariant ---
        for key in list(values.keys()):
            if key.endswith("_femaleVariant"):
                lang_code = key.split("_")[0]
                female_key = f"{lang_code}_femaleVariant"
                male_key = f"{lang_code}_maleVariant"

                if male_key in values:
                    f_var = values.get(female_key, "")
                    m_var = values.get(male_key, "")
                    log_entries.append(
                        f"    [{lang_code}] Before variant swap: {female_key}='{f_var}', {male_key}='{m_var}'."
                    )

                    # If male variant is empty, copy female into male before the swap
                    if isinstance(m_var, str) and m_var.strip() == "":
                        log_entries.append(f"        Empty {male_key}. Copying from {female_key}.")
                        values[male_key] = f_var
                        m_var = values[male_key]
                        log_entries.append(f"        After copy: {male_key}='{values[male_key]}'.")

                    # Perform swap
                    values[female_key], values[male_key] = values[male_key], values[female_key]
                    log_entries.append(
                        f"    [{lang_code}] After variant swap: {female_key}='{values[female_key]}', {male_key}='{values[male_key]}'."
                    )
                else:
                    log_entries.append(f"    [{lang_code}] Missing key {male_key}, no swap performed.")

    # Write back JSON
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        log_entries.append(
            f"{now_str()} - Updated '{filepath}'. IDs processed: {processed_count}, skipped: {skipped_count}."
        )
    except Exception as e:
        log_entries.append(f"{now_str()} - ERROR writing '{filepath}': {e}")

# === 2) Update res/CVLPV_npc_info.json ===
# - language: '<existing>_transV' (regardless of current data)
# - description: '<existing> (MtF&FtM)'
npc_info_path = os.path.join("res", "CVLPV_npc_info.json")
try:
    with open(npc_info_path, "r", encoding="utf-8") as f:
        npc_info = json.load(f)

    if isinstance(npc_info, dict) and "V" in npc_info and isinstance(npc_info["V"], dict):
        current_lang = npc_info["V"].get("language")
        current_desc = npc_info["V"].get("description")

        current_lang_str = "" if current_lang is None else str(current_lang)
        current_desc_str = "" if current_desc is None else str(current_desc)

        new_lang = f"{current_lang_str}_transV"
        new_desc = f"{current_desc_str} (MtF&FtM)"

        npc_info["V"]["language"] = new_lang
        npc_info["V"]["description"] = new_desc

        with open(npc_info_path, "w", encoding="utf-8") as f:
            json.dump(npc_info, f, ensure_ascii=False, indent=4)

        log_entries.append(
            f"{now_str()} - Updated CVLPV_npc_info.json: language '{current_lang_str}' -> '{new_lang}', "
            f"description '{current_desc_str}' -> '{new_desc}'."
        )
    else:
        log_entries.append(f"{now_str()} - Unexpected structure in '{npc_info_path}': missing 'V' object.")
except FileNotFoundError:
    log_entries.append(f"{now_str()} - File not found: '{npc_info_path}'. Skipped npc_info updates.")
except Exception as e:
    log_entries.append(f"{now_str()} - ERROR processing '{npc_info_path}': {e}")

# === 3) Finish and write log ===
log_entries.append(f"{now_str()} - Processing completed.")

log_path = "logTVMV.txt"
try:
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(log_entries))
    print(f"Operation completed. Detailed log in '{log_path}'.")
except Exception as e:
    print(f"Log writing error '{log_path}': {e}")
