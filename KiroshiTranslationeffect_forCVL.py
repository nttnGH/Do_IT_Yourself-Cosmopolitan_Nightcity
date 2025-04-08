import os
import json
import re
from datetime import datetime

# Mapping dictionary to convert language code to its three-letter equivalent
lang_mapping = {
    "EN": "eng",
    "PL": "pol",
    "BR": "bra",
    "CN": "chin",
    "FR": "fra",
    "DE": "deu",
    "IT": "ita",
    "JP": "jpn",
    "KR": "kor",
    "RU": "rus",
    "ES": "mex"
}

# List of JSON files to process
files = [
    os.path.join("res", "CVLPV_cnc_data.json"),
    os.path.join("res", "CVLPV_cdt_data.json")
]

# Log file name
log_filename = "logKTE.txt"

def log_message(msg):
    """Log a message with a timestamp to both the console and the log file."""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_line = f"{timestamp} {msg}"
    print(log_line)
    with open(log_filename, "a", encoding="utf-8") as log_file:
        log_file.write(log_line + "\n")

def update_tag(xml_str, new_l, new_o):
    """
    Update the XML tag by replacing the attribute 'l'
    with new_l and attribute 'o' with new_o.
    """
    updated = re.sub(r'l="[^"]*"', f'l="{new_l}"', xml_str)
    updated = re.sub(r'o="[^"]*"', f'o="{new_o}"', updated)
    return updated

def extract_t_attribute(xml_str):
    """
    Extract the value of the attribute 't' from a <kiroshi> tag.
    Returns an empty string if not found.
    """
    m = re.search(r't="([^"]*)"', xml_str)
    if m:
        return m.group(1)
    return ""

def create_tag(new_l, new_o, new_t):
    """
    Create a new <kiroshi> XML tag with the specified attributes.
    """
    return f'<kiroshi l="{new_l}" o="{new_o}" t="{new_t}" b="" a=""/>'

def process_entry(entry, entry_id):
    log_message(f"Processing entry {entry_id}")

    # 1. Determine the reference language (vlanguage)
    reference_lang = None
    reference_female_text = None
    reference_male_text = None

    # Loop through all _femaleVariant keys to find one without the <kiroshi> tag (plain text)
    for key, val in entry.items():
        if key.endswith("_femaleVariant") and val.strip() != "":
            # If the value does NOT contain a <kiroshi> tag, it's our reference
            if "<kiroshi" not in val:
                lang_code = key.split("_")[0]
                reference_lang = lang_code
                reference_female_text = val.strip()
                # Try to get the corresponding male variant for the reference language
                ref_male_key = f"{lang_code}_maleVariant"
                ref_male = entry.get(ref_male_key, "").strip()
                # If male text is empty or also plain text, we use the female one as fallback
                reference_male_text = ref_male if ref_male != "" and "<kiroshi" not in ref_male else reference_female_text
                log_message(f"  Detected reference language: {lang_code} => {lang_mapping.get(lang_code, 'unknown')}")
                break

    if reference_lang is None:
        log_message(f"  No reference language found for entry {entry_id}. Nothing will be modified.")
        return

    # Determine the three-letter code to use for non-reference tags
    target_code = lang_mapping.get(reference_lang, reference_lang.lower())

    # 2. Loop through and update all keys ending with _femaleVariant or _maleVariant
    for key in list(entry.keys()):
        if not (key.endswith("_femaleVariant") or key.endswith("_maleVariant")):
            continue

        # Do not modify the field of the reference language (even if it is in XML)
        lang_prefix = key.split("_")[0]
        if lang_prefix == reference_lang:
            log_message(f"  {key} is the reference field for language {reference_lang} – not modified.")
            continue

        original_val = entry[key]
        variant_type = "female" if "femaleVariant" in key else "male"

        if original_val.strip() != "":
            # If the field contains a <kiroshi> tag, update it
            if "<kiroshi" in original_val:
                # For the female variant, assign the reference female text;
                # For the male variant, use the reference male text if available, otherwise the female text.
                if variant_type == "female":
                    new_o = reference_female_text
                else:  # male
                    new_o = reference_male_text if reference_male_text.strip() != "" else reference_female_text

                updated_val = update_tag(original_val, target_code, new_o)
                entry[key] = updated_val
                log_message(f"  Updated {key}: replaced attributes 'l' and 'o'")
            else:
                # If there is no <kiroshi> tag, it's likely the reference field; do not modify.
                log_message(f"  {key} does not contain a <kiroshi> tag – field is considered reference; not modified.")
        else:
            # For empty fields (only for maleVariant)
            if variant_type == "male":
                if reference_male_text.strip() != "":
                    # Try to get the 't' attribute from the corresponding femaleVariant field in the same language
                    female_key = f"{lang_prefix}_femaleVariant"
                    female_val = entry.get(female_key, "")
                    t_value = extract_t_attribute(female_val) if "<kiroshi" in female_val else ""
                    # If no 't' is found, fallback to using the reference female text
                    new_tag = create_tag(target_code, reference_male_text, t_value if t_value else reference_female_text)
                    entry[key] = new_tag
                    log_message(f"  Created tag for {key} (initially empty field)")
                else:
                    log_message(f"  {key} is empty and no reference male value is available – not modified.")

def process_file(filepath):
    log_message(f"=== Processing file {filepath} ===")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log_message(f"Error reading file {filepath}: {e}")
        return

    # Process each entry in the JSON
    for entry_id, entry in data.items():
        process_entry(entry, entry_id)

    # Write the modified data back to the same file (overwriting the original)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        log_message(f"Modifications saved in {filepath}")
    except Exception as e:
        log_message(f"Error writing to file {filepath}: {e}")

def main():
    # Clear the log file at the start (optional)
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log_file.write(f"=== Log start ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n")
    
    for file in files:
        if os.path.exists(file):
            process_file(file)
        else:
            log_message(f"File not found: {file}")

if __name__ == "__main__":
    main()
