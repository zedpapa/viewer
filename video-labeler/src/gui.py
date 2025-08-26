import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from PIL import Image, ImageTk
from src.database import Database
from src.video_processing import get_video_info

# Helper class for the scrollable view
class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        # ... (init is the same)
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title("Video Labeler")
        self.parent.geometry("1200x800")
        self.pack(fill="both", expand=True)
        self.db = Database('video_library.db')
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.master_video_list = []
        self.displayed_videos = []
        self.current_video_info = None
        self.thumbnail_images = []
        self.video_item_widgets = {}
        self.sort_criterion = tk.StringVar(value="Filename")
        self.sort_order_asc = tk.BooleanVar(value=True)
        self.create_menu()
        self.create_main_layout()
        self.update_filter_section()

    def on_closing(self):
        self.db.close()
        self.parent.destroy()

    def create_menu(self):
        # ... (same as before)
        self.menu_bar = tk.Menu(self.parent)
        self.parent.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Folder", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

    def create_main_layout(self):
        # ... (same as before)
        paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned_window.pack(fill=tk.BOTH, expand=True)
        self.sidebar = tk.Frame(paned_window, width=350, relief=tk.SUNKEN, borderwidth=2)
        paned_window.add(self.sidebar, stretch="never")
        self.create_sidebar_layout()
        main_content = tk.Frame(paned_window, relief=tk.SUNKEN, borderwidth=2)
        paned_window.add(main_content)
        sort_frame = tk.Frame(main_content)
        sort_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(sort_frame, text="Sort by:").pack(side='left', padx=(0, 5))
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_criterion, values=["Filename", "Size", "Duration"], state="readonly")
        sort_combo.pack(side='left', padx=5)
        sort_combo.bind("<<ComboboxSelected>>", self.sort_and_update_display)
        self.sort_order_button = tk.Button(sort_frame, text="Ascending", command=self.toggle_sort_order)
        self.sort_order_button.pack(side='left', padx=5)
        self.scrollable_view = ScrollableFrame(main_content)
        self.scrollable_view.pack(fill="both", expand=True, padx=5, pady=5)
        self.video_display_frame = self.scrollable_view.scrollable_frame

    def create_sidebar_layout(self):
        # ... (same as before)
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        filter_frame = tk.Frame(self.sidebar)
        filter_frame.pack(pady=10, padx=10, fill=tk.X, anchor='n')
        tk.Label(filter_frame, text="Filter by Label", font=("Arial", 10, "bold")).pack(anchor="w")
        self.filter_labels_frame = tk.Frame(filter_frame)
        self.filter_labels_frame.pack(fill=tk.X, expand=True)
        tk.Button(filter_frame, text="Clear Filter", command=self.clear_filter).pack(pady=5)
        tk.Label(self.sidebar, text="Selected Video:", font=("Arial", 10, "bold")).pack(pady=(10,0), padx=10, anchor="w")
        self.selected_video_label = tk.Label(self.sidebar, text="None", wraplength=330, justify=tk.LEFT)
        self.selected_video_label.pack(pady=(0,10), padx=10, anchor="w")
        tk.Label(self.sidebar, text="Labels:", font=("Arial", 10, "bold")).pack(pady=10, padx=10, anchor="w")
        self.labels_frame = tk.Frame(self.sidebar)
        self.labels_frame.pack(fill=tk.X, expand=False, padx=10)
        add_frame = tk.Frame(self.sidebar, pady=10)
        add_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10)
        tk.Label(add_frame, text="New Label", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0,5))
        tk.Label(add_frame, text="Name:").grid(row=1, column=0, sticky='w')
        self.new_label_name_entry = tk.Entry(add_frame)
        self.new_label_name_entry.grid(row=1, column=1, sticky='ew', pady=2)
        tk.Label(add_frame, text="Value:").grid(row=2, column=0, sticky='w')
        self.new_label_value_entry = tk.Entry(add_frame)
        self.new_label_value_entry.grid(row=2, column=1, sticky='ew', pady=2)
        add_button = tk.Button(add_frame, text="Add Label", command=self.add_label)
        add_button.grid(row=3, column=0, columnspan=2, pady=(10,0))
        add_frame.grid_columnconfigure(1, weight=1)

    def create_video_item_widget(self, video_info, photo):
        item_frame = tk.Frame(self.video_display_frame, borderwidth=2, relief="groove")

        thumb_label = tk.Label(item_frame, image=photo)
        thumb_label.pack(side="left", padx=5, pady=5)

        info_frame = tk.Frame(item_frame)
        info_frame.pack(side="left", fill="x", expand=True, padx=5)

        tk.Label(info_frame, text=video_info['filename'], font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(info_frame, text=f"Duration: {video_info['duration_str']}").pack(anchor="w")
        tk.Label(info_frame, text=f"Size: {video_info['filesize_str']}").pack(anchor="w")

        # Bind click events
        item_frame.bind("<Button-1>", lambda e, vi=video_info: self.on_video_select(vi))
        item_frame.bind("<Button-3>", lambda e, vi=video_info: self.show_context_menu(e, vi))
        for widget in info_frame.winfo_children() + [thumb_label]:
            widget.bind("<Button-1>", lambda e, vi=video_info: self.on_video_select(vi))
            widget.bind("<Button-3>", lambda e, vi=video_info: self.show_context_menu(e, vi))

        return item_frame

    def show_context_menu(self, event, video_info):
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Rename", command=lambda: self.prompt_for_rename(video_info))
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def prompt_for_rename(self, video_info):
        old_name_no_ext, ext = os.path.splitext(video_info['filename'])
        new_name_no_ext = simpledialog.askstring(
            "Rename Video", "Enter new name (without extension):",
            initialvalue=old_name_no_ext
        )

        if not new_name_no_ext or new_name_no_ext == old_name_no_ext:
            return # User cancelled or didn't change the name

        # Basic validation for invalid filename characters
        invalid_chars = '/\\?%*:|"<>'
        if any(c in invalid_chars for c in new_name_no_ext):
            messagebox.showerror("Invalid Name", f"The name contains invalid characters.\nAvoid: {invalid_chars}")
            return

        self.rename_video(video_info, new_name_no_ext + ext)

    def rename_video(self, video_info, new_filename):
        old_filepath = video_info['filepath']
        dir_path = os.path.dirname(old_filepath)
        new_filepath = os.path.join(dir_path, new_filename)

        if os.path.exists(new_filepath):
            messagebox.showerror("Rename Failed", f"A file named '{new_filename}' already exists in this directory.")
            return

        try:
            # 1. Rename on disk
            os.rename(old_filepath, new_filepath)

            # 2. Update database
            self.db.update_video_filepath(old_filepath, new_filepath)

            # 3. Update in-memory lists (master and displayed)
            # This is tricky because video_info is a dictionary, which is mutable
            # We need to update the dictionary in place to affect all references to it
            video_info['filepath'] = new_filepath
            video_info['filename'] = new_filename

            # 4. Refresh UI
            self.sort_and_update_display()
            messagebox.showinfo("Success", "Video renamed successfully.")

        except OSError as e:
            messagebox.showerror("Rename Failed", f"An error occurred: {e}")
            # If the rename failed, we don't need to do anything else.

    # --- All other methods remain the same ---
    def sort_and_update_display(self, event=None):
        criterion = self.sort_criterion.get()
        reverse = not self.sort_order_asc.get()
        key_map = {
            "Filename": lambda v: v['filename'].lower(),
            "Size": lambda v: v['filesize_bytes'],
            "Duration": lambda v: v['duration_seconds']
        }
        sorted_list = sorted(self.displayed_videos, key=key_map[criterion], reverse=reverse)
        self.update_video_list(sorted_list)

    def toggle_sort_order(self):
        new_value = not self.sort_order_asc.get()
        self.sort_order_asc.set(new_value)
        self.sort_order_button.config(text="Ascending" if new_value else "Descending")
        self.sort_and_update_display()

    def update_video_list(self, videos_to_display):
        for widget in self.video_display_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images = []
        self.displayed_videos = videos_to_display
        self.video_item_widgets = {}
        self.current_video_info = None
        self.selected_video_label.config(text="None")
        self.update_label_display()
        for video_info in self.displayed_videos:
            img_path = video_info.get("thumbnail_path")
            img = Image.open(img_path) if img_path and os.path.exists(img_path) else Image.new("RGB", (128, 72), "black")
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_images.append(photo)
            video_item = self.create_video_item_widget(video_info, photo)
            video_item.pack(fill='x', padx=5, pady=5)
            self.video_item_widgets[video_info['filepath']] = video_item

    def on_video_select(self, video_info):
        if self.current_video_info and self.current_video_info['filepath'] in self.video_item_widgets:
            prev_widget = self.video_item_widgets.get(self.current_video_info['filepath'])
            if prev_widget:
                prev_widget.config(bg=self.parent.cget('bg'))
        self.current_video_info = video_info
        self.selected_video_label.config(text=self.current_video_info['filename'])
        if self.current_video_info['filepath'] in self.video_item_widgets:
            new_widget = self.video_item_widgets.get(self.current_video_info['filepath'])
            if new_widget:
                new_widget.config(bg="lightblue")
        self.update_label_display()

    def scan_for_videos(self, folder_path):
        self.master_video_list = []
        video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv')
        print("Scanning for videos and extracting metadata...")
        filepaths = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(video_extensions):
                    filepaths.append(os.path.join(root, file))
        total_videos = len(filepaths)
        for i, filepath in enumerate(filepaths):
            self.parent.title(f"Video Labeler - Processing {i+1}/{total_videos}")
            video_info = get_video_info(filepath)
            if video_info:
                self.master_video_list.append(video_info)
            self.parent.update_idletasks()
        self.parent.title("Video Labeler")
        print(f"Found and processed {len(self.master_video_list)} videos.")
        self.sort_and_update_display()

    def update_filter_section(self):
        for widget in self.filter_labels_frame.winfo_children():
            widget.destroy()
        all_labels = self.db.get_all_unique_labels()
        for label_name in all_labels:
            btn = tk.Button(self.filter_labels_frame, text=label_name, command=lambda ln=label_name: self.filter_by_label(ln))
            btn.pack(fill=tk.X, pady=2)

    def filter_by_label(self, label_name):
        filtered_paths = self.db.get_videos_for_label_name(label_name)
        videos_to_display = [v for v in self.master_video_list if v['filepath'] in filtered_paths]
        self.update_video_list(videos_to_display)
        self.sort_and_update_display()

    def clear_filter(self):
        self.update_video_list(self.master_video_list)
        self.sort_and_update_display()

    def update_label_display(self):
        for widget in self.labels_frame.winfo_children():
            widget.destroy()
        if not self.current_video_info:
            return
        video_id = self.db.get_or_create_video(self.current_video_info['filepath'])
        labels = self.db.get_labels_for_video(video_id)
        if not labels:
            tk.Label(self.labels_frame, text="No labels yet.").pack()
            return
        for i, (video_label_id, name, value) in enumerate(labels):
            label_text = f"{name}: {value}"
            tk.Label(self.labels_frame, text=label_text).grid(row=i, column=0, sticky='w')
            remove_button = tk.Button(self.labels_frame, text="Remove", command=lambda vli=video_label_id: self.remove_label(vli))
            remove_button.grid(row=i, column=1, sticky='e', padx=5)

    def add_label(self):
        if not self.current_video_info:
            messagebox.showwarning("No Video Selected", "Please select a video from the list first.")
            return
        label_name = self.new_label_name_entry.get().strip()
        label_value = self.new_label_value_entry.get().strip()
        if not label_name or not label_value:
            messagebox.showwarning("Input Error", "Both label name and value are required.")
            return
        video_id = self.db.get_or_create_video(self.current_video_info['filepath'])
        label_id = self.db.get_or_create_label(label_name)
        self.db.add_video_label(video_id, label_id, label_value)
        self.new_label_name_entry.delete(0, tk.END)
        self.new_label_value_entry.delete(0, tk.END)
        self.update_label_display()
        self.update_filter_section()

    def remove_label(self, video_label_id):
        self.db.remove_video_label(video_label_id)
        self.update_label_display()
        self.update_filter_section()

    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.scan_for_videos(folder_path)
