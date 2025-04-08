import os
import json

def merge_json(file1, file2):
    """
    Loads two JSON files and merges the dictionaries.
    Data from file2 overwrite those from file1 for duplicate keys.
    Returns the merged dictionary and a list of log messages for each processed ID.
    """
    with open(file1, 'r', encoding='utf-8') as f1:
        data1 = json.load(f1)
    with open(file2, 'r', encoding='utf-8') as f2:
        data2 = json.load(f2)
    
    log_messages = []
    # For each key in file2, update or add to data1 and log the action
    for key, value in data2.items():
        if key in data1:
            log_messages.append(f"ID {key}: replaced data from {os.path.basename(file1)} with data from {os.path.basename(file2)}.")
        else:
            log_messages.append(f"ID {key}: added new data from {os.path.basename(file2)}.")
        data1[key] = value
    
    return data1, log_messages

def save_json(data, filename):
    """
    Saves a dictionary to a JSON file using UTF-8 encoding and formatted output.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    # Path to the folder containing the JSON files
    res_dir = 'res'
    
    combined_logs = []
    
    # Merge for CNC files
    file_CVL_cnc = os.path.join(res_dir, 'CVL_cnc_data.json')
    file_PV_cnc = os.path.join(res_dir, 'PV_cnc_data.json')
    merged_cnc, logs_cnc = merge_json(file_CVL_cnc, file_PV_cnc)
    
    # Save the merged result to CVLPV_cnc_data.json
    output_cnc = os.path.join(res_dir, 'CVLPV_cnc_data.json')
    save_json(merged_cnc, output_cnc)
    
    combined_logs.append("=== CNC Merge Log ===")
    combined_logs.extend(logs_cnc)
    
    # Merge for CDT files
    file_CVL_cdt = os.path.join(res_dir, 'CVL_cdt_data.json')
    file_PV_cdt = os.path.join(res_dir, 'PV_cdt_data.json')
    merged_cdt, logs_cdt = merge_json(file_CVL_cdt, file_PV_cdt)
    
    # Save the merged result to CVLPV_cdt_data.json
    output_cdt = os.path.join(res_dir, 'CVLPV_cdt_data.json')
    save_json(merged_cdt, output_cdt)
    
    combined_logs.append("\n=== CDT Merge Log ===")
    combined_logs.extend(logs_cdt)
    
    # Write a detailed log of all merged IDs to logFusion.txt
    log_file = 'logFusion.txt'
    with open(log_file, 'w', encoding='utf-8') as lf:
        lf.write("\n".join(combined_logs))
    
    print("Merge complete. Merged files are saved in the 'res' folder, and the detailed log is available in logFusion.txt.")

if __name__ == "__main__":
    main()
