import cv2
import numpy as np
import mss
import tkinter as tk
from PIL import Image, ImageTk
import sys

# Monitors
MONITOR_INDEX = 1
MONITOR_LIVE = 2

CROP_REGION = {}

def start_crop():
    def start(event):
        global start_x, start_y
        start_x, start_y = event.x, event.y
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2)
        canvas.rect = rect

    def update(event):
        canvas.coords(canvas.rect, start_x, start_y, event.x, event.y)

    def finish(event):
        global CROP_REGION
        CROP_REGION["left"] = min(start_x, event.x)
        CROP_REGION["top"] = min(start_y, event.y)
        CROP_REGION["width"] = abs(event.x - start_x)
        CROP_REGION["height"] = abs(event.y - start_y)
        crop_root.destroy()
        start_overlay()

    global crop_root, canvas
    crop_root = tk.Tk()
    crop_root.title("Select Crop Area")

    with mss.mss() as sct:
        monitor = sct.monitors[MONITOR_INDEX]
        crop_root.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}")

    crop_root.attributes("-alpha", 0.3)
    crop_root.attributes("-topmost", True)

    canvas = tk.Canvas(crop_root, bg="gray", cursor="cross")
    canvas.pack(fill="both", expand=True)
    canvas.bind("<Button-1>", start)
    canvas.bind("<B1-Motion>", update)
    canvas.bind("<ButtonRelease-1>", finish)

    def check_keyboard_interrupt():
        try:
            crop_root.after(100, check_keyboard_interrupt)
        except KeyboardInterrupt:
            crop_root.destroy()
            sys.exit(0)

    crop_root.after(100, check_keyboard_interrupt)
    try:
        crop_root.mainloop()
    except KeyboardInterrupt:
        crop_root.destroy()
        sys.exit(0)

def start_overlay():
    def update_frame():
        try:
            with mss.mss() as sct:
                source_monitor = sct.monitors[MONITOR_INDEX]
                region = {
                    "top": source_monitor["top"] + CROP_REGION["top"],
                    "left": source_monitor["left"] + CROP_REGION["left"],
                    "width": CROP_REGION["width"],
                    "height": CROP_REGION["height"]
                }
                img = np.array(sct.grab(region))
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                img = Image.fromarray(img)
                img = img.resize((root.winfo_width(), root.winfo_height()))  # Resize to current window size
                imgtk = ImageTk.PhotoImage(image=img)

                label.imgtk = imgtk
                label.configure(image=imgtk)

            if not movable:  # Only update if not in movable mode
                root.after(30, update_frame)
        except KeyboardInterrupt:
            root.destroy()
            sys.exit(0)

    def toggle_movable(event=None):
        nonlocal movable
        movable = not movable
        if movable:
            root.configure(cursor="fleur")
            label.pack_forget()  # Hide live feed
            exit_btn.place(x=root.winfo_width()-25, y=5)
        else:
            root.configure(cursor="arrow")
            exit_btn.place_forget()
            label.pack()  # Show live feed
            update_frame()  # Resume live feed

    def start_move(event):
        if movable:
            root.x_offset = event.x
            root.y_offset = event.y

    def do_move(event):
        if movable:
            x = root.winfo_pointerx() - root.x_offset
            y = root.winfo_pointery() - root.y_offset
            root.geometry(f"+{x}+{y}")

    def resize_percent(event):
        if movable:
            width = root.winfo_width()
            height = root.winfo_height()
            if event.keysym == "Up":
                width = int(width * 1.1)
                height = int(height * 1.1)
            elif event.keysym == "Down":
                width = int(width * 0.9)
                height = int(height * 0.9)
            width = max(50, width)
            height = max(50, height)
            root.geometry(f"{width}x{height}")

    global root, label
    movable = False 
    root = tk.Tk()
    root.title("Live Overlay")
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.wm_attributes("-transparentcolor", "black")

    with mss.mss() as sct:
        live_monitor = sct.monitors[MONITOR_LIVE]
        root.geometry(f"{CROP_REGION['width']}x{CROP_REGION['height']}+{live_monitor['left']}+{live_monitor['top']}")

    label = tk.Label(root, bg="black")
    label.pack()

    exit_btn = tk.Button(root, text="X", command=root.destroy, bg="red", fg="white", bd=0, font=("Arial", 12, "bold"))
    exit_btn.place_forget()

    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)

    # F4 toggles movable mode
    root.bind("<F4>", toggle_movable)

    # Arrow keys resize by percentage
    root.bind("<Up>", resize_percent)
    root.bind("<Down>", resize_percent)

    def check_interrupt():
        try:
            root.after(100, check_interrupt)
        except KeyboardInterrupt:
            root.destroy()
            sys.exit(0)

    root.after(100, check_interrupt)
    update_frame()
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()
        sys.exit(0)

start_crop()
