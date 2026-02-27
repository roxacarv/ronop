import customtkinter as ctk
from tkinter import filedialog, messagebox

class ConfigTab(ctk.CTkFrame):
    def __init__(self, master, config_manager):
        super().__init__(master)
        self.config_manager = config_manager

        # Theme Section
        ctk.CTkLabel(self, text="Configurações de Aparência", font=("Arial", 16, "bold")).pack(pady=(20, 10))
        
        theme_frame = ctk.CTkFrame(self)
        theme_frame.pack(pady=10, fill="x", padx=40)
        
        ctk.CTkLabel(theme_frame, text="Tema:").pack(side="left", padx=10, pady=10)
        
        self.theme_var = ctk.StringVar(value=self.config_manager.get_theme().capitalize())
        theme_menu = ctk.CTkOptionMenu(
            theme_frame, 
            values=["System", "Light", "Dark"],
            variable=self.theme_var,
            command=self.change_theme
        )
        theme_menu.pack(side="right", padx=10, pady=10)

        # Folders Section
        ctk.CTkLabel(self, text="Pastas Padrão por Aba", font=("Arial", 16, "bold")).pack(pady=(20, 10))
        
        folders_frame = ctk.CTkScrollableFrame(self, height=250)
        folders_frame.pack(pady=10, fill="both", expand=True, padx=40)

        self.folder_vars = {}
        tabs = [
            "Dividir Vídeo", 
            "Juntar Vídeos", 
            "Converter Formatos", 
            "Vídeo -> Imagens", 
            "Redimensionar (Crop)", 
            "Dividir PDF"
        ]

        for tab_name in tabs:
            row_frame = ctk.CTkFrame(folders_frame)
            row_frame.pack(pady=5, fill="x")
            
            ctk.CTkLabel(row_frame, text=tab_name, width=150, anchor="w").pack(side="left", padx=10)
            
            path_var = ctk.StringVar(value=self.config_manager.get_default_folder(tab_name))
            self.folder_vars[tab_name] = path_var
            
            ctk.CTkEntry(row_frame, textvariable=path_var, width=250).pack(side="left", padx=5)
            
            ctk.CTkButton(
                row_frame, 
                text="Selecionar", 
                width=80,
                command=lambda tn=tab_name, pv=path_var: self.select_folder(tn, pv)
            ).pack(side="right", padx=10)

        ctk.CTkButton(self, text="Salvar Todas as Configurações", command=self.save_all).pack(pady=20)

    def change_theme(self, new_theme):
        theme = new_theme.lower()
        self.config_manager.set_theme(theme)
        ctk.set_appearance_mode(theme)

    def select_folder(self, tab_name, path_var):
        folder = filedialog.askdirectory()
        if folder:
            path_var.set(folder)
            self.config_manager.set_default_folder(tab_name, folder)

    def save_all(self):
        for tab_name, path_var in self.folder_vars.items():
            self.config_manager.set_default_folder(tab_name, path_var.get())
        
        messagebox.showinfo("Configurações", "Todas as configurações foram salvas com sucesso!")
