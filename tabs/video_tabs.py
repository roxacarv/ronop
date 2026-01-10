import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox

class VideoSplitTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.split_file_var = ctk.StringVar()
        self.start_time_var = ctk.StringVar()
        self.end_time_var = ctk.StringVar()

        ctk.CTkLabel(self, text="Arquivo de entrada:").pack(pady=(20, 5))
        ctk.CTkEntry(self, textvariable=self.split_file_var, width=400).pack()
        ctk.CTkButton(self, text="Carregar vídeo", command=self.load_video_for_split).pack(pady=10)

        frame = ctk.CTkFrame(self)
        frame.pack(pady=10)
        ctk.CTkLabel(frame, text="Início (hh:mm:ss):").grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkEntry(frame, textvariable=self.start_time_var, width=120).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(frame, text="Fim (hh:mm:ss):").grid(row=1, column=2, padx=5)
        ctk.CTkEntry(frame, textvariable=self.end_time_var, width=120).grid(row=0, column=3, padx=5)

        ctk.CTkButton(self, text="Dividir vídeo", command=self.split_video).pack(pady=15)

    def load_video_for_split(self):
        file = filedialog.askopenfilename(filetypes=[("Vídeos MP4", "*.mp4"), ("Todos os arquivos", "*.*")])
        if not file:
            return
        self.split_file_var.set(file)

        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            duration = float(result.stdout.strip())
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            formatted_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            self.start_time_var.set("00:00:00")
            self.end_time_var.set(formatted_duration)
            messagebox.showinfo("Vídeo carregado", f"Duração: {formatted_duration}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o vídeo:\n{e}")

    def split_video(self):
        input_file = self.split_file_var.get()
        start = self.start_time_var.get()
        end = self.end_time_var.get()
        if not input_file or not start or not end:
            messagebox.showerror("Erro", "Preencha todos os campos.")
            return

        output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if not output_file:
            return

        if os.path.exists(output_file):
            if not messagebox.askyesno("Arquivo existe", f"{output_file} já existe. Deseja sobrescrever?"):
                return

        cmd = ["ffmpeg", "-i", input_file, "-ss", start, "-to", end, "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental", output_file]
        try:
            subprocess.run(cmd, check=True)
            messagebox.showinfo("Sucesso", f"Vídeo salvo em:\n{output_file}")
        except subprocess.CalledProcessError:
            messagebox.showerror("Erro", "Falha ao dividir o vídeo.")


class VideoJoinTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.join_files = []

        ctk.CTkLabel(self, text="Selecione os vídeos para juntar:").pack(pady=10)
        ctk.CTkButton(self, text="Adicionar vídeos", command=self.add_join_files).pack(pady=5)

        self.join_listbox = ctk.CTkTextbox(self, height=200, width=500)
        self.join_listbox.pack(pady=10)

        ctk.CTkButton(self, text="Juntar vídeos", command=self.join_videos).pack(pady=10)

    def add_join_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Vídeos MP4", "*.mp4")])
        if files:
            self.join_files.extend(files)
            self.join_listbox.delete("1.0", "end")
            for f in self.join_files:
                self.join_listbox.insert("end", f + "\n")

    def join_videos(self):
        if len(self.join_files) < 2:
            messagebox.showerror("Erro", "Adicione pelo menos dois vídeos para juntar.")
            return

        output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if not output_file:
            return

        if os.path.exists(output_file):
            if not messagebox.askyesno("Arquivo existe", f"{output_file} já existe. Deseja sobrescrever?"):
                return

        list_file = "files_to_join.txt"
        with open(list_file, "w") as f:
            for video in self.join_files:
                f.write(f"file '{os.path.abspath(video)}'\n")

        cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_file]
        try:
            subprocess.run(cmd, check=True)
            os.remove(list_file)
            messagebox.showinfo("Sucesso", f"Vídeos juntados em:\n{output_file}")
        except subprocess.CalledProcessError:
            messagebox.showerror("Erro", "Falha ao juntar os vídeos.")


class VideoConvertTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.convert_file_var = ctk.StringVar()
        self.convert_start_var = ctk.StringVar(value="00:00:00")
        self.convert_end_var = ctk.StringVar()
        self.format_var = ctk.StringVar(value="GIF")

        ctk.CTkLabel(self, text="Arquivo de entrada:").pack(pady=(20, 5))
        ctk.CTkEntry(self, textvariable=self.convert_file_var, width=400).pack()
        ctk.CTkButton(self, text="Carregar vídeo", command=self.load_video_for_convert).pack(pady=10)

        frame_time = ctk.CTkFrame(self)
        frame_time.pack(pady=10)
        ctk.CTkLabel(frame_time, text="Início (hh:mm:ss):").grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkEntry(frame_time, textvariable=self.convert_start_var, width=120).grid(row=0, column=1)
        ctk.CTkLabel(frame_time, text="Fim (hh:mm:ss):").grid(row=0, column=2, padx=5)
        ctk.CTkEntry(frame_time, textvariable=self.convert_end_var, width=120).grid(row=0, column=3)

        ctk.CTkLabel(self, text="Formato de saída:").pack(pady=(10, 5))
        ctk.CTkOptionMenu(self, variable=self.format_var, values=["GIF", "WebM", "MP3"]).pack(pady=5)

        ctk.CTkButton(self, text="Converter", command=self.convert_video).pack(pady=15)

    def load_video_for_convert(self):
        file = filedialog.askopenfilename(filetypes=[("Vídeos MP4", "*.mp4"), ("Todos os arquivos", "*.*")])
        if not file:
            return
        self.convert_file_var.set(file)

        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            duration = float(result.stdout.strip())
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            formatted_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            self.convert_start_var.set("00:00:00")
            self.convert_end_var.set(formatted_duration)
            messagebox.showinfo("Vídeo carregado", f"Duração: {formatted_duration}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o vídeo:\n{e}")

    def convert_video(self):
        input_file = self.convert_file_var.get()
        start = self.convert_start_var.get()
        end = self.convert_end_var.get()
        output_format = self.format_var.get()

        if not input_file or not end:
            messagebox.showerror("Erro", "Selecione o vídeo e informe os tempos.")
            return

        if output_format == "GIF":
            ext, file_type = ".gif", ("GIF", "*.gif")
        elif output_format == "WebM":
            ext, file_type = ".webm", ("WebM", "*.webm")
        elif output_format == "MP3":
            ext, file_type = ".mp3", ("MP3", "*.mp3")
        else:
            return

        output_file = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[file_type])
        if not output_file:
            return

        if os.path.exists(output_file):
            if not messagebox.askyesno("Arquivo existe", f"{output_file} já existe. Deseja sobrescrever?"):
                return

        cmd = ["ffmpeg", "-i", input_file, "-ss", start, "-to", end]
        if output_format == "GIF":
            cmd.extend(["-vf", "fps=10,scale=480:-1:flags=lanczos", "-loop", "0"])
        elif output_format == "WebM":
            cmd.extend(["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "30", "-c:a", "libvorbis"])
        elif output_format == "MP3":
            cmd.extend(["-vn", "-acodec", "libmp3lame", "-q:a", "2"])
        cmd.append(output_file)

        try:
            subprocess.run(cmd, check=True)
            messagebox.showinfo("Sucesso", f"Conversão para {output_format} concluída:\n{output_file}")
        except subprocess.CalledProcessError:
            messagebox.showerror("Erro", f"Falha ao converter para {output_format}.")
