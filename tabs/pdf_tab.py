import os
import fitz
import zipfile
import io
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk

class RearrangeWindow(ctk.CTkToplevel):
    def __init__(self, parent, selected_pages, pdf_path):
        super().__init__(parent)
        self.title("Reordenar Páginas")
        self.geometry("600x700")
        self.parent = parent
        self.pdf_path = pdf_path
        self.selected_pages = selected_pages  # List of page indices
        
        self.label = ctk.CTkLabel(self, text="Organize as páginas e escolha o formato de saída", font=("Arial", 16, "bold"))
        self.label.pack(pady=15)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=550, height=450)
        self.scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.items = []
        self.render_items()
        
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=20, fill="x")
        
        ctk.CTkButton(button_frame, text="Gerar novo PDF", command=self.save_as_pdf, fg_color="#2ecc71", hover_color="#27ae60").pack(side="left", padx=20, expand=True)
        ctk.CTkButton(button_frame, text="Exportar PNGs (ZIP)", command=self.save_as_zip, fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=20, expand=True)

    def render_items(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.items = []
        
        try:
            doc = fitz.open(self.pdf_path)
            for i, page_idx in enumerate(self.selected_pages):
                frame = ctk.CTkFrame(self.scroll_frame)
                frame.pack(fill="x", pady=5, padx=5)
                
                # Thumbnail
                page = doc.load_page(page_idx)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(img)
                
                img_label = ctk.CTkLabel(frame, image=photo, text="")
                img_label.image = photo 
                img_label.pack(side="left", padx=10, pady=5)
                
                ctk.CTkLabel(frame, text=f"Página Original: {page_idx + 1}", font=("Arial", 12)).pack(side="left", padx=10)
                
                # Control buttons
                btn_frame = ctk.CTkFrame(frame)
                btn_frame.pack(side="right", padx=10)
                
                ctk.CTkButton(btn_frame, text="↑", width=40, command=lambda idx=i: self.move_up(idx)).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="↓", width=40, command=lambda idx=i: self.move_down(idx)).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="Remover", width=70, fg_color="#e74c3c", hover_color="#c0392b", command=lambda idx=i: self.remove_item(idx)).pack(side="left", padx=5)
                
            doc.close()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao renderizar páginas: {e}")

    def move_up(self, index):
        if index > 0:
            self.selected_pages[index], self.selected_pages[index-1] = self.selected_pages[index-1], self.selected_pages[index]
            self.render_items()

    def move_down(self, index):
        if index < len(self.selected_pages) - 1:
            self.selected_pages[index], self.selected_pages[index+1] = self.selected_pages[index+1], self.selected_pages[index]
            self.render_items()

    def remove_item(self, index):
        self.selected_pages.pop(index)
        self.render_items()
        if not self.selected_pages:
            self.destroy()

    def save_as_pdf(self):
        output_file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not output_file:
            return
        
        if os.path.exists(output_file):
            if not messagebox.askyesno("Arquivo existe", f"{output_file} já existe. Deseja sobrescrever?"):
                return
        
        try:
            doc = fitz.open(self.pdf_path)
            new_doc = fitz.open()
            for page_idx in self.selected_pages:
                new_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
            new_doc.save(output_file)
            new_doc.close()
            doc.close()
            messagebox.showinfo("Sucesso", f"Novo PDF criado com sucesso!\nSalvo em: {output_file}")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar PDF: {e}")

    def save_as_zip(self):
        output_file = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")])
        if not output_file:
            return

        if os.path.exists(output_file):
            if not messagebox.askyesno("Arquivo existe", f"{output_file} já existe. Deseja sobrescrever?"):
                return
        
        try:
            doc = fitz.open(self.pdf_path)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for i, page_idx in enumerate(self.selected_pages):
                    page = doc.load_page(page_idx)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("png")
                    zip_file.writestr(f"pagina_{i+1}_orig_{page_idx+1}.png", img_data)
            
            with open(output_file, "wb") as f:
                f.write(zip_buffer.getvalue())
            
            doc.close()
            messagebox.showinfo("Sucesso", f"Arquivo ZIP criado com sucesso!\nSalvo em: {output_file}")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar ZIP: {e}")


class ZoomModal(ctk.CTkToplevel):
    def __init__(self, parent, page_idx, pdf_path):
        super().__init__(parent)
        self.title(f"Afastamento - Página {page_idx + 1}")
        self.geometry("800x900")
        
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            max_w, max_h = 750, 800
            ratio = min(max_w / img.width, max_h / img.height)
            if ratio < 1:
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
                
            photo = ImageTk.PhotoImage(img)
            doc.close()
            
            self.scroll = ctk.CTkScrollableFrame(self)
            self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
            
            self.img_label = ctk.CTkLabel(self.scroll, image=photo, text="")
            self.img_label.image = photo
            self.img_label.pack(pady=10)
            
            ctk.CTkButton(self, text="Fechar", command=self.destroy).pack(pady=10)
            self.bind("<Escape>", lambda e: self.destroy())
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no zoom: {e}")
            self.destroy()


class PDFSplitTab(ctk.CTkFrame, TkinterDnD.DnDWrapper):
    def __init__(self, master):
        super().__init__(master)
        TkinterDnD.DnDWrapper.__init__(self)
        self.pdf_file_path = None
        self.selected_indices = []
        self.thumbnail_frames = {}

        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(top_frame, text="Carregar PDF", command=self.load_pdf_for_split).pack(side="left", padx=5)
        self.pdf_status_label = ctk.CTkLabel(top_frame, text="Nenhum arquivo selecionado")
        self.pdf_status_label.pack(side="left", padx=20)

        self.btn_next_pdf = ctk.CTkButton(top_frame, text="Próximo (Organizar) →", state="disabled", command=self.open_rearrange_window, fg_color="#f39c12", hover_color="#d35400")
        self.btn_next_pdf.pack(side="right", padx=5)

        self.pdf_scroll = ctk.CTkScrollableFrame(self, label_text="Selecione as páginas clicando nelas")
        self.pdf_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # DnD Support
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        # Manually load the PDF
        self.pdf_file_path = file_path
        self.selected_indices = []
        self.pdf_status_label.configure(text=os.path.basename(file_path))
        self.btn_next_pdf.configure(state="disabled")
        
        for widget in self.pdf_scroll.winfo_children():
            widget.destroy()
        self.thumbnail_frames = {}
        
        # Re-trigger load logic (mimic load_pdf_for_split but with specific path)
        try:
            import fitz
            from PIL import Image, ImageTk
            doc = fitz.open(file_path)
            cols = 4
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.15, 0.15))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(img)
                
                f = ctk.CTkFrame(self.pdf_scroll, width=130, height=180, border_width=0)
                f.grid(row=i // cols, column=i % cols, padx=10, pady=10)
                f.grid_propagate(False)
                
                l = ctk.CTkLabel(f, image=photo, text="")
                l.image = photo
                l.pack(expand=True, fill="both", padx=5, pady=5)
                
                ctk.CTkLabel(f, text=f"Pág {i+1}", font=("Arial", 10)).pack(pady=(0, 5))
                
                l.bind("<Button-1>", lambda e, idx=i: self.toggle_page(idx))
                f.bind("<Button-1>", lambda e, idx=i: self.toggle_page(idx))
                l.bind("<Double-Button-1>", lambda e, idx=i: self.show_page_zoom(idx))
                f.bind("<Double-Button-1>", lambda e, idx=i: self.show_page_zoom(idx))
                self.thumbnail_frames[i] = f
            doc.close()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir PDF: {e}")

    def load_pdf_for_split(self):
        file = filedialog.askopenfilename(filetypes=[("Arquivos PDF", "*.pdf")])
        if not file:
            return
        
        self.pdf_file_path = file
        self.selected_indices = []
        self.pdf_status_label.configure(text=os.path.basename(file))
        self.btn_next_pdf.configure(state="disabled")
        
        for widget in self.pdf_scroll.winfo_children():
            widget.destroy()
        self.thumbnail_frames = {}
        
        try:
            doc = fitz.open(file)
            cols = 4
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.15, 0.15))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(img)
                
                f = ctk.CTkFrame(self.pdf_scroll, width=130, height=180, border_width=0)
                f.grid(row=i // cols, column=i % cols, padx=10, pady=10)
                f.grid_propagate(False)
                
                l = ctk.CTkLabel(f, image=photo, text="")
                l.image = photo
                l.pack(expand=True, fill="both", padx=5, pady=5)
                
                ctk.CTkLabel(f, text=f"Pág {i+1}", font=("Arial", 10)).pack(pady=(0, 5))
                
                l.bind("<Button-1>", lambda e, idx=i: self.toggle_page(idx))
                f.bind("<Button-1>", lambda e, idx=i: self.toggle_page(idx))
                l.bind("<Double-Button-1>", lambda e, idx=i: self.show_page_zoom(idx))
                f.bind("<Double-Button-1>", lambda e, idx=i: self.show_page_zoom(idx))
                
                self.thumbnail_frames[i] = f
                
            doc.close()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir PDF: {e}")

    def toggle_page(self, idx):
        if idx in self.selected_indices:
            self.selected_indices.remove(idx)
            self.thumbnail_frames[idx].configure(border_width=0)
        else:
            self.selected_indices.append(idx)
            self.thumbnail_frames[idx].configure(border_width=2, border_color="#3498db")
        
        if self.selected_indices:
            self.btn_next_pdf.configure(state="normal")
        else:
            self.btn_next_pdf.configure(state="disabled")

    def open_rearrange_window(self):
        if not self.pdf_file_path or not self.selected_indices:
            return
        RearrangeWindow(self, list(self.selected_indices), self.pdf_file_path)

    def show_page_zoom(self, page_idx):
        if not self.pdf_file_path:
            return
        ZoomModal(self, page_idx, self.pdf_file_path)
