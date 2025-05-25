# Screenshot Sorter for Final Fantasy XIV

A simple tool to help organize your Final Fantasy XIV screenshots by date, location, and character name — with automatic backup archiving. Perfect if you want to quickly find that one specific screenshot without hunting through a messy folder.

---

## Features

- Sorts screenshots into folders by **date → location → character name**
- Creates an **Archive** folder with copies of all original screenshots as backup
- User-friendly GUI with options for moving or copying files
- Works best with screenshots named using the Dalamud plugin **Sightseeingaway** (`First party plugin from Dalamud`) format:  
  `Timestamp - Map/Zone Name - Character Name`

---

## How It Works

1. Select your **source folder** containing your screenshots.
2. Choose whether to move or copy the files to a new folder.
3. The program will create an Archive folder in your source directory to keep backups.
4. Screenshots will be sorted into a folder structure based on their filenames.

---

## Folder Structure

After running the tool, your screenshots will be organized like this:

```plaintext
(Your folder name)
│
├── Archive
│   ├── 2025-05-25_00-35-19.549-New Gridania-Char Name.jpg
│   ├── 2025-05-25_00-43-50.436-Central Shroud-Char Name.jpg
│   └── (all original screenshots copied here as backup)
│
├── 25-05-2025  (date folder, sorting by screenshot date)
│   ├── New Gridania  (location folder)
│   │   ├── Char Name (character name folder)
│   │   │   ├── 2025-05-25_00-35-19.549-New Gridania-Char Name.jpg
│   │   │   └── 2025-05-25_00-35-38.206-New Gridania-Char Name.jpg
│   ├── Central Shroud
│   │   └── Char Name
│   │       └── 2025-05-25_00-43-50.436-Central Shroud-Char Name.jpg
│   └── South Shroud
│       └── Char Name
│           └── 2025-05-25_00-44-14.717-South Shroud-Char Name.jpg
│
└── (any unsorted or unrecognized screenshots could stay here)
```
---

## Notes

⚠️ Always backup your photos before running the tool! ⚠️

The program copies files to an Archive folder, but better safe than sorry.

The tool expects screenshot filenames to follow this pattern:

YYYY-MM-DD_HH-MM-SS.milliseconds-Location-Character Name.ext

Tested on Windows with Python 3.x and can be packaged as a standalone .exe.

---

## How to Use

Download or clone this repository.

Run the Python script screenshot_sorter_gui.py with Python 3.

Or use the pre-built screenshot_sorter.exe if you prefer not to install Python.

Follow the GUI instructions.

---

## License

Feel free to use, modify, and share!  
_Disclaimer: Always backup your files before using this tool. The author is not responsible for any data loss._
