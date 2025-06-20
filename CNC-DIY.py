import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import pygame
import json
import os
import shutil
import logging
from logging.handlers import RotatingFileHandler
import threading
import re 

# --- Global Variables ---
BASE_DIR = "source"
RES_DIR = "res"

language_codes = {
    "English": ("EN", "en-us"),
    "Polish": ("PL", "pl-pl"),
    "Brazilian": ("BR", "pt-br"),
    "Chinese": ("CN", "zh-cn"),
    "French": ("FR", "fr-fr"),
    "German": ("DE", "de-de"),
    "Italian": ("IT", "it-it"),
    "Japanese": ("JP", "jp-jp"),
    "Korean": ("KR", "kr-kr"),
    "Russian": ("RU", "ru-ru"),
    "Spanish": ("ES", "es-es"),
    "Arabic": ("AR", "ar-ar"),
    "Czech": ("CZ", "cz-cz"),
    "Hungarian": ("HU", "hu-hu"),
    "Latin American Spanish": ("MX", "es-mx"),
    "Thai": ("TH", "th-th"),
    "Turkish": ("TR", "tr-tr"),
    "Ukrainian": ("UA", "ua-ua"),
    "Traditional Chinese": ("ZH", "zh-tw")
}

# --- Helper Functions ---
def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load JSON from {filepath}", exc_info=True)
        raise

def save_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Failed to save JSON to {filepath}", exc_info=True)
        raise

