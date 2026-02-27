import os
import subprocess
import shutil
import tempfile
import zipfile
import io
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk

class FrameRearrangeWindow(ctk.CTkToplevel):
    def __init__(self, parent, selected_frames, config_manager=None, last_dir=""):
        super().__init__(parent)
        self.title("Reordenar Quadros")
        self.geometry("600x700")
        self.selected_frames = selected_frames  # List of dicts: {"image": PIL.Image, "name": str}
        self.config_manager = config_manager
        self.last_dir = last_dir
        
        self.label = ctk.CTkLabel(self, text="Organize os quadros e exporte", font=("Arial", 16, "bold"))
        self.label.pack(pady=15)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=550, height=450)
        self.scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.render_items()
        
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=20, fill="x")
        
        ctk.CTkButton(button_frame, text="Exportar PNGs (ZIP)", command=self.save_as_zip, fg_color="#3498db", hover_color="#2980b9").pack(expand=True)

    def render_items(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        for i, item in enumerate(self.selected_frames):
            frame = ctk.CTkFrame(self.scroll_frame)
            frame.pack(fill="x", pady=5, padx=5)
            
            # Thumbnail
            img = item["image"].copy()
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)
            
            img_label = ctk.CTkLabel(frame, image=photo, text="")
            img_label.image = photo 
            img_label.pack(side="left", padx=10, pady=5)
            
            ctk.CTkLabel(frame, text=item["name"], font=("Arial", 12)).pack(side="left", padx=10)
            
            # Control buttons
            btn_frame = ctk.CTkFrame(frame)
            btn_frame.pack(side="right", padx=10)
            
            ctk.CTkButton(btn_frame, text="↑", width=40, command=lambda idx=i: self.move_up(idx)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="↓", width=40, command=lambda idx=i: self.move_down(idx)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Remover", width=70, fg_color="#e74c3c", hover_color="#c0392b", command=lambda idx=i: self.remove_item(idx)).pack(side="left", padx=5)

    def move_up(self, index):
        if index > 0:
            self.selected_frames[index], self.selected_frames[index-1] = self.selected_frames[index-1], self.selected_frames[index]
            self.render_items()

    def move_down(self, index):
        if index < len(self.selected_frames) - 1:
            self.selected_frames[index], self.selected_frames[index+1] = self.selected_frames[index+1], self.selected_frames[index]
            self.render_items()

    def remove_item(self, index):
        self.selected_frames.pop(index)
        self.render_items()
        if not self.selected_frames:
            self.destroy()

    def save_as_zip(self):
        initial_dir = self.last_dir or (self.config_manager.get_default_folder("Vídeo -> Imagens") if self.config_manager else "")
        output_file = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            defaultextension=".zip", 
            filetypes=[("ZIP files", "*.zip")]
        )
        if not output_file:
            return
        
        if os.path.exists(output_file):
            if not messagebox.askyesno("Arquivo existe", f"{output_file} já existe. Deseja sobrescrever?"):
                return
        
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for i, item in enumerate(self.selected_frames):
                    img_byte_arr = io.BytesIO()
                    item["image"].save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"quadro_{i+1}_{item['name']}.png", img_byte_arr.getvalue())
            
            with open(output_file, "wb") as f:
                f.write(zip_buffer.getvalue())
            
            messagebox.showinfo("Sucesso", f"Arquivo ZIP criado com sucesso!\nSalvo em: {output_file}")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar ZIP: {e}")


