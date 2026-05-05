import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES

class VideoRotateTab(ctk.CTkFrame, TkinterDnD.DnDWrapper):
    def __init__(self, master, config_manager=None):
        super().__init__(master)
        TkinterDnD.DnDWrapper.__init__(self)
        self.config_manager = config_manager
        self.input_file_var = ctk.StringVar()
        self.rotation_var = ctk.StringVar(value="90° Horário")
        self.last_dir = ""

        ctk.CTkLabel(self, text="Arquivo de entrada:").pack(pady=(20, 5))
        ctk.CTkEntry(self, textvariable=self.input_file_var, width=400).pack()
        ctk.CTkButton(self, text="Carregar vídeo", command=self.load_video).pack(pady=10)

        ctk.CTkLabel(self, text="Opções de Rotação:").pack(pady=(10, 5))
        ctk.CTkOptionMenu(
            self, 
            variable=self.rotation_var, 
            values=["90° Horário", "90° Anti-Horário", "180°"]
        ).pack(pady=5)

        ctk.CTkButton(self, text="Rotacionar", fg_color="green", hover_color="darkgreen", command=self.rotate_video).pack(pady=20)

        # DnD Support
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        self.input_file_var.set(file_path)
        self.last_dir = os.path.dirname(file_path)

    def load_video(self):
        initial_dir = self.config_manager.get_default_folder("Rotacionar Vídeo") if self.config_manager else ""
        file = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("Vídeos", "*.mp4 *.mkv *.mov *.avi"), ("Todos os arquivos", "*.*")]
        )
        if file:
            self.input_file_var.set(file)
            self.last_dir = os.path.dirname(file)

    def rotate_video(self):
        input_file = self.input_file_var.get()
        rotation_mode = self.rotation_var.get()

        if not input_file:
            messagebox.showerror("Erro", "Selecione o arquivo de entrada.")
            return

        initial_dir = self.last_dir or (self.config_manager.get_default_folder("Rotacionar Vídeo") if self.config_manager else "")
        output_file = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            defaultextension=".mp4", 
            filetypes=[("MP4 files", "*.mp4")]
        )
        if not output_file:
            return

        if os.path.exists(output_file):
            if not messagebox.askyesno("Arquivo existe", f"{output_file} já existe. Deseja sobrescrever?"):
                return

        # FFmpeg transpose values:
        # 1 = 90Clockwise
        # 2 = 90CounterClockwise
        
        if rotation_mode == "90° Horário":
            vf_filter = "transpose=1"
        elif rotation_mode == "90° Anti-Horário":
            vf_filter = "transpose=2"
        elif rotation_mode == "180°":
            vf_filter = "transpose=1,transpose=1"
        else:
            vf_filter = "transpose=1"

        cmd = [
            "ffmpeg", "-y", "-i", input_file, 
            "-vf", vf_filter, 
            "-c:v", "libx264", "-crf", "18", 
            "-c:a", "copy", 
            output_file
        ]

        try:
            subprocess.run(cmd, check=True)
            messagebox.showinfo("Sucesso", f"Vídeo rotacionado com sucesso!\nSalvo em:\n{output_file}")
        except subprocess.CalledProcessError:
            messagebox.showerror("Erro", "Falha ao rotacionar o vídeo.")
