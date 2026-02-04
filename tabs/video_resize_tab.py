import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
import tempfile

class VideoResizeTab(ctk.CTkFrame, TkinterDnD.DnDWrapper):
    def __init__(self, master):
        super().__init__(master)
        TkinterDnD.DnDWrapper.__init__(self)
        self.input_file = ""
        self.video_width = 0
        self.video_height = 0
        self.temp_frame_path = ""
        self.current_scale = 1.0
        self.img_offset_x = 0
        self.img_offset_y = 0
        self.dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.resize_mode = None # "n", "s", "e", "w", "ne", "nw", "se", "sw" or None
        
        self.target_width_var = ctk.StringVar(value="1080")
        self.target_height_var = ctk.StringVar(value="1080")
        self.x_offset_var = ctk.StringVar(value="0")
        self.y_offset_var = ctk.StringVar(value="0")

        # Traces for automatic updates
        self.target_width_var.trace_add("write", lambda *args: self.update_preview())
        self.target_height_var.trace_add("write", lambda *args: self.update_preview())
        self.x_offset_var.trace_add("write", lambda *args: self.update_preview())
        self.y_offset_var.trace_add("write", lambda *args: self.update_preview())

        # Left side: Controls
        self.controls_frame = ctk.CTkFrame(self, width=250)
        self.controls_frame.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.controls_frame, text="Configurações de Corte", font=("Arial", 16, "bold")).pack(pady=10)

        ctk.CTkButton(self.controls_frame, text="Selecionar Vídeo", command=self.load_video).pack(pady=10, padx=10, fill="x")

        # Resolution inputs
        res_frame = ctk.CTkFrame(self.controls_frame)
        res_frame.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(res_frame, text="Largura Final:").grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkEntry(res_frame, textvariable=self.target_width_var, width=80).grid(row=0, column=1, pady=2)
        
        ctk.CTkLabel(res_frame, text="Altura Final:").grid(row=1, column=0, sticky="w", padx=5)
        ctk.CTkEntry(res_frame, textvariable=self.target_height_var, width=80).grid(row=1, column=1, pady=2)

        # Offset inputs
        off_frame = ctk.CTkFrame(self.controls_frame)
        off_frame.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(off_frame, text="X (Horizontal):").grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkEntry(off_frame, textvariable=self.x_offset_var, width=80).grid(row=0, column=1, pady=2)
        
        ctk.CTkLabel(off_frame, text="Y (Vertical):").grid(row=1, column=0, sticky="w", padx=5)
        ctk.CTkEntry(off_frame, textvariable=self.y_offset_var, width=80).grid(row=1, column=1, pady=2)

        ctk.CTkButton(self.controls_frame, text="Centralizar", command=self.center_crop).pack(pady=5, padx=10, fill="x")
        
        self.info_label = ctk.CTkLabel(self.controls_frame, text="Resolução: -", text_color="gray")
        self.info_label.pack(pady=10)

        ctk.CTkButton(self.controls_frame, text="Cortar e Salvar", fg_color="green", hover_color="darkgreen", command=self.process_video).pack(side="bottom", pady=20, padx=10, fill="x")

        # Right side: Visualization
        self.viz_frame = ctk.CTkFrame(self)
        self.viz_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.canvas = Canvas(self.viz_frame, bg="#2b2b2b", highlightthickness=0, cursor="fleur")
        self.canvas.pack(fill="both", expand=True)
        self.canvas_image = None
        self.preview_image = None
        self.crop_rect_id = None

        # DnD Support
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

        # Mouse Interaction Bindings
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<Motion>", self.update_cursor)

    def update_cursor(self, event):
        if not self.input_file or self.dragging: return
        mode = self.get_interaction_mode(event.x, event.y)
        cursor_map = {
            "n": "top_side", "s": "bottom_side", "e": "right_side", "w": "left_side",
            "nw": "top_left_corner", "ne": "top_right_corner", "sw": "bottom_left_corner", "se": "bottom_right_corner",
            "move": "fleur", None: "arrow"
        }
        self.canvas.configure(cursor=cursor_map.get(mode, "arrow"))

    def get_interaction_mode(self, mouse_x, mouse_y):
        try:
            cx = (mouse_x - self.img_offset_x) / self.current_scale
            cy = (mouse_y - self.img_offset_y) / self.current_scale
            
            tw = int(self.target_width_var.get())
            th = int(self.target_height_var.get())
            tx = int(self.x_offset_var.get())
            ty = int(self.y_offset_var.get())
            
            margin = 15 / self.current_scale # Interaction handle size
            
            # Corner detection
            is_n = abs(cy - ty) < margin
            is_s = abs(cy - (ty + th)) < margin
            is_w = abs(cx - tx) < margin
            is_e = abs(cx - (tx + tw)) < margin
            
            if is_n and is_w: return "nw"
            if is_n and is_e: return "ne"
            if is_s and is_w: return "sw"
            if is_s and is_e: return "se"
            if is_n: return "n"
            if is_s: return "s"
            if is_w: return "w"
            if is_e: return "e"
            
            # Inside detection for move
            if tx < cx < tx + tw and ty < cy < ty + th:
                return "move"
                
            return None
        except ValueError:
            return None

    def start_drag(self, event):
        if not self.input_file: return
        mode = self.get_interaction_mode(event.x, event.y)
        if mode:
            self.dragging = True
            self.resize_mode = mode if mode != "move" else None
            self.drag_start_mouse_x = event.x
            self.drag_start_mouse_y = event.y
            try:
                self.drag_start_tx = int(self.x_offset_var.get())
                self.drag_start_ty = int(self.y_offset_var.get())
                self.drag_start_tw = int(self.target_width_var.get())
                self.drag_start_th = int(self.target_height_var.get())
            except ValueError:
                self.dragging = False
        else:
            self.dragging = False

    def do_drag(self, event):
        if not self.dragging or not self.input_file: return
        
        dx = (event.x - self.drag_start_mouse_x) / self.current_scale
        dy = (event.y - self.drag_start_mouse_y) / self.current_scale
        
        new_tx, new_ty = self.drag_start_tx, self.drag_start_ty
        new_tw, new_th = self.drag_start_tw, self.drag_start_th
        
        if self.resize_mode:
            # Resizing logic
            if "n" in self.resize_mode:
                dy = min(dy, self.drag_start_th - 10) # Minimum height 10
                new_ty = max(0, self.drag_start_ty + int(dy))
                new_th = self.drag_start_th - (new_ty - self.drag_start_ty)
            if "s" in self.resize_mode:
                new_th = max(10, min(int(self.drag_start_th + dy), self.video_height - self.drag_start_ty))
            if "w" in self.resize_mode:
                dx = min(dx, self.drag_start_tw - 10) # Minimum width 10
                new_tx = max(0, self.drag_start_tx + int(dx))
                new_tw = self.drag_start_tw - (new_tx - self.drag_start_tx)
            if "e" in self.resize_mode:
                new_tw = max(10, min(int(self.drag_start_tw + dx), self.video_width - self.drag_start_tx))
        else:
            # Moving logic
            new_tx = max(0, min(int(self.drag_start_tx + dx), self.video_width - self.drag_start_tw))
            new_ty = max(0, min(int(self.drag_start_ty + dy), self.video_height - self.drag_start_th))
            
        self.x_offset_var.set(str(new_tx))
        self.y_offset_var.set(str(new_ty))
        self.target_width_var.set(str(new_tw))
        self.target_height_var.set(str(new_th))

    def stop_drag(self, event):
        self.dragging = False
        self.resize_mode = None
        self.update_cursor(event)

    def handle_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        self.input_file = file_path
        self.get_video_info()
        self.extract_frame()
        self.center_crop()
        self.update_preview()

    def load_video(self):
        file = filedialog.askopenfilename(filetypes=[("Vídeos", "*.mp4 *.mkv *.mov *.avi"), ("Todos os arquivos", "*.*")])
        if not file:
            return
        
        self.input_file = file
        self.get_video_info()
        self.extract_frame()
        self.center_crop()
        self.update_preview()

    def get_video_info(self):
        try:
            cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", self.input_file]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            w, h = map(int, result.stdout.strip().split('x'))
            self.video_width = w
            self.video_height = h
            self.info_label.configure(text=f"Resolução: {w}x{h}")
            
            # Initial crop area: full video resolution
            self.target_width_var.set(str(w))
            self.target_height_var.set(str(h))
            self.x_offset_var.set("0")
            self.y_offset_var.set("0")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler info do vídeo: {e}")

    def extract_frame(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            self.temp_frame_path = tmp.name
        
        try:
            # Extract frame at 1 second mark
            cmd = ["ffmpeg", "-y", "-ss", "00:00:01", "-i", self.input_file, "-frames:v", "1", "-q:v", "2", self.temp_frame_path]
            # Try 0 seconds if 1 second fails (short videos)
            subprocess.run(cmd, capture_output=True, check=False)
            if not os.path.exists(self.temp_frame_path) or os.path.getsize(self.temp_frame_path) == 0:
                 cmd = ["ffmpeg", "-y", "-i", self.input_file, "-frames:v", "1", "-q:v", "2", self.temp_frame_path]
                 subprocess.run(cmd, capture_output=True, check=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao extrair frame: {e}")

    def update_preview(self):
        if not self.temp_frame_path or not os.path.exists(self.temp_frame_path):
            return

        try:
            img = Image.open(self.temp_frame_path)
            
            # Canvas size
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            
            if canvas_w <= 1 or canvas_h <= 1: # Avoid zero division
                self.after(200, self.update_preview)
                return

            # Main image scaling to fit canvas
            img_w, img_h = img.size
            self.current_scale = min(canvas_w / img_w, canvas_h / img_h) * 0.9
            new_w, new_h = int(img_w * self.current_scale), int(img_h * self.current_scale)
            
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(img_resized)
            
            self.canvas.delete("all")
            self.img_offset_x = (canvas_w - new_w) // 2
            self.img_offset_y = (canvas_h - new_h) // 2
            self.canvas.create_image(self.img_offset_x, self.img_offset_y, anchor="nw", image=self.preview_image)
            
            # Draw Crop Rectangle
            try:
                tw_str = self.target_width_var.get()
                th_str = self.target_height_var.get()
                tx_str = self.x_offset_var.get()
                ty_str = self.y_offset_var.get()
                
                if not all([tw_str, th_str, tx_str, ty_str]): return

                tw = int(tw_str)
                th = int(th_str)
                tx = int(tx_str)
                ty = int(ty_str)
                
                # Scale crop values to canvas coordinates
                cw = tw * self.current_scale
                ch = th * self.current_scale
                cx = self.img_offset_x + tx * self.current_scale
                cy = self.img_offset_y + ty * self.current_scale
                
                self.canvas.create_rectangle(cx, cy, cx + cw, cy + ch, outline="red", width=2, dash=(4, 4))
                self.canvas.create_text(cx + 5, cy + 5, text="Área de Corte", fill="red", anchor="nw")
            except ValueError:
                pass # Ignore invalid numeric inputs during typing
                
        except Exception as e:
            # Silent fail for transient typing errors
            pass

    def center_crop(self):
        if self.video_width == 0: return
        try:
            tw = int(self.target_width_var.get())
            th = int(self.target_height_var.get())
            
            x = (self.video_width - tw) // 2
            y = (self.video_height - th) // 2
            
            self.x_offset_var.set(str(max(0, x)))
            self.y_offset_var.set(str(max(0, y)))
            # update_preview will be called via trace
        except ValueError:
            pass

    def process_video(self):
        if not self.input_file:
            messagebox.showerror("Erro", "Selecione um vídeo primeiro.")
            return

        try:
            tw = int(self.target_width_var.get())
            th = int(self.target_height_var.get())
            tx = int(self.x_offset_var.get())
            ty = int(self.y_offset_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Valores de resolução ou offset inválidos.")
            return

        if tw + tx > self.video_width or th + ty > self.video_height:
             if not messagebox.askyesno("Aviso", "A área de corte excede as dimensões do vídeo. Deseja continuar?"):
                 return

        output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if not output_file:
            return

        if os.path.exists(output_file):
            if not messagebox.askyesno("Arquivo existe", f"{output_file} já existe. Deseja sobrescrever?"):
                return

        # FFmpeg crop=w:h:x:y
        crop_filter = f"crop={tw}:{th}:{tx}:{ty}"
        cmd = ["ffmpeg", "-y", "-i", self.input_file, "-vf", crop_filter, "-c:v", "libx264", "-crf", "18", "-c:a", "copy", output_file]

        try:
            subprocess.run(cmd, check=True)
            messagebox.showinfo("Sucesso", f"Vídeo cortado com sucesso!\nSalvo em: {output_file}")
        except subprocess.CalledProcessError:
            messagebox.showerror("Erro", "Falha ao processar o vídeo.")

    def __del__(self):
        if self.temp_frame_path and os.path.exists(self.temp_frame_path):
            try:
                os.remove(self.temp_frame_path)
            except:
                pass