class VideoToImagesTab(ctk.CTkFrame, TkinterDnD.DnDWrapper):
    def __init__(self, master, config_manager=None):
        super().__init__(master)
        TkinterDnD.DnDWrapper.__init__(self) # Initialize DnDWrapper explicitly
        self.config_manager = config_manager
        self.video_path = None
        self.last_dir = ""
        self.temp_dir = None
        self.frames_data = [] # List of dicts: {"image": PIL.Image, "name": str}
        self.selected_indices = []
        self.thumbnail_frames = {}

        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(top_frame, text="Carregar Vídeo/GIF", command=self.load_video).pack(side="left", padx=5)
        self.status_label = ctk.CTkLabel(top_frame, text="Nenhum arquivo selecionado")
        self.status_label.pack(side="left", padx=20)

        # Interval selection
        ctk.CTkLabel(top_frame, text="FPS:").pack(side="left", padx=(10, 2))
        self.fps_var = ctk.StringVar(value="1")
        self.fps_entry = ctk.CTkEntry(top_frame, textvariable=self.fps_var, width=40)
        self.fps_entry.pack(side="left", padx=5)

        self.btn_next = ctk.CTkButton(top_frame, text="Próximo (Organizar) →", state="disabled", command=self.open_rearrange_window, fg_color="#f39c12", hover_color="#d35400")
        self.btn_next.pack(side="right", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self, label_text="Selecione os quadros clicando neles")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # DnD Support
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        self.video_path = file_path
        self.last_dir = os.path.dirname(file_path)
        self.status_label.configure(text=os.path.basename(file_path))
        self.extract_frames()

    def load_video(self):
        initial_dir = self.config_manager.get_default_folder("Vídeo -> Imagens") if self.config_manager else ""
        file = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("Vídeos/GIFs", "*.mp4 *.gif *.mov *.avi *.webm"), ("Todos", "*.*")]
        )
        if not file:
            return
        
        self.video_path = file
        self.last_dir = os.path.dirname(file)
        self.status_label.configure(text=os.path.basename(file))
        self.extract_frames()

    def extract_frames(self):
        # Limpar existentes
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.thumbnail_frames = {}
        self.frames_data = []
        self.selected_indices = []
        self.btn_next.configure(state="disabled")

        # Criar diretório temporário
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.temp_dir = tempfile.mkdtemp()

        fps = self.fps_var.get()
        try:
            # Comando FFmpeg para extrair quadros
            # %04d.png para ter nomes ordenados
            cmd = [
                "ffmpeg", "-y", "-i", self.video_path,
                "-vf", f"fps={fps}",
                os.path.join(self.temp_dir, "frame_%04d.png")
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Carregar imagens extraídas
            files = sorted(os.listdir(self.temp_dir))
            if not files:
                messagebox.showwarning("Aviso", "Nenhum quadro foi extraído. Verifique o FPS ou o arquivo.")
                return

            cols = 4
            for i, filename in enumerate(files):
                full_path = os.path.join(self.temp_dir, filename)
                img = Image.open(full_path)
                
                # Armazenar dados
                self.frames_data.append({"image": img.copy(), "name": filename})
                
                # Criar miniatura para o UI
                thumb_img = img.copy()
                thumb_img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(thumb_img)
                
                f = ctk.CTkFrame(self.scroll, width=130, height=180, border_width=0)
                f.grid(row=i // cols, column=i % cols, padx=10, pady=10)
                f.grid_propagate(False)
                
                l = ctk.CTkLabel(f, image=photo, text="")
                l.image = photo
                l.pack(expand=True, fill="both", padx=5, pady=5)
                
                ctk.CTkLabel(f, text=filename, font=("Arial", 10)).pack(pady=(0, 5))
                
                l.bind("<Button-1>", lambda e, idx=i: self.toggle_frame(idx))
                f.bind("<Button-1>", lambda e, idx=i: self.toggle_frame(idx))
                
                self.thumbnail_frames[i] = f
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao extrair quadros: {e}")

    def toggle_frame(self, idx):
        if idx in self.selected_indices:
            self.selected_indices.remove(idx)
            self.thumbnail_frames[idx].configure(border_width=0)
        else:
            self.selected_indices.append(idx)
            self.thumbnail_frames[idx].configure(border_width=2, border_color="#3498db")
        
        if self.selected_indices:
            self.btn_next.configure(state="normal")
        else:
            self.btn_next.configure(state="disabled")

    def open_rearrange_window(self):
        if not self.selected_indices:
            return
        
        selected_data = [self.frames_data[i] for i in self.selected_indices]
        FrameRearrangeWindow(self, selected_data, self.config_manager, self.last_dir)

    def __del__(self):
        # Limpar temp dir quando o objeto for destruído
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