# --- Main Application ---
class CNCApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.iconbitmap(os.path.join(RES_DIR, "#CosmopolitanNightCity.ico"))
        self.title("Cosmopolitan Night City - DIY edition")
        self.geometry("600x700")
        self.resizable(True, True)
        self.config_data = {}
        self.image_cache = {}
        self.setup_logging()
        self.create_widgets()
        self.after(200, self.show_welcome_message)

        # NPC
        try:
            self.npc_info = load_json(os.path.join(RES_DIR, "CNC_npc_info.json"))
            logging.info("CNC_npc_info.json loaded successfully.")
        except Exception as e:
            logging.error("Failed to load CNC_npc_info.json", exc_info=True)
            messagebox.showerror("Error", "Failed to load NPC info. Check the log for details.")
            self.quit()

        # "CVLPV_npc_info.json"
        cvlpv_path = os.path.join(RES_DIR, "CVLPV_npc_info.json")
        if os.path.exists(cvlpv_path):
            try:
                npc_info_extra = load_json(cvlpv_path)
                self.npc_info.update(npc_info_extra)
                logging.info("CVLPV_npc_info.json loaded and merged successfully.")
            except Exception as e:
                logging.error("Failed to load CVLPV_npc_info.json", exc_info=True)

    # --- UI Update Methods ---
    def safe_update_status(self, msg):
        self.after(0, lambda: self.status_label.config(text=msg))
        logging.info(msg)

    def safe_add_step(self, msg):
        def add():
            self.steps_list.insert(tk.END, msg)
            self.steps_list.see(tk.END)
        self.after_idle(add)
        logging.info(msg)

    def safe_update_progress(self, value):
        self.after(0, lambda: self.progress_var.set(value))

    def safe_show_error(self, msg):
        self.after(0, lambda: messagebox.showerror("Error", msg))

    # --- Audio preview ---
    def play_npc_preview(self, npc_name):
        try:
            audio_path = os.path.join("res", "xomod", f"{npc_name}.wav")
            if os.path.exists(audio_path):
                pygame.mixer.init()
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
            else:
                logging.warning(f"No audio preview found for {npc_name}")
        except Exception as e:
            logging.error(f"Error while playing audio preview for {npc_name}", exc_info=True)

    # --- Logging ---
    def setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        log_path = os.path.join(BASE_DIR, "resources", "log.txt")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        handler = RotatingFileHandler(log_path, maxBytes=1000000, backupCount=5, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # --- GUI Layout ---
    def create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=2)
        self.rowconfigure(2, weight=0)
        
        # First Frame 
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        ttk.Label(self.main_frame, text="What main language’s pumping through Night City?\n(Choose the language your game’s voices are configured in)").pack(anchor="w")
        # "ALL"
        audio_options = ["English", "Polish", "Russian", "German", "French", "Italian", "Spanish", "Chinese", "Korean", "Japanese", "Brazilian", "ALL"]
        self.audio_choice = ttk.Combobox(self.main_frame, values=audio_options, state="readonly")
        self.audio_choice.pack(fill="x")
        self.audio_choice.current(0)
        ttk.Label(self.main_frame, text="Which language is wired into your Kiroshi translator?\n(Choose the language you read your in-game subtitles in)").pack(anchor="w")
        subtitle_options = list(language_codes.keys()) + ["ALL"]
        self.subtitle_choice = ttk.Combobox(self.main_frame, values=subtitle_options, state="readonly")
        self.subtitle_choice.pack(fill="x")
        self.subtitle_choice.current(0)
        ttk.Button(self.main_frame, text="START", command=self.next_step).pack(pady=10)
        
        # Steps frame
        steps_frame = ttk.LabelFrame(self, text="Steps")
        steps_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.steps_list = tk.Listbox(steps_frame, height=4, font=("TkDefaultFont", 8))
        self.steps_list.pack(fill="both", expand=True, padx=2, pady=2)

        # Status frame
        status_frame = ttk.Frame(self)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            relief="sunken",
            anchor="w",
            font=("TkDefaultFont", 8)
        )
        self.status_label.pack(fill="x", padx=2, pady=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            maximum=100,
            length=100  
        )
        self.progress_bar.pack(fill="x", padx=2, pady=1)

        # Message
    def show_welcome_message(self):
        welcome_text = (
            "Get ready to build your very own version of Cosmopolitan Night City!\n\n"
            "Need help? A detailed tutorial is waiting for you on NexusMods."
        )
        messagebox.showinfo("Welcome", welcome_text)

    def show_final_message(self):
        final_text = (
            "First step complete! Now, it's time to convert and pack the 'source' folder into WolvenKit "
            "(refer to the NexusMods tutorial video for guidance).\n\nPress OK to exit."
        )
        messagebox.showinfo("Process Complete", final_text)
        self.quit()

    # --- Step B: Language & NPC Selection ---
    def next_step(self):
        try:
            self.config_data["audio_language"] = self.audio_choice.get()
            self.config_data["subtitle_language"] = self.subtitle_choice.get()
            self.handle_language_files(self.config_data["audio_language"], self.config_data["subtitle_language"])
            self.safe_add_step("Audio language selected.")
            self.safe_add_step("Subtitles language selected.")

            self.character_selection()
        except Exception as e:
            logging.error("Error in next step", exc_info=True)
            messagebox.showerror("Error", "An error occurred while proceeding to the next step. Check the log for details.")

    def character_selection(self, index=0):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        characters = list(self.npc_info.keys())
        if index < len(characters):
            npc = characters[index]
            info = self.npc_info[npc]
            # Description
            desc_box = tk.Text(
                self.main_frame,
                height=5,               
                width=60,               
                wrap="word",
                font=("TkDefaultFont", 9),
                relief="solid",
                state="normal",
                bg=self.cget("bg"),
                bd=1
            )
            desc_box.insert("1.0", info['description'])
            desc_box.configure(state="disabled")
            desc_box.pack(fill="x", padx=5, pady=(5, 2))
            # language
            lang_text = f"Override language protocol: set to {info['language']}?"
            lang_label = ttk.Label(
                self.main_frame,
                text=lang_text,
                anchor="w",
                font=("TkDefaultFont", 9),
                width=60
            )
            lang_label.pack(fill="x", padx=5, pady=(0, 5))
            npc_image = self.load_image(npc)
            if npc_image:
                self.image_cache[npc] = npc_image
                ttk.Label(self.main_frame, image=npc_image).pack(pady=5)
                ttk.Button(self.main_frame, text="🔊 Audio Preview", command=lambda: self.play_npc_preview(npc)).pack(pady=5)

            # Check
            if self.config_data["audio_language"] != "ALL" and info["language"] == self.config_data["audio_language"]:
                ttk.Label(self.main_frame, text="Not selectable (identical audio language)").pack(anchor="w", pady=5)
                choice = tk.BooleanVar(value=False)
                ttk.Radiobutton(self.main_frame, text="Yes", variable=choice, value=True, state="disabled").pack(anchor="w")
                ttk.Radiobutton(self.main_frame, text="No", variable=choice, value=False, state="disabled").pack(anchor="w")
            else:
                choice = tk.BooleanVar(value=True)
                ttk.Radiobutton(self.main_frame, text="Yes", variable=choice, value=True).pack(anchor="w")
                ttk.Radiobutton(self.main_frame, text="No", variable=choice, value=False).pack(anchor="w")

            # Next
            ttk.Button(self.main_frame, text="Next", command=lambda: self.next_character(npc, choice, index)).pack(pady=10)
        else:
            self.safe_add_step("NPCs selection completed.")
            self.save_configuration()

    def next_character(self, npc, choice, index):
        self.config_data[npc] = choice.get()
        self.character_selection(index + 1)

    def save_configuration(self):
        try:
            config_path = os.path.join(BASE_DIR, "resources", "config_diy.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            save_json(config_path, self.config_data)
            logging.info("Configuration saved successfully.")
            messagebox.showinfo("Selection Finished.", "Configuration saved successfully.")
            threading.Thread(target=self.worker_process, daemon=True).start()
        except Exception as e:
            logging.error("Failed to save configuration", exc_info=True)
            messagebox.showerror("Error", "Failed to save configuration. Check the log for details.")

    def load_image(self, npc_name):
        image_path = os.path.join("res", "xomod", f"{npc_name}.png")
        if os.path.exists(image_path):
            image = Image.open(image_path).resize((200, 200))
            return ImageTk.PhotoImage(image)
        return None

    # --- Step C: Language Files Handling ---
    def handle_language_files(self, audio_language, subtitle_language):
        try:
            # Audio files
            if audio_language == "ALL":
                for lang, codes in language_codes.items():
                    audio_code, full_audio_code = codes
                    base_audio_path = os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code)
                    ep1_audio_path = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code)
                    self.copy_files(f"files/leng/{audio_code}_base_stringidvariantlengthsreport.json.json", base_audio_path)
                    self.copy_files(f"files/leng/{audio_code}_ep1_stringidvariantlengthsreport.json.json", ep1_audio_path)
                    lipmap_path = os.path.join(BASE_DIR, "raw", "base", "localization")
                    self.copy_files(f"files/lipmap/{audio_code}_lipmap.json", lipmap_path)
                    vomap_base_files = [
                        "base_voiceovermap.json.json", "base_voiceovermap_1.json.json",
                        "base_voiceovermap_helmet.json.json", "base_voiceovermap_holocall.json.json",
                        "base_voiceovermap_rewinded.json.json"
                    ]
                    vomap_ep1_files = [
                        "ep1_voiceovermap.json.json", "ep1_voiceovermap_helmet.json.json",
                        "ep1_voiceovermap_holocall.json.json", "ep1_voiceovermap_rewinded.json.json"
                    ]
                    for file in vomap_base_files:
                        self.copy_files(f"files/vomap/{audio_code}_{file}",
                                        os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code))
                    for file in vomap_ep1_files:
                        self.copy_files(f"files/vomap/{audio_code}_{file}",
                                        os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code))
            else:
                audio_code, full_audio_code = language_codes[audio_language]
                base_audio_path = os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code)
                ep1_audio_path = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code)
                self.copy_files(f"files/leng/{audio_code}_base_stringidvariantlengthsreport.json.json", base_audio_path)
                self.copy_files(f"files/leng/{audio_code}_ep1_stringidvariantlengthsreport.json.json", ep1_audio_path)
                lipmap_path = os.path.join(BASE_DIR, "raw", "base", "localization")
                self.copy_files(f"files/lipmap/{audio_code}_lipmap.json", lipmap_path)
                vomap_base_files = [
                    "base_voiceovermap.json.json", "base_voiceovermap_1.json.json",
                    "base_voiceovermap_helmet.json.json", "base_voiceovermap_holocall.json.json",
                    "base_voiceovermap_rewinded.json.json"
                ]
                vomap_ep1_files = [
                    "ep1_voiceovermap.json.json", "ep1_voiceovermap_helmet.json.json",
                    "ep1_voiceovermap_holocall.json.json", "ep1_voiceovermap_rewinded.json.json"
                ]
                for file in vomap_base_files:
                    self.copy_files(f"files/vomap/{audio_code}_{file}",
                                    os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code))
                for file in vomap_ep1_files:
                    self.copy_files(f"files/vomap/{audio_code}_{file}",
                                    os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code))
            # Subtitles
            if subtitle_language == "ALL":
                for lang, codes in language_codes.items():
                    subtitle_code, full_subtitle_code = codes
                    base_sub_path = os.path.join(BASE_DIR, "raw", "base", "localization", full_subtitle_code)
                    ep1_sub_path = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_subtitle_code)
                    self.copy_files(f"files/Sub/{subtitle_code}_base_subtitles", base_sub_path)
                    self.copy_files(f"files/Sub/{subtitle_code}_ep1_subtitles", ep1_sub_path)
            else:
                subtitle_code, full_subtitle_code = language_codes[subtitle_language]
                base_sub_path = os.path.join(BASE_DIR, "raw", "base", "localization", full_subtitle_code)
                ep1_sub_path = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_subtitle_code)
                self.copy_files(f"files/Sub/{subtitle_code}_base_subtitles", base_sub_path)
                self.copy_files(f"files/Sub/{subtitle_code}_ep1_subtitles", ep1_sub_path)
            logging.info("Language-specific files handled successfully.")
        except Exception as e:
            logging.error("Failed to handle language-specific files", exc_info=True)
            messagebox.showerror("Error", "Failed to handle language-specific files. Check the log for details.")

    def copy_files(self, source, destination):
        try:
            if os.path.exists(source):
                os.makedirs(destination, exist_ok=True)
                if os.path.isdir(source):
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                else:
                    shutil.copy(source, destination)
                logging.info(f"Files copied from {source} to {destination}")
        except Exception as e:
            logging.error("Failed to copy files", exc_info=True)
            messagebox.showerror("Error", "Failed to copy files. Check the log for details.")

    # --- Processing Worker ---
    def worker_process(self):
        try:
            self.safe_update_status("Starting processing...")
            self.safe_update_progress(5)
            # Configuration
            config_path = os.path.join(BASE_DIR, "resources", "config_diy.json")
            self.config_data = load_json(config_path)

            # 1. INFOS
            try:
                id_data = load_json(os.path.join(RES_DIR, "CNC_id_info.json"))
                logging.info("CNC_id_info.json loaded successfully.")
            except Exception as e:
                logging.error("Failed to load CNC_id_info.json", exc_info=True)
                messagebox.showerror("Error", "Failed to load ID info. Check the log for details.")
                self.quit()

            cvlpv_id_path = os.path.join(RES_DIR, "CVLPV_id_info.json")
            if os.path.exists(cvlpv_id_path):
                try:
                    id_data_extra = load_json(cvlpv_id_path)
                    id_data.update(id_data_extra)
                    logging.info("CVLPV_id_info.json loaded and merged successfully.")
                except Exception as e:
                    logging.error("Failed to load CVLPV_id_info.json", exc_info=True)

            # 2. CDT
            try:
                cdt_data = load_json(os.path.join(RES_DIR, "CNC_cdt_data.json"))
                logging.info("CNC_cdt_data.json loaded successfully.")
            except Exception as e:
                logging.error("Failed to load CNC_cdt_data.json", exc_info=True)
                messagebox.showerror("Error", "Failed to load CDT data. Check the log for details.")
                self.quit()

            cvlpv_cdt_path = os.path.join(RES_DIR, "CVLPV_cdt_data.json")
            if os.path.exists(cvlpv_cdt_path):
                try:
                    cdt_data_extra = load_json(cvlpv_cdt_path)
                    cdt_data.update(cdt_data_extra)
                    logging.info("CVLPV_cdt_data.json loaded and merged successfully.")
                except Exception as e:
                    logging.error("Failed to load CVLPV_cdt_data.json", exc_info=True)

            # 3. CNC
            try:
                cnc_data = load_json(os.path.join(RES_DIR, "CNC_cnc_data.json"))
                logging.info("CNC_cnc_data.json loaded successfully.")
            except Exception as e:
                logging.error("Failed to load CNC_cnc_data.json", exc_info=True)
                messagebox.showerror("Error", "Failed to load CNC data. Check the log for details.")
                self.quit()

            cvlpv_cnc_path = os.path.join(RES_DIR, "CVLPV_cnc_data.json")
            if os.path.exists(cvlpv_cnc_path):
                try:
                    cnc_data_extra = load_json(cvlpv_cnc_path)
                    cnc_data.update(cnc_data_extra)
                    logging.info("CVLPV_cnc_data.json loaded and merged successfully.")
                except Exception as e:
                    logging.error("Failed to load CVLPV_cnc_data.json", exc_info=True)


            # IDs       
            selected_ids = []
            for npc, selected in self.config_data.items():
                if isinstance(selected, bool) and selected and npc in id_data:
                    selected_ids.extend(id_data[npc]["Ids"])
            filtered_cdt_data = {data_id: info for data_id, info in cdt_data.items() if data_id in selected_ids}
            filtered_cnc_data = {data_id: info for data_id, info in cnc_data.items() if data_id in selected_ids}
            save_json(os.path.join(BASE_DIR, "resources", "cdt.json"), filtered_cdt_data)
            save_json(os.path.join(BASE_DIR, "resources", "cnc.json"), filtered_cnc_data)
            self.safe_update_progress(10)


            # --- 1 : Audio ---
            self.process_audio_files()
            self.safe_add_step(f"Audio files processed successfully!")
            self.safe_update_progress(25)

            # --- 2 : Lipsync ---
            self.process_lipsync()
            self.safe_add_step("Lipsync and Lipmap processing successfully!")
            self.safe_update_progress(35)

            # --- 3 : Voiceovermaps ---
            count_vo_base = self.process_voiceovermaps_base()
            self.safe_add_step(f"Voiceovermaps (Cyberpunk2077) updated: {count_vo_base} entries.")
            count_vo_ep1 = self.process_voiceovermaps_ep1()
            self.safe_add_step(f"Voiceovermaps (Phantom Liberty) updated: {count_vo_ep1} entries.")
            self.safe_add_step("Voiceovermaps processing successfully!")
            self.safe_update_progress(45)

            # --- 4 : Dialogue duration ---
            count_durations_base = self.update_stringidvariantlengthsreport("base", filtered_cnc_data)
            count_durations_ep1 = self.update_stringidvariantlengthsreport("ep1", filtered_cdt_data)
            self.safe_add_step(f"Updated dialogue durations: {count_durations_base} entries for Cyberpunk2077, {count_durations_ep1} for Phantom Liberty.")
            self.safe_add_step("Dialogue durations processing successfully!")
            self.safe_update_progress(60)

            # --- 5 : Subtitles ---
            subtitle_language = self.config_data["subtitle_language"]
            subtitle_code = language_codes[subtitle_language][0] if subtitle_language != "ALL" else None
            count_subtitles_base = self.modify_subtitles("base", subtitle_code, filtered_cnc_data)
            count_subtitles_ep1 = self.modify_subtitles("ep1", subtitle_code, filtered_cdt_data)
            self.safe_add_step(f"Subtitles modified: {count_subtitles_base} entries for Cyberpunk2077, {count_subtitles_ep1} for Phantom Liberty.")
            self.safe_add_step("Subtitles processing successfully!")
            self.safe_update_progress(85)

            # --- 6 : Cleaning ---
            self.safe_add_step("Cleaning up intermediate files...")
            self.cleanup_intermediate_files()
            self.safe_add_step("Cleanup completed.")
            self.safe_update_progress(95)


            self.safe_add_step("All processing completed successfully!!!")
            self.safe_update_progress(100)
            self.after(0, self.show_final_message)

        except Exception as e:
            logging.error("Failed to process data", exc_info=True)
            self.safe_show_error("Failed to process data. Check the log for details.")
                
    # --- Step 1 : Audio (.wem) ---
    def process_audio_files(self):
        try:
            self.safe_update_status("Processing audio files...")
            cnc_path = os.path.join(BASE_DIR, "resources", "cnc.json")
            cdt_path = os.path.join(BASE_DIR, "resources", "cdt.json")
            cnc_data = load_json(cnc_path)
            cdt_data = load_json(cdt_path)
            audio_files_base = set()
            audio_files_ep1 = set()
            for entry in cnc_data.values():
                if "female_file" in entry:
                    audio_files_base.add(entry["female_file"])
                if "male_file" in entry:
                    audio_files_base.add(entry["male_file"])
            for entry in cdt_data.values():
                if "female_file" in entry:
                    audio_files_ep1.add(entry["female_file"])
                if "male_file" in entry:
                    audio_files_ep1.add(entry["male_file"])
            self.safe_add_step(f"Found {len(audio_files_base)} unique audio file(s) for Cyberpunk2077 and {len(audio_files_ep1)} for Phantom Liberty.")
            source_wem_dir = os.path.join("files", "wem")
            found_files = {}
            for root, _, files in os.walk(source_wem_dir):
                for f in files:
                    if f.lower().endswith(".wem"):
                        found_files.setdefault(f, []).append(os.path.join(root, f))

            copied_base = 0
            for audio_file in audio_files_base:
                if audio_file in found_files:
                    for src in found_files[audio_file]:
                        rel_path = os.path.relpath(src, source_wem_dir)
                        dst = os.path.join(BASE_DIR, "archive", "base", "localization", rel_path)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                        copied_base += 1
                        logging.info(f"Copied audio file {src} to {dst}")
                else:
                    logging.warning(f"Audio file {audio_file} not found in {source_wem_dir}")

            copied_ep1 = 0
            for audio_file in audio_files_ep1:
                if audio_file in found_files:
                    for src in found_files[audio_file]:
                        rel_path = os.path.relpath(src, source_wem_dir)
                        dst = os.path.join(BASE_DIR, "archive", "ep1", "localization", rel_path)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                        copied_ep1 += 1
                        logging.info(f"Copied audio file {src} to {dst}")
                else:
                    logging.warning(f"Audio file {audio_file} not found in {source_wem_dir}")

            self.safe_update_status("Audio files processed.")
            return (copied_base, copied_ep1)
        except Exception as e:
            logging.error("Failed to process audio files", exc_info=True)
            self.safe_show_error("Failed to process audio files. Check the log for details.")
            return (0, 0)

    # --- Step 2 : Lipsync and Lipmap ---    
    def process_lipsync(self):
        try:
            self.safe_update_status("Processing lipsync data...")
            self.safe_update_progress(20)
            # 1 : lipsync.json
            config_diy_path = os.path.join(BASE_DIR, "resources", "config_diy.json")
            cnc_lipsync_data_path = os.path.join(RES_DIR, "CNC_lipsync_data.json")
            lipsync_output_path = os.path.join(BASE_DIR, "resources", "lipsync.json")
            
            config_data = load_json(config_diy_path)
            npc_list = [key for key, value in config_data.items() if isinstance(value, bool) and value]
            lipsync_data = load_json(cnc_lipsync_data_path)            
            # CVLPL
            cvlpv_lipsync_data_path = os.path.join(RES_DIR, "CVLPV_lipsync_data.json")
            if os.path.exists(cvlpv_lipsync_data_path):
                try:
                    cvlpv_lipsync_data = load_json(cvlpv_lipsync_data_path)
                    lipsync_data.update(cvlpv_lipsync_data)
                    logging.info("CVLPV_lipsync_data.json loaded and merged successfully.")
                except Exception as e:
                    logging.error("Failed to load CVLPV_lipsync_data.json", exc_info=True)

            filtered_data = {npc: paths for npc, paths in lipsync_data.items() if npc in npc_list}
            save_json(lipsync_output_path, filtered_data)
            self.safe_add_step("New lipsyncs created.")
            
            # 2 : anims
            source_files_folder = os.path.join("files", "lipsync")
            destination_archive_folder = os.path.join(BASE_DIR, "archive")
            lipsync_data = load_json(lipsync_output_path)
            for npc, file_paths in lipsync_data.items():
                for relative_path in file_paths:
                    source_file = os.path.join(source_files_folder, relative_path)
                    dest_file = os.path.join(destination_archive_folder, relative_path)
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                    if os.path.exists(source_file):
                        shutil.copy2(source_file, dest_file)
                        logging.info(f"Copied anim file from {source_file} to {dest_file}")
                    else:
                        logging.warning(f"Anims file {source_file} not found in {source_files_folder}")
            self.safe_add_step("Lipsync files process completed.")
            
            # 3 : Lipmap
            audio_language = config_data.get("audio_language", "English")
            lipmap_folder = os.path.join(BASE_DIR, "raw", "base", "localization")
            if audio_language == "ALL":
                for lang, codes in language_codes.items():
                    lang_code, full_audio_code = codes
                    lipmap_filename = f"{lang_code}_lipmap.json"
                    lipmap_path = os.path.join(lipmap_folder, lipmap_filename)
                    if os.path.exists(lipmap_path):
                        lipmap_data = load_json(lipmap_path)
                        lipsync_data = load_json(lipsync_output_path)
                        all_lipsync_paths = set()
                        for npc, paths in lipsync_data.items():
                            for path in paths:
                                all_lipsync_paths.add(path)
                        
                        def update_depot_path(original_value):
                            pattern = r'^(base\\localization\\)[^\\]+(\\lipsync\\.+)$'
                            match = re.match(pattern, original_value)
                            if match:
                                prefix, suffix = match.groups()
                                candidate = prefix + "cnc" + suffix
                                if candidate in all_lipsync_paths:
                                    return candidate
                            return original_value
                        
                        scene_entries = lipmap_data.get("Data", {}).get("RootChunk", {}).get("sceneEntries", [])
                        for entry in scene_entries:
                            for anim in entry.get("animSets", []):
                                depot = anim.get("DepotPath", {})
                                original = depot.get("$value", "")
                                updated = update_depot_path(original)
                                if updated != original:
                                    depot["$value"] = updated
                        
                        output_lipmap_path = os.path.join(lipmap_folder, f"{full_audio_code}.lipmap.json")
                        save_json(output_lipmap_path, lipmap_data)
                        self.safe_add_step(f"New lipmap saved for {lang} localization.")
                    else:
                        logging.warning(f"Lipmap file {lipmap_path} not found for {lang} localization.")
            else:
                lang_code, full_audio_code = language_codes.get(audio_language, ("EN", "en-us"))
                lipmap_filename = f"{lang_code}_lipmap.json"
                lipmap_path = os.path.join(lipmap_folder, lipmap_filename)
                lipmap_data = load_json(lipmap_path)
                lipsync_data = load_json(lipsync_output_path)
                all_lipsync_paths = set()
                for npc, paths in lipsync_data.items():
                    for path in paths:
                        all_lipsync_paths.add(path)
                        
                def update_depot_path(original_value):
                    pattern = r'^(base\\localization\\)[^\\]+(\\lipsync\\.+)$'
                    match = re.match(pattern, original_value)
                    if match:
                        prefix, suffix = match.groups()
                        candidate = prefix + "cnc" + suffix
                        if candidate in all_lipsync_paths:
                            return candidate
                    return original_value
                        
                scene_entries = lipmap_data.get("Data", {}).get("RootChunk", {}).get("sceneEntries", [])
                for entry in scene_entries:
                    for anim in entry.get("animSets", []):
                        depot = anim.get("DepotPath", {})
                        original = depot.get("$value", "")
                        updated = update_depot_path(original)
                        if updated != original:
                            depot["$value"] = updated
                output_lipmap_path = os.path.join(lipmap_folder, f"{full_audio_code}.lipmap.json")
                save_json(output_lipmap_path, lipmap_data)
                self.safe_add_step("New lipmap saved.")
            
        except Exception as e:
            logging.error("Failed in new lipsync processing", exc_info=True)
            self.safe_show_error("Lipsync processing failed. Check the log for details.")

    # --- Step 3 : Voiceover Maps ---
    def process_voiceovermaps_base(self):
        try:
            count_vo = 0
            self.safe_update_status("Processing base voiceovermap files...")
            ref_data = load_json(os.path.join(BASE_DIR, "resources", "cnc.json"))
            audio_language = self.config_data["audio_language"]
            if audio_language == "ALL":
                for lang, codes in language_codes.items():
                    audio_code, full_audio_code = codes
                    base_dir = os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code)
                    file_mappings = {
                        f"{audio_code}_base_voiceovermap.json.json": ("voiceovermap.json.json", "vo"),
                        f"{audio_code}_base_voiceovermap_1.json.json": ("voiceovermap_1.json.json", "vo"),
                        f"{audio_code}_base_voiceovermap_helmet.json.json": ("voiceovermap_helmet.json.json", "vo_helmet"),
                        f"{audio_code}_base_voiceovermap_holocall.json.json": ("voiceovermap_holocall.json.json", "vo_holocall"),
                        f"{audio_code}_base_voiceovermap_rewinded.json.json": ("voiceovermap_rewinded.json.json", "vo_rewinded"),
                    }
                    for filename, (new_filename, folder_replacement) in file_mappings.items():
                        file_path = os.path.join(base_dir, filename)
                        if os.path.exists(file_path):
                            data = load_json(file_path)
                            entries = data.get("Data", {}).get("RootChunk", {}).get("root", {}).get("Data", {}).get("entries", [])
                            for entry in entries:
                                sid = entry.get("stringId")
                                if sid in ref_data:
                                    new_female = ref_data[sid].get("femaleResPath$value")
                                    new_male = ref_data[sid].get("maleResPath$value")
                                    if new_female:
                                        new_female = new_female.replace("[folder]", folder_replacement)
                                        entry["femaleResPath"]["DepotPath"]["$value"] = new_female
                                    if new_male:
                                        new_male = new_male.replace("[folder]", folder_replacement)
                                        entry["maleResPath"]["DepotPath"]["$value"] = new_male
                                    count_vo += 1
                            target_path = os.path.join(base_dir, new_filename)
                            save_json(target_path, data)
                        else:
                            logging.warning(f"File {file_path} does not exist and will be skipped.")
                return count_vo
            else:
                audio_code, full_audio_code = language_codes[audio_language]
                base_dir = os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code)
                file_mappings = {
                    f"{audio_code}_base_voiceovermap.json.json": ("voiceovermap.json.json", "vo"),
                    f"{audio_code}_base_voiceovermap_1.json.json": ("voiceovermap_1.json.json", "vo"),
                    f"{audio_code}_base_voiceovermap_helmet.json.json": ("voiceovermap_helmet.json.json", "vo_helmet"),
                    f"{audio_code}_base_voiceovermap_holocall.json.json": ("voiceovermap_holocall.json.json", "vo_holocall"),
                    f"{audio_code}_base_voiceovermap_rewinded.json.json": ("voiceovermap_rewinded.json.json", "vo_rewinded"),
                }
                for filename, (new_filename, folder_replacement) in file_mappings.items():
                    file_path = os.path.join(base_dir, filename)
                    if os.path.exists(file_path):
                        data = load_json(file_path)
                        entries = data.get("Data", {}).get("RootChunk", {}).get("root", {}).get("Data", {}).get("entries", [])
                        for entry in entries:
                            sid = entry.get("stringId")
                            if sid in ref_data:
                                new_female = ref_data[sid].get("femaleResPath$value")
                                new_male = ref_data[sid].get("maleResPath$value")
                                if new_female:
                                    new_female = new_female.replace("[folder]", folder_replacement)
                                    entry["femaleResPath"]["DepotPath"]["$value"] = new_female
                                if new_male:
                                    new_male = new_male.replace("[folder]", folder_replacement)
                                    entry["maleResPath"]["DepotPath"]["$value"] = new_male
                                count_vo += 1
                        target_path = os.path.join(base_dir, new_filename)
                        save_json(target_path, data)
                    else:
                        logging.warning(f"File {file_path} does not exist and will be skipped.")
                return count_vo
        except Exception as e:
            logging.error("Failed to process base voiceovermaps", exc_info=True)
            self.safe_show_error("Failed to process base voiceovermaps. Check the log for details.")
            return 0

    def process_voiceovermaps_ep1(self):
        try:
            count_vo = 0
            self.safe_update_status("Processing ep1 voiceovermap files...")
            ref_data = load_json(os.path.join(BASE_DIR, "resources", "cdt.json"))
            audio_language = self.config_data["audio_language"]
            if audio_language == "ALL":
                for lang, codes in language_codes.items():
                    audio_code, full_audio_code = codes
                    ep1_dir = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code)
                    file_mappings = {
                        f"{audio_code}_ep1_voiceovermap.json.json": ("voiceovermap.json.json", "vo"),
                        f"{audio_code}_ep1_voiceovermap_helmet.json.json": ("voiceovermap_helmet.json.json", "vo_helmet"),
                        f"{audio_code}_ep1_voiceovermap_holocall.json.json": ("voiceovermap_holocall.json.json", "vo_holocall"),
                        f"{audio_code}_ep1_voiceovermap_rewinded.json.json": ("voiceovermap_rewinded.json.json", "vo_rewinded"),
                    }
                    for filename, (new_filename, folder_replacement) in file_mappings.items():
                        file_path = os.path.join(ep1_dir, filename)
                        if os.path.exists(file_path):
                            data = load_json(file_path)
                            entries = data.get("Data", {}).get("RootChunk", {}).get("root", {}).get("Data", {}).get("entries", [])
                            for entry in entries:
                                sid = entry.get("stringId")
                                if sid in ref_data:
                                    new_female = ref_data[sid].get("femaleResPath$value")
                                    new_male = ref_data[sid].get("maleResPath$value")
                                    if new_female:
                                        new_female = new_female.replace("[folder]", folder_replacement)
                                        entry["femaleResPath"]["DepotPath"]["$value"] = new_female
                                    if new_male:
                                        new_male = new_male.replace("[folder]", folder_replacement)
                                        entry["maleResPath"]["DepotPath"]["$value"] = new_male
                                    count_vo += 1
                            target_path = os.path.join(ep1_dir, new_filename)
                            save_json(target_path, data)
                        else:
                            logging.warning(f"File {file_path} does not exist and will be skipped.")
                return count_vo
            else:
                audio_code, full_audio_code = language_codes[audio_language]
                ep1_dir = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code)
                file_mappings = {
                    f"{audio_code}_ep1_voiceovermap.json.json": ("voiceovermap.json.json", "vo"),
                    f"{audio_code}_ep1_voiceovermap_helmet.json.json": ("voiceovermap_helmet.json.json", "vo_helmet"),
                    f"{audio_code}_ep1_voiceovermap_holocall.json.json": ("voiceovermap_holocall.json.json", "vo_holocall"),
                    f"{audio_code}_ep1_voiceovermap_rewinded.json.json": ("voiceovermap_rewinded.json.json", "vo_rewinded"),
                }
                for filename, (new_filename, folder_replacement) in file_mappings.items():
                    file_path = os.path.join(ep1_dir, filename)
                    if os.path.exists(file_path):
                        data = load_json(file_path)
                        entries = data.get("Data", {}).get("RootChunk", {}).get("root", {}).get("Data", {}).get("entries", [])
                        for entry in entries:
                            sid = entry.get("stringId")
                            if sid in ref_data:
                                new_female = ref_data[sid].get("femaleResPath$value")
                                new_male = ref_data[sid].get("maleResPath$value")
                                if new_female:
                                    new_female = new_female.replace("[folder]", folder_replacement)
                                    entry["femaleResPath"]["DepotPath"]["$value"] = new_female
                                if new_male:
                                    new_male = new_male.replace("[folder]", folder_replacement)
                                    entry["maleResPath"]["DepotPath"]["$value"] = new_male
                                count_vo += 1
                        target_path = os.path.join(ep1_dir, new_filename)
                        save_json(target_path, data)
                    else:
                        logging.warning(f"File {file_path} does not exist and will be skipped.")
                return count_vo
        except Exception as e:
            logging.error("Failed to process ep1 voiceovermaps", exc_info=True)
            self.safe_show_error("Failed to process ep1 voiceovermaps. Check the log for details.")
            return 0

    # --- Step 4 : Duration dialogue ---
    def update_stringidvariantlengthsreport(self, episode, reference_data):
        try:
            self.safe_update_status("Processing duration files...")
            count_updated = 0
            audio_language = self.config_data["audio_language"]
            if audio_language == "ALL":
                allowed_audio = ["English", "Polish", "Brazilian", "Chinese", "French", "German", "Italian", "Japanese", "Korean", "Russian", "Spanish"]
                for lang in allowed_audio:
                    audio_code, full_audio_code = language_codes[lang]
                    if episode == "base":
                        source_path = os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code,
                           f"{audio_code}_base_stringidvariantlengthsreport.json.json")
                        target_path = os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code,
                           "stringidvariantlengthsreport.json.json")
                    elif episode == "ep1":
                        source_path = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code,
                           f"{audio_code}_ep1_stringidvariantlengthsreport.json.json")
                        target_path = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code,
                           "stringidvariantlengthsreport.json.json")
                    else:
                        logging.error(f"Invalid episode: {episode}")
                        continue

                    data = load_json(source_path)
                    for entry in data["Data"]["RootChunk"]["root"]["Data"]["entries"]:
                        string_id = entry["stringId"]
                        if string_id in reference_data:
                            entry["femaleLength"] = float(reference_data[string_id]["translated_femaleLength"])
                            entry["maleLength"] = float(reference_data[string_id]["translated_maleLength"])
                            logging.info(f"Updated {string_id} in {episode} report for {lang}.")
                            count_updated += 1
                    save_json(target_path, data)
                return count_updated
            
            else:
                audio_code, full_audio_code = language_codes[audio_language]
                if episode == "base":
                    source_path = os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code, f"{audio_code}_base_stringidvariantlengthsreport.json.json")
                    target_path = os.path.join(BASE_DIR, "raw", "base", "localization", full_audio_code, "stringidvariantlengthsreport.json.json")
                elif episode == "ep1":
                    source_path = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code, f"{audio_code}_ep1_stringidvariantlengthsreport.json.json")
                    target_path = os.path.join(BASE_DIR, "raw", "ep1", "localization", full_audio_code, "stringidvariantlengthsreport.json.json")
                else:
                    logging.error(f"Invalid episode: {episode}")
                    return 0
                data = load_json(source_path)
                entries = data["Data"]["RootChunk"]["root"]["Data"]["entries"]
                for entry in entries:
                    string_id = entry["stringId"]
                    if string_id in reference_data:
                        entry["femaleLength"] = float(reference_data[string_id]["translated_femaleLength"])
                        entry["maleLength"] = float(reference_data[string_id]["translated_maleLength"])
                        logging.info(f"Updated {string_id} in {episode} report.")
                        count_updated += 1
                save_json(target_path, data)
                return count_updated
        except Exception as e:
            logging.error(f"Failed to update {episode} stringidvariantlengthsreport", exc_info=True)
            self.safe_show_error(f"Failed to update {episode} dialogue durations. Check the log for details.")
            return 0

    # --- Step 5 : Subtitles ---
    def modify_subtitles(self, episode, subtitle_code, reference_data):
        try:
            self.safe_update_status("Processing subtitles files...")
            total_modified = 0
            subtitle_language = self.config_data["subtitle_language"]
            if subtitle_language == "ALL":
                for lang, codes in language_codes.items():
                    code, full_code = codes
                    vanilla_path = os.path.join(BASE_DIR, "raw", episode, "localization", full_code, "vanillasubtitles")
                    for root_dir, _, files in os.walk(vanilla_path):
                        for file in files:
                            if file.endswith(".json"):
                                vanilla_file_path = os.path.join(root_dir, file)
                                target_file_path = os.path.join(root_dir.replace("vanillasubtitles", "subtitles"), file)
                                subtitle_data = load_json(vanilla_file_path)
                                entries = subtitle_data["Data"]["RootChunk"]["root"]["Data"]["entries"]
                                modified = False
                                for entry in entries:
                                    string_id = entry["stringId"]
                                    if string_id in reference_data:
                                        entry["femaleVariant"] = reference_data[string_id][f"{code}_femaleVariant"]
                                        entry["maleVariant"] = reference_data[string_id][f"{code}_maleVariant"]
                                        modified = True
                                        total_modified += 1
                                if modified:
                                    os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                                    save_json(target_file_path, subtitle_data)
                return total_modified
            else:
                _, subtitle_full_code = language_codes[subtitle_language]
                vanilla_path = os.path.join(BASE_DIR, "raw", episode, "localization", subtitle_full_code, "vanillasubtitles")
                for root_dir, _, files in os.walk(vanilla_path):
                    for file in files:
                        if file.endswith(".json"):
                            vanilla_file_path = os.path.join(root_dir, file)
                            target_file_path = os.path.join(root_dir.replace("vanillasubtitles", "subtitles"), file)
                            subtitle_data = load_json(vanilla_file_path)
                            entries = subtitle_data["Data"]["RootChunk"]["root"]["Data"]["entries"]
                            modified = False
                            for entry in entries:
                                string_id = entry["stringId"]
                                if string_id in reference_data:
                                    entry["femaleVariant"] = reference_data[string_id][f"{subtitle_code}_femaleVariant"]
                                    entry["maleVariant"] = reference_data[string_id][f"{subtitle_code}_maleVariant"]
                                    modified = True
                                    total_modified += 1
                            if modified:
                                os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                                save_json(target_file_path, subtitle_data)
                return total_modified
        except Exception as e:
            logging.error(f"Failed to modify {episode} subtitles", exc_info=True)
            self.safe_show_error(f"Failed to modify {episode} subtitles. Check the log for details.")
            return 0

    # --- Step 6 : Cleaning ---
    def cleanup_intermediate_files(self):
        raw_dir = os.path.join(BASE_DIR, "raw")
        audio_language = self.config_data.get("audio_language", "English")
        subtitle_language = self.config_data.get("subtitle_language", "English")
        self.safe_update_status("Cleaning intermediate files...")
        for episode in ["base", "ep1"]:
            # Cleanup for audio files
            if audio_language == "ALL":
                for lang, codes in language_codes.items():
                    audio_code, full_audio_code = codes
                    loc_audio_dir = os.path.join(raw_dir, episode, "localization", full_audio_code)
                    if os.path.exists(loc_audio_dir):
                        if episode == "base":
                            lipmap_file = os.path.join(raw_dir, episode, "localization", f"{audio_code}_lipmap.json")
                            if os.path.exists(lipmap_file):
                                try:
                                    os.remove(lipmap_file)
                                    logging.info(f"Removed lipmap file: {lipmap_file}")
                                except Exception as e:
                                    logging.error(f"Error removing lipmap file {lipmap_file}", exc_info=True)
                        report_filename = f"{audio_code}_{'base' if episode=='base' else 'ep1'}_stringidvariantlengthsreport.json.json"
                        report_file = os.path.join(loc_audio_dir, report_filename)
                        if os.path.exists(report_file):
                            try:
                                os.remove(report_file)
                                logging.info(f"Removed report file: {report_file}")
                            except Exception as e:
                                logging.error(f"Error removing report file {report_file}", exc_info=True)
                        vo_prefix = f"{audio_code}_{'base' if episode=='base' else 'ep1'}_voiceovermap"
                        for file in os.listdir(loc_audio_dir):
                            if file.startswith(vo_prefix) and file.endswith(".json.json"):
                                vo_file = os.path.join(loc_audio_dir, file)
                                try:
                                    os.remove(vo_file)
                                    logging.info(f"Removed voiceovermap file: {vo_file}")
                                except Exception as e:
                                    logging.error(f"Error removing voiceovermap file {vo_file}", exc_info=True)
            else:
                audio_code, full_audio_code = language_codes.get(audio_language, ("EN", "en-us"))
                loc_audio_dir = os.path.join(raw_dir, episode, "localization", full_audio_code)
                if os.path.exists(loc_audio_dir):
                    if episode == "base":
                        lipmap_file = os.path.join(raw_dir, episode, "localization", f"{audio_code}_lipmap.json")
                        if os.path.exists(lipmap_file):
                            try:
                                os.remove(lipmap_file)
                                logging.info(f"Removed lipmap file: {lipmap_file}")
                            except Exception as e:
                                logging.error(f"Error removing lipmap file {lipmap_file}", exc_info=True)
                    report_filename = f"{audio_code}_{'base' if episode=='base' else 'ep1'}_stringidvariantlengthsreport.json.json"
                    report_file = os.path.join(loc_audio_dir, report_filename)
                    if os.path.exists(report_file):
                        try:
                            os.remove(report_file)
                            logging.info(f"Removed report file: {report_file}")
                        except Exception as e:
                            logging.error(f"Error removing report file {report_file}", exc_info=True)
                    vo_prefix = f"{audio_code}_{'base' if episode=='base' else 'ep1'}_voiceovermap"
                    for file in os.listdir(loc_audio_dir):
                        if file.startswith(vo_prefix) and file.endswith(".json.json"):
                            vo_file = os.path.join(loc_audio_dir, file)
                            try:
                                os.remove(vo_file)
                                logging.info(f"Removed voiceovermap file: {vo_file}")
                            except Exception as e:
                                logging.error(f"Error removing voiceovermap file {vo_file}", exc_info=True)
            # Cleanup for subtitles files
            if subtitle_language == "ALL":
                for lang, codes in language_codes.items():
                    _, full_subtitle_code = codes
                    loc_sub_dir = os.path.join(raw_dir, episode, "localization", full_subtitle_code)
                    if os.path.exists(loc_sub_dir):
                        vanilla_dir = os.path.join(loc_sub_dir, "vanillasubtitles")
                        if os.path.exists(vanilla_dir):
                            try:
                                shutil.rmtree(vanilla_dir)
                                logging.info(f"Removed vanillasubtitles folder: {vanilla_dir}")
                            except Exception as e:
                                logging.error(f"Error removing vanillasubtitles folder {vanilla_dir}", exc_info=True)
            else:
                _, full_subtitle_code = language_codes.get(subtitle_language, ("EN", "en-us"))
                loc_sub_dir = os.path.join(raw_dir, episode, "localization", full_subtitle_code)
                if os.path.exists(loc_sub_dir):
                    vanilla_dir = os.path.join(loc_sub_dir, "vanillasubtitles")
                    if os.path.exists(vanilla_dir):
                        try:
                            shutil.rmtree(vanilla_dir)
                            logging.info(f"Removed vanillasubtitles folder: {vanilla_dir}")
                        except Exception as e:
                            logging.error(f"Error removing vanillasubtitles folder {vanilla_dir}", exc_info=True)

        logging.info("Intermediate files cleanup completed.")

        # Delete the "files" folder once the process is fully complete
        files_dir = "files"
        if os.path.exists(files_dir):
            try:
                shutil.rmtree(files_dir)
                logging.info(f"Cdpr's files successfully deleted.")
            except Exception as e:
                logging.error(f"Error while deleting the '{files_dir}' folder", exc_info=True)

        # Also delete the "res" folder once the process is fully complete
        res_dir = "res"
        if os.path.exists(res_dir):
            try:
                shutil.rmtree(res_dir)
                logging.info(f"Nttn's files successfully deleted.")
            except Exception as e:
                logging.error(f"Error while deleting the '{res_dir}' folder", exc_info=True)

        self.safe_update_status("Final step")

if __name__ == "__main__":
    app = CNCApp()
    app.mainloop()
