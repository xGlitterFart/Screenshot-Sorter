import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

class IntroductionPage:
    def __init__(self, root, on_continue):
        self.root = root
        self.on_continue = on_continue

        self.frame = tk.Frame(root, padx=20, pady=20)
        self.frame.pack(fill="both", expand=True)

        intro_text = (
            "Welcome to the Screenshot Sorter!\n\n"
            "This tool helps you organize your Final Fantasy XIV screenshots by:\n"
            "- Sorting photos by date, location, and character name.\n"
            "- Archiving copies to keep backups.\n\n"
            "This idea came while browsing through my pictures just to find that one specific one.\n"
            "This is sorta like a little helper for the first party plugin from Dalamud 'Sightseeingaway',\nwith the following setting: Timestamp (Readable Format), Map/Zone Name and Character Name.\n\n"
            "Please note, I have zero knowledge about coding and I asked Chatgpt for help.\n(Yes, I am that lazy).\nSo please always make a backup of your photos before using the Screenshot Sorter. I take no responsibility for loss of photos or anything else.\n\n"
            "Click 'Continue' to start."
        )

        self.label = tk.Label(self.frame, text=intro_text, justify="left", font=("Arial", 12))
        self.label.pack(pady=(0,20))

        self.continue_btn = tk.Button(self.frame, text="Continue", command=self.proceed)
        self.continue_btn.pack()

    def proceed(self):
        self.frame.destroy()
        self.on_continue()


class ScreenshotSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot Sorter")

        self.main_frame = tk.Frame(root, padx=15, pady=15)
        self.main_frame.pack(fill="both", expand=True)

        # Warning Label - bold, red, centered over 3 columns
        self.warning_label = tk.Label(
            self.main_frame,
            text="⚠️ Please backup your photos before moving them! ⚠️",
            fg="red",
            font=("Arial", 12, "bold"),
        )
        self.warning_label.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0,10))

        # Options: 1 or 2
        self.option_var = tk.StringVar(value="1")
        self.opt1_rb = tk.Radiobutton(self.main_frame, text="Option 1: Move & archive in source folder", variable=self.option_var, value="1", command=self.toggle_destination)
        self.opt2_rb = tk.Radiobutton(self.main_frame, text="Option 2: Copy to destination folder without changing source", variable=self.option_var, value="2", command=self.toggle_destination)
        self.opt1_rb.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0,5))
        self.opt2_rb.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0,10))

        # Source Folder
        tk.Label(self.main_frame, text="Source Folder:").grid(row=3, column=0, sticky="w")
        self.src_entry = tk.Entry(self.main_frame, width=45)
        self.src_entry.grid(row=3, column=1, sticky="ew")
        self.src_browse_btn = tk.Button(self.main_frame, text="Browse", command=self.browse_source)
        self.src_browse_btn.grid(row=3, column=2, sticky="ew", padx=(5,0))

        # Destination Folder (for option 2)
        tk.Label(self.main_frame, text="Destination Folder:").grid(row=4, column=0, sticky="w")
        self.dest_entry = tk.Entry(self.main_frame, width=45, state="disabled")
        self.dest_entry.grid(row=4, column=1, sticky="ew")
        self.dest_browse_btn = tk.Button(self.main_frame, text="Browse", command=self.browse_destination, state="disabled")
        self.dest_browse_btn.grid(row=4, column=2, sticky="ew", padx=(5,0))

        # Start Button
        self.start_btn = tk.Button(self.main_frame, text="Start", command=self.start_sorting)
        self.start_btn.grid(row=5, column=0, columnspan=3, pady=(15,0), sticky="ew")

        # Make columns resize nicely
        self.main_frame.grid_columnconfigure(1, weight=1)

    def toggle_destination(self):
        if self.option_var.get() == "2":
            self.dest_entry.config(state="normal")
            self.dest_browse_btn.config(state="normal")
        else:
            self.dest_entry.config(state="disabled")
            self.dest_browse_btn.config(state="disabled")
            self.dest_entry.delete(0, tk.END)

    def browse_source(self):
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, folder)

    def browse_destination(self):
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, folder)

    def start_sorting(self):
        option = self.option_var.get()
        source_folder = self.src_entry.get()
        dest_folder = self.dest_entry.get() if option == "2" else None

        if not source_folder or not os.path.isdir(source_folder):
            messagebox.showerror("Error", "Please select a valid Source Folder.")
            return
        if option == "2" and (not dest_folder or not os.path.isdir(dest_folder)):
            messagebox.showerror("Error", "Please select a valid Destination Folder.")
            return

        try:
            if option == "1":
                self.sort_and_archive_in_source(source_folder)
            else:
                self.copy_to_destination(dest_folder, source_folder)
            messagebox.showinfo("Success", "Sorting completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")

    def sort_and_archive_in_source(self, source_folder):
        files = [f for f in os.listdir(source_folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if not files:
            raise Exception("No image files found in source folder.")

        # Get date from first file (assumes format YYYY-MM-DD_...)
        date_part = files[0].split("_")[0]
        date_folder_name = "-".join(date_part.split("-")[::-1])  # Convert to DD-MM-YYYY

        main_date_folder = os.path.join(source_folder, date_folder_name)
        os.makedirs(main_date_folder, exist_ok=True)

        archive_folder = os.path.join(source_folder, "Archive")
        os.makedirs(archive_folder, exist_ok=True)

        for file in files:
            full_src_path = os.path.join(source_folder, file)
            try:
                parts = file.split("_", 1)[1]  # after first "_"
                name_parts = parts.split("-")
                location = name_parts[3]
                player_name_with_ext = "-".join(name_parts[4:])
                player_name = os.path.splitext(player_name_with_ext)[0]

                location_folder = os.path.join(main_date_folder, location)
                player_folder = os.path.join(location_folder, player_name)
                os.makedirs(player_folder, exist_ok=True)

                dest_path = os.path.join(player_folder, file)

                shutil.move(full_src_path, dest_path)
                shutil.copy2(dest_path, os.path.join(archive_folder, file))
            except Exception as e:
                print(f"Skipping file {file} due to parsing error: {e}")

    def copy_to_destination(self, dest_folder, source_folder):
        files = [f for f in os.listdir(source_folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if not files:
            raise Exception("No image files found in source folder.")

        for file in files:
            full_src_path = os.path.join(source_folder, file)
            full_dest_path = os.path.join(dest_folder, file)
            shutil.copy2(full_src_path, full_dest_path)


def main():
    root = tk.Tk()
    root.title("Screenshot Sorter")
    root.geometry("1025x600")

    def start_main_app():
        ScreenshotSorterApp(root)

    IntroductionPage(root, on_continue=start_main_app)
    root.mainloop()

if __name__ == "__main__":
    main()
