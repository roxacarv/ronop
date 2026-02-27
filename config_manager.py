import json
import os

class ConfigManager:
    CONFIG_FILE = os.path.expanduser("~/.ronop_config.json")
    
    DEFAULT_CONFIG = {
        "theme": "dark",
        "default_folders": {
            "Dividir Vídeo": "",
            "Juntar Vídeos": "",
            "Converter Formatos": "",
            "Vídeo -> Imagens": "",
            "Redimensionar (Crop)": "",
            "Dividir PDF": ""
        }
    }

    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Merge with default to handle missing keys in old versions
                    merged = self.DEFAULT_CONFIG.copy()
                    merged.update(config)
                    return merged
            except Exception:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_theme(self):
        return self.config.get("theme", "dark")

    def set_theme(self, theme):
        self.config["theme"] = theme
        self.save_config()

    def get_default_folder(self, tab_name):
        return self.config.get("default_folders", {}).get(tab_name, "")

    def set_default_folder(self, tab_name, folder_path):
        if "default_folders" not in self.config:
            self.config["default_folders"] = {}
        self.config["default_folders"][tab_name] = folder_path
        self.save_config()
