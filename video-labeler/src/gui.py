import tkinter as tk
from tkinter import filedialog, messagebox
import os
from src.database import Database

class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title("Video Labeler")
        self.parent.geometry("1000x700")
        self.pack(fill="both", expand=True)

        self.db = Database('video_library.db')
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.master_video_list = [] # All videos from the scanned folder
        self.displayed_videos = [] # The list of videos currently shown in the listbox
        self.current_video_filepath = None

        self.create_menu()
        self.create_main_layout()
        self.update_filter_section()

    def on_closing(self):
        self.db.close()
        self.parent.destroy()

    def create_menu(self):
        self.menu_bar = tk.Menu(self.parent)
        self.parent.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Folder", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

    def create_main_layout(self):
        paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned_window.pack(fill=tk.BOTH, expand=True)

        self.sidebar = tk.Frame(paned_window, width=300, relief=tk.SUNKEN, borderwidth=2)
        paned_window.add(self.sidebar, stretch="never")
        self.create_sidebar_layout()

        main_content = tk.Frame(paned_window, relief=tk.SUNKEN, borderwidth=2)
        paned_window.add(main_content)

        list_frame = tk.Frame(main_content)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.video_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.video_listbox.yview)
        self.video_listbox.bind('<<ListboxSelect>>', self.on_video_select)

    def create_sidebar_layout(self):
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        # --- Filter Section ---
        filter_frame = tk.Frame(self.sidebar)
        filter_frame.pack(pady=10, padx=10, fill=tk.X, anchor='n')
        tk.Label(filter_frame, text="Filter by Label", font=("Arial", 10, "bold")).pack(anchor="w")
        self.filter_labels_frame = tk.Frame(filter_frame)
        self.filter_labels_frame.pack(fill=tk.X, expand=True)
        tk.Button(filter_frame, text="Clear Filter", command=self.clear_filter).pack(pady=5)

        # --- Selected Video Section ---
        tk.Label(self.sidebar, text="Selected Video:", font=("Arial", 10, "bold")).pack(pady=(10,0), padx=10, anchor="w")
        self.selected_video_label = tk.Label(self.sidebar, text="None", wraplength=280, justify=tk.LEFT)
        self.selected_video_label.pack(pady=(0,10), padx=10, anchor="w")

        # --- Existing Labels Section ---
        tk.Label(self.sidebar, text="Labels:", font=("Arial", 10, "bold")).pack(pady=10, padx=10, anchor="w")
        self.labels_frame = tk.Frame(self.sidebar)
        self.labels_frame.pack(fill=tk.X, expand=False, padx=10)

        # --- Add New Label Section ---
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

    def update_filter_section(self):
        for widget in self.filter_labels_frame.winfo_children():
            widget.destroy()

        all_labels = self.db.get_all_unique_labels()
        for label_name in all_labels:
            btn = tk.Button(self.filter_labels_frame, text=label_name, command=lambda ln=label_name: self.filter_by_label(ln))
            btn.pack(fill=tk.X, pady=2)

    def filter_by_label(self, label_name):
        filtered_paths = self.db.get_videos_for_label_name(label_name)
        # We only want to show videos that are in the current master list
        videos_to_display = [path for path in filtered_paths if path in self.master_video_list]
        self.update_video_list(videos_to_display)

    def clear_filter(self):
        self.update_video_list(self.master_video_list)

    def on_video_select(self, event):
        selection_indices = self.video_listbox.curselection()
        if not selection_indices:
            return

        selected_index = selection_indices[0]
        self.current_video_filepath = self.displayed_videos[selected_index]

        filename = os.path.basename(self.current_video_filepath)
        self.selected_video_label.config(text=filename)
        self.update_label_display()

    def update_label_display(self):
        for widget in self.labels_frame.winfo_children():
            widget.destroy()

        if not self.current_video_filepath:
            return

        video_id = self.db.get_or_create_video(self.current_video_filepath)
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
        if not self.current_video_filepath:
            messagebox.showwarning("No Video Selected", "Please select a video from the list first.")
            return

        label_name = self.new_label_name_entry.get().strip()
        label_value = self.new_label_value_entry.get().strip()

        if not label_name or not label_value:
            messagebox.showwarning("Input Error", "Both label name and value are required.")
            return

        video_id = self.db.get_or_create_video(self.current_video_filepath)
        label_id = self.db.get_or_create_label(label_name)
        self.db.add_video_label(video_id, label_id, label_value)

        self.new_label_name_entry.delete(0, tk.END)
        self.new_label_value_entry.delete(0, tk.END)

        self.update_label_display()
        self.update_filter_section() # Refresh filters in case this was a new label name

    def remove_label(self, video_label_id):
        self.db.remove_video_label(video_label_id)
        self.update_label_display()
        self.update_filter_section() # A label might have been completely removed

    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.scan_for_videos(folder_path)

    def scan_for_videos(self, folder_path):
        self.master_video_list = []
        video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv')
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(video_extensions):
                    self.master_video_list.append(os.path.join(root, file))
        self.update_video_list(self.master_video_list)

    def update_video_list(self, videos_to_display):
        self.video_listbox.delete(0, tk.END)
        self.displayed_videos = videos_to_display

        # Reset selection
        self.current_video_filepath = None
        self.selected_video_label.config(text="None")
        self.update_label_display()

        for video_file in self.displayed_videos:
            filename = os.path.basename(video_file)
            self.video_listbox.insert(tk.END, filename)
