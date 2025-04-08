import os
import json
from datetime import datetime

# List of JSON files to process in the "res" folder
files = ["CVLPV_cnc_data.json", "CVLPV_cdt_data.json"]

# Initialize the log entries list
log_entries = []
timestamp = lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S')

log_entries.append(f"{timestamp()} - Starting processing.")

# Process each JSON file
for filename in files:
    filepath = os.path.join("res", filename)
    log_entries.append(f"{timestamp()} - Processing file '{filepath}'.")
    
    try:
        # Load the content of the JSON file
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log_entries.append(f"{timestamp()} - Error reading file '{filepath}': {e}")
        continue

    # Process each id in the JSON data
    for id_entry, values in data.items():
        log_entries.append(f"{timestamp()} - Processing id '{id_entry}':")

        # --- Swap translated_femaleLength and translated_maleLength ---
        if "translated_femaleLength" in values and "translated_maleLength" in values:
            original_female_length = values["translated_femaleLength"]
            original_male_length = values["translated_maleLength"]
            log_entries.append(f"    Before swap lengths: translated_femaleLength = '{original_female_length}', translated_maleLength = '{original_male_length}'.")
            values["translated_femaleLength"], values["translated_maleLength"] = original_male_length, original_female_length
            log_entries.append(f"    After swap lengths: translated_femaleLength = '{values['translated_femaleLength']}', translated_maleLength = '{values['translated_maleLength']}'.")
        else:
            log_entries.append("    Keys translated_femaleLength and/or translated_maleLength not found.")

        # --- Swap femaleResPath$value and maleResPath$value ---
        if "femaleResPath$value" in values and "maleResPath$value" in values:
            original_female_path = values["femaleResPath$value"]
            original_male_path = values["maleResPath$value"]
            log_entries.append(f"    Before swap ResPath: femaleResPath$value = '{original_female_path}', maleResPath$value = '{original_male_path}'.")
            values["femaleResPath$value"], values["maleResPath$value"] = original_male_path, original_female_path
            log_entries.append(f"    After swap ResPath: femaleResPath$value = '{values['femaleResPath$value']}', maleResPath$value = '{values['maleResPath$value']}'.")
        else:
            log_entries.append("    Keys femaleResPath$value and/or maleResPath$value not found.")

        # --- Process and swap language variant keys ---
        # Iterate over all keys ending with "_femaleVariant"
        keys = list(values.keys())
        for key in keys:
            if key.endswith("_femaleVariant"):
                # Extract the language code (everything before the first underscore)
                lang_code = key.split("_")[0]
                female_key = f"{lang_code}_femaleVariant"
                male_key = f"{lang_code}_maleVariant"
                
                if male_key in values:
                    original_female_variant = values.get(female_key, "")
                    original_male_variant = values.get(male_key, "")
                    log_entries.append(f"    [{lang_code}] Before processing: {female_key} = '{original_female_variant}', {male_key} = '{original_male_variant}'.")
                    
                    # If the male variant is empty, copy the female variant into it
                    if original_male_variant.strip() == "":
                        log_entries.append(f"        The value of {male_key} is empty. Copying value from {female_key}.")
                        values[male_key] = original_female_variant
                        # Update the variable after copying
                        original_male_variant = values[male_key]
                        log_entries.append(f"        After copying: {male_key} = '{values[male_key]}'.")
                        
                    # Swap the variants
                    values[female_key], values[male_key] = values[male_key], values[female_key]
                    log_entries.append(f"    [{lang_code}] After swap: {female_key} = '{values[female_key]}', {male_key} = '{values[male_key]}'.")
                else:
                    log_entries.append(f"    [{lang_code}] Key {male_key} not found, no swap performed.")

    # Overwrite the original JSON file with the modified data
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        log_entries.append(f"{timestamp()} - File '{filepath}' has been successfully updated.")
    except Exception as e:
        log_entries.append(f"{timestamp()} - Error writing file '{filepath}': {e}")

log_entries.append(f"{timestamp()} - Finished processing.")

# Save the log in the TVMV.txt file
log_path = "logTVMV.txt"
try:
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(log_entries))
    print(f"Operation completed. Detailed log saved in '{log_path}'.")
except Exception as e:
    print(f"Error writing log to '{log_path}': {e}")
