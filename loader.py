import os
import platform
import msgs

# the folder of the 2 text files
CONFIG_FOLDER_NAME = "dashboard_holder_files"
EXIT_FILENAME = "exit_phrases.txt"
LOG_FILENAME = "log_phrases.txt"

def get_documents_path():
    system = platform.system()
    if system == "Windows":
        import ctypes.wintypes
        CSIDL_PERSONAL = 5
        SHGFP_TYPE_CURRENT = 0
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
        return buf.value
    else:
        return os.path.join(os.path.expanduser("~"), "Documents")

def ensure_config_files():
    docs_path = get_documents_path()
    config_path = os.path.join(docs_path, CONFIG_FOLDER_NAME)

    # create the directory
    if not os.path.exists(config_path):
        try:
            os.makedirs(config_path)
            print(f"Created configuration folder at: {config_path}")
        except OSError as e:
            print(f"Error creating config folder: {e}")
            return None, None

    exit_file_path = os.path.join(config_path, EXIT_FILENAME)
    log_file_path = os.path.join(config_path, LOG_FILENAME)

    # create the exit phrases file
    if not os.path.exists(exit_file_path):
        try:
            with open(exit_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(msgs.EXIT_PHRASES))
        except Exception as e:
            print(f"Could not create {EXIT_FILENAME}: {e}")

    # create the gimmick log phrases file
    if not os.path.exists(log_file_path):
        try:
            with open(log_file_path, "w", encoding="utf-8") as f:
                lines = [f"{lvl.replace('[','').replace(']','').replace('/','')} | {msg}" for lvl, msg in msgs.LOG_PHRASES]
                f.write("\n".join(lines))
        except Exception as e:
            print(f"Could not create {LOG_FILENAME}: {e}")

    return exit_file_path, log_file_path

def load_configs():
    exit_path, log_path = ensure_config_files()
    
    loaded_exits = []
    loaded_logs = []

    # read exits
    if exit_path and os.path.exists(exit_path):
        try:
            with open(exit_path, "r", encoding="utf-8") as f:
                loaded_exits = [line.strip() for line in f if line.strip()]
        except Exception:
            pass

    # read logs
    if log_path and os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" in line:
                        parts = line.strip().split("|", 1)
                        raw_level = parts[0].strip()
                        msg = parts[1].strip()
                        
                        if "WARN" in raw_level: level_tag = "[yellow]WARN[/]"
                        elif "CRIT" in raw_level: level_tag = "[red]CRIT[/]"
                        elif "DEBUG" in raw_level: level_tag = "[blue]DEBUG[/]"
                        else: level_tag = "[green]INFO[/]"
                        
                        loaded_logs.append((level_tag, msg))
        except Exception:
            pass

    # fallback
    final_exits = loaded_exits if loaded_exits else msgs.EXIT_PHRASES
    final_logs = loaded_logs if loaded_logs else msgs.LOG_PHRASES

    return final_exits, final_logs

# testing
if __name__ == "__main__":
    e, l = load_configs()
    print(f"Loaded {len(e)} exit phrases and {len(l)} log phrases.")
    print(f"Files located in: {os.path.join(get_documents_path(), CONFIG_FOLDER_NAME)}")