import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tabs.video_tabs import VideoSplitTab, VideoJoinTab, VideoConvertTab
from tabs.pdf_tab import PDFSplitTab
from tabs.video_to_images_tab import VideoToImagesTab
from tabs.video_resize_tab import VideoResizeTab

class FFmpegGUI(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title("🎬 FFmpeg Toolkit")
        self.geometry("750x550")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Initialize tabs as frames
        self.split_tab = self.tabview.add("Dividir Vídeo")
        self.join_tab = self.tabview.add("Juntar Vídeos")
        self.convert_tab = self.tabview.add("Converter Formatos")
        self.movie_to_img_tab = self.tabview.add("Vídeo -> Imagens")
        self.resize_tab = self.tabview.add("Redimensionar (Crop)")
        self.pdf_tab = self.tabview.add("Dividir PDF")

        # Add functionality to tabs
        VideoSplitTab(self.split_tab).pack(fill="both", expand=True)
        VideoJoinTab(self.join_tab).pack(fill="both", expand=True)
        VideoConvertTab(self.convert_tab).pack(fill="both", expand=True)
        VideoToImagesTab(self.movie_to_img_tab).pack(fill="both", expand=True)
        VideoResizeTab(self.resize_tab).pack(fill="both", expand=True)
        PDFSplitTab(self.pdf_tab).pack(fill="both", expand=True)


if __name__ == "__main__":
    app = FFmpegGUI()
    app.mainloop()