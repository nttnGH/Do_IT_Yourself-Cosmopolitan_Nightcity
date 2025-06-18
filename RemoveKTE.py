import os
import json
import re
import sys
from datetime import datetime

# Dictionary mapping display names to language codes used in the JSON "Language" field
LANGUAGES = {
    "ENGLISH":   "eng",
    "POLISH":    "pol",
    "BRAZILIAN": "bra",
    "CHINESE":   "chin",
    "FRENCH":    "fra",
    "GERMAN":    "deu",
    "ITALIAN":   "ita",
    "JAPANESE":  "jpn",
    "KOREAN":    "kor",
    "RUSSIAN":   "rus",
    "SPANISH":   "mex"
}

# Only these files in "res" will be processed
TARGET_FILES = [
    "CNC_cdt_data.json",
    "CNC_cnc_data.json",
    "CVLPV_cnc_data.json",
    "CVLPV_cdt_data.json"
]

# Initialize a global list to collect log entries
log_entries = []

def select_languages():
    """
    Prompt the user in English to choose which languages should have their <kiroshi> tags cleaned.
    Returns a list of selected language codes (e.g., ["eng", "kor"]).
    """
    print("This plugin helps you remove certain `kiroshi translation effect` and replace them with simple `kiroshi tag`,")
    print("meaning that you still have the subtitle that displays in your language but without the translation effect.")
    print("Please choose the language(s) for which you do not want the `kiroshi translation effect`!\n")

    log_entries.append("=== Language Selection ===")
    selected_codes = []

    for display_name, code in LANGUAGES.items():
        while True:
            response = input(f"For {display_name}? Answer yes (remove it) or no (keep it) (Y for yes or N for no), then press Enter: ").strip().upper()
            if response == "Y":
                selected_codes.append(code)
                log_entries.append(f"Selected to remove effect for: {display_name} ({code})")
                break
            elif response == "N":
                log_entries.append(f"Kept translation effect for: {display_name} ({code})")
                break
            else:
                print("Invalid response. Please enter 'Y' for yes or 'N' for no.")

    log_entries.append(f"Final selected languages: {selected_codes}\n")
    return selected_codes

def process_file(filepath, selected_codes):
    """
    Load the JSON from `filepath`, and for each entry whose "Language" is in selected_codes,
    replace the first occurrence of o="...some text..." with o=" " in <kiroshi> tags found in any
    *_femaleVariant or *_maleVariant fields. Write the modified JSON back to the same file if changes occur.
    """
    filename = os.path.basename(filepath)
    log_entries.append(f"--- Processing file: {filename} ---")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        error_msg = f"Error reading '{filename}': {e}"
        print(error_msg, file=sys.stderr)
        log_entries.append(error_msg + "\n")
        return

    modified = False
    entries_modified_count = 0

    # Iterate through each entry (each ID → sub-object)
    for entry_id, entry in data.items():
        language = entry.get("Language")
        # Only process entries whose Language is in the selected_codes list
        if language not in selected_codes:
            continue

        # Iterate through keys of the sub-object
        for key, value in entry.items():
            # Only consider keys ending with "_femaleVariant" or "_maleVariant"
            if not (key.endswith("_femaleVariant") or key.endswith("_maleVariant")):
                continue
            if not isinstance(value, str):
                continue

            # Only modify if there's a <kiroshi ...> tag containing the correct l="language" attribute
            if '<kiroshi' not in value or f'l="{language}"' not in value:
                continue

            # Replace the first occurrence of o="...any content..." with o=" "
            new_value = re.sub(r'o="[^"]*"', 'o=" "', value, count=1)

            # If the string actually changed, update the entry
            if new_value != value:
                entry[key] = new_value
                modified = True
                entries_modified_count += 1
                log_entries.append(f"Modified entry ID {entry_id}, field {key}")

    if not modified:
        msg = f"No modification needed in '{filename}'."
        print(msg)
        log_entries.append(msg + "\n")
        return

    # Write the modified JSON back to the same file, UTF-8 encoded and pretty-printed
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        msg = f"Modified and saved: '{filename}' (entries changed: {entries_modified_count})"
        print(msg)
        log_entries.append(msg + "\n")
    except Exception as e:
        error_msg = f"Error writing '{filename}': {e}"
        print(error_msg, file=sys.stderr)
        log_entries.append(error_msg + "\n")

def write_log():
    """
    Write all collected log entries into logKTEr.txt in the script directory.
    """

    if getattr(sys, 'frozen', False):
        # Si on est dans l’exécutable PyInstaller (mode « gelé »)
        script_dir = os.path.dirname(sys.executable)
    else:
        # Si on est toujours en script .py
        script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "logKTEr.txt")

    try:
        with open(log_path, 'w', encoding='utf-8') as log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"Log generated on: {timestamp}\n\n")
            for entry in log_entries:
                log_file.write(entry + "\n")
        print(f"Log file written: 'logKTEr.txt'")
    except Exception as e:
        print(f"Error writing log file: {e}", file=sys.stderr)

def main():
    # Let the user choose which languages to clean
    selected_codes = select_languages()
    if not selected_codes:
        print("No language selected. Exiting...")
        log_entries.append("No language was selected. Script exited without processing.\n")
        write_log()
        sys.exit(0)

    # Determine the path to the "res" directory
    
    if getattr(sys, 'frozen', False):
        # Si on est dans l’exécutable PyInstaller (mode « gelé »)
        script_dir = os.path.dirname(sys.executable)
    else:
        # Si on est toujours en script .py
        script_dir = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.join(script_dir, "res")

    if not os.path.isdir(res_dir):
        error_msg = f"Error: The folder 'res' does not exist in {script_dir}"
        print(error_msg, file=sys.stderr)
        log_entries.append(error_msg + "\n")
        write_log()
        sys.exit(1)

    # Process only the target files if they exist
    for filename in TARGET_FILES:
        filepath = os.path.join(res_dir, filename)
        if os.path.isfile(filepath):
            print(f"Processing file: {filename}")
            process_file(filepath, selected_codes)
        else:
            warning_msg = f"'{filename}' not found in 'res', skipping."
            print(warning_msg)
            log_entries.append(warning_msg + "\n")

    # After all processing, write the log
    write_log()

if __name__ == "__main__":
    main()

