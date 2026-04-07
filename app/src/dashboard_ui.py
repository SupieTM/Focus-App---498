import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from eyeTracker import eyeTracker
import threading
import time
import os
import json
from website_blocker import HostsBlocker

DATA_FILE = "app_data.json"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Focus App CS498")
        self.geometry("1100x700")

        # ---------- STATE ----------
        self.points = tk.IntVar(value=100)
        self.is_focusing = False
        self.focus_remaining = 0
        self.blocked_sites = []
        self.timer_enabled = tk.BooleanVar(value=True)  # Timer enabled by default
        #Implement website blocker
        self.blocker = HostsBlocker()
        # ---------- PRELOADED THEMES ----------``
        self.themes = {
            "light": {"bg_color": "#ecf0f1", "text_color": "#000000", "start_btn": "#2ecc71",
                      "stop_btn": "#e74c3c", "bg_image": None, "locked": False, "preview": None},
            "dark": {"bg_color": "#2c3e50", "text_color": "#ffffff", "start_btn": "#27ae60",
                     "stop_btn": "#c0392b", "bg_image": None, "locked": False, "preview": None},
            "ocean": {"bg_color": "#1abc9c", "text_color": "#ffffff", "start_btn": "#16a085",
                      "stop_btn": "#c0392b", "bg_image": "themes/ocean_theme.png", "locked": True, "preview": "themes/ocean_theme.png"},
            "forest": {"bg_color": "#2ecc71", "text_color": "#ffffff", "start_btn": "#27ae60",
                       "stop_btn": "#c0392b", "bg_image": "themes/forest_theme.png", "locked": True, "preview": "themes/forest_theme.png"},
            "sunset": {"bg_color": "#e67e22", "text_color": "#ffffff", "start_btn": "#d35400",
                       "stop_btn": "#c0392b", "bg_image": "themes/sunset_theme.png", "locked": True, "preview": "themes/sunset_theme.png"},
            "space": {"bg_color": "#34495e", "text_color": "#ecf0f1", "start_btn": "#2980b9",
                      "stop_btn": "#c0392b", "bg_image": "themes/space_theme.png", "locked": True, "preview": "themes/space_theme.png"},
        }
        self.current_theme = "light"
        self.bg_img_tk = None

        # ---------- LOAD DATA ----------
        self.load_data()

        # ---------- TABS ----------
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)
        self.main_tab = tk.Frame(notebook)
        self.rewards_tab = tk.Frame(notebook)
        self.settings_tab = tk.Frame(notebook)
        notebook.add(self.main_tab, text="Dashboard")
        notebook.add(self.rewards_tab, text="Rewards Shop")
        notebook.add(self.settings_tab, text="Settings")

        self.build_main_tab()
        self.build_rewards_tab()
        self.build_settings_tab()

        # Apply initial theme
        self.apply_theme(self.current_theme)

        # Bind window resize to adjust background
        self.bind("<Configure>", self.resize_bg)
        #Cleanup function
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    #Cleanup Function
    def on_closing(self):
        #Runs automatically when the user tries to close the app
        #Avoids sites being blocked when the app closes
        print("Closing application. Cleaning up system files...")
        if self.is_focusing:
            self.blocker.stop(self.blocked_sites)
        self.save_data()
        self.destroy()

    # ---------- DASHBOARD ----------
    def build_main_tab(self):
        frame = self.main_tab
        self.main_bg_label = tk.Label(frame)
        self.main_bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        tk.Label(frame, text="Focus Dashboard", font=("Arial", 22)).pack(pady=20)
        self.status_label = tk.Label(frame, text="Not Focusing", font=("Arial", 14))
        self.status_label.pack(pady=10)

        # Timer HH:MM:SS
        self.timer_frame = tk.LabelFrame(frame, text="Focus Timer", padx=10, pady=10)
        self.timer_frame.pack(pady=10)

        self.hour_entry = tk.Entry(self.timer_frame, width=3, justify="center")
        self.hour_entry.insert(0, "00")
        self.hour_entry.pack(side="left")
        tk.Label(self.timer_frame, text=":").pack(side="left")

        self.min_entry = tk.Entry(self.timer_frame, width=3, justify="center")
        self.min_entry.insert(0, "25")
        self.min_entry.pack(side="left")
        tk.Label(self.timer_frame, text=":").pack(side="left")

        self.sec_entry = tk.Entry(self.timer_frame, width=3, justify="center")
        self.sec_entry.insert(0, "00")
        self.sec_entry.pack(side="left")

        # Timer enable checkbox
        tk.Checkbutton(self.timer_frame, text="Enable Timer", variable=self.timer_enabled).pack(pady=5)

        # Site Blocker
        block_frame = tk.LabelFrame(frame, text="Sites to Block", padx=10, pady=10)
        block_frame.pack(pady=10)
        self.site_entry = tk.Entry(block_frame, width=40)
        self.site_entry.pack(side="left", padx=5)
        tk.Button(block_frame, text="Add", command=self.add_site).pack(side="left")
        tk.Button(block_frame, text="Remove", command=self.remove_site).pack(side="left")
        self.site_listbox = tk.Listbox(block_frame, height=4)
        self.site_listbox.pack(pady=5)
        for site in self.blocked_sites:
            self.site_listbox.insert(tk.END, site)

        # White Noise
        noise_frame = tk.LabelFrame(frame, text="White Noise Options", padx=10, pady=10)
        noise_frame.pack(pady=10)
        tk.Label(noise_frame, text="Volume:").pack()
        self.noise_slider = tk.Scale(noise_frame, from_=0, to=100, orient="horizontal")
        self.noise_slider.set(50)
        self.noise_slider.pack()
        self.noise_var = tk.BooleanVar()
        tk.Checkbutton(noise_frame, text="Enable White Noise", variable=self.noise_var).pack()

        # Buttons
        self.start_button = tk.Button(frame, text="Start Focus Session", font=("Arial", 14),
                                      command=self.start_focus)
        self.start_button.pack(pady=10)
        self.stop_button = tk.Button(frame, text="Stop Focus Session", font=("Arial", 14),
                                     command=self.stop_focus, state="disabled")
        self.stop_button.pack(pady=10)

    # ---------- SITE BLOCKER ----------
    def add_site(self):
        site = self.site_entry.get().strip()
        if site and site not in self.blocked_sites:
            self.blocked_sites.append(site)
            self.site_listbox.insert(tk.END, site)
            self.site_entry.delete(0, tk.END)
            self.save_data()

    def remove_site(self):
        selected = self.site_listbox.curselection()
        if selected:
            index = selected[0]
            site = self.site_listbox.get(index)
            self.blocked_sites.remove(site)
            self.site_listbox.delete(index)
            self.save_data()

    # ---------- FOCUS LOGIC ----------
    def start_focus(self):
        if self.is_focusing:
            return
        try:
            h = int(self.hour_entry.get())
            m = int(self.min_entry.get())
            s = int(self.sec_entry.get())
        except:
            h = m = s = 0
        self.focus_remaining = h*3600 + m*60 + s
        if self.focus_remaining == 0:
            self.focus_remaining = 1500

        self.is_focusing = True
        self.focus_start_time = time.time()
        self.status_label.config(text="Focusing...")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        # Disable timer editing
        for entry in [self.hour_entry, self.min_entry, self.sec_entry]:
            entry.config(state="disabled")

        if self.site_listbox.size() > 0:
            print("Site blocker started for:", self.blocked_sites)
            self.blocker.start(self.blocked_sites)
        self.site_entry.config(state="disabled")
        
        if self.noise_var.get():
            print("White noise started at volume:", self.noise_slider.get())
        print("Eye tracking started")
        print("Remote tracking started")

        # Threads
        threading.Thread(target=self.update_timer, daemon=True).start()
        threading.Thread(target=self.simulate_eye_tracking, daemon=True).start()

    def stop_focus(self):
        if not self.is_focusing:
            return
        self.is_focusing = False
        duration = int(time.time() - self.focus_start_time)
        earned_points = duration // 5
        self.points.set(self.points.get() + earned_points)
        self.status_label.config(text=f"Session Ended ({duration}s)")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        # Re-enable timer entries only if timer is enabled
        if self.timer_enabled.get():
            for entry in [self.hour_entry, self.min_entry, self.sec_entry]:
                entry.config(state="normal")
        self.show_report(duration, earned_points)
        self.save_data()
        self.update_rewards_buttons()
        self.blocker.stop(self.blocked_sites)

    # ---------- TIMER ----------
    def update_timer(self):
        while self.is_focusing and self.focus_remaining > 0:
            if self.timer_enabled.get():
                h = self.focus_remaining // 3600
                m = (self.focus_remaining % 3600) // 60
                s = self.focus_remaining % 60
                # Update entries while keeping them disabled
                for entry, val in [(self.hour_entry, h), (self.min_entry, m), (self.sec_entry, s)]:
                    entry.config(state="normal")
                    entry.delete(0, tk.END)
                    entry.insert(0, f"{val:02}")
                    entry.config(state="disabled")
            time.sleep(1)
            self.focus_remaining -= 1

        # Auto stop
        if self.focus_remaining <= 0 and self.is_focusing:
            self.stop_focus()

    # ---------- DISTRACTION CHALLENGE ----------
    def simulate_eye_tracking(self):

        #Initalize the eyeTracker
        eT: eyeTracker = eyeTracker()

        start = time.time()

        while self.is_focusing:
            end = time.time()

            rL = eT.getSingleFrame(1)

            # Calculate the rotation of all in frame
            for pitch, yaw, roll in rL:
                if (abs(pitch) < 25 or abs(yaw) < 20):
                    start = end

            # If noone in frame is looking at the camera for 10 seconds start the challenge
            if ((end - start) > 5):
                self.trigger_challenge()
                start = end

            print(end - start)

            if not self.is_focusing:
                break

        #Close the eyeTracker and start challenge
        eT.closeCamera()
        
    def trigger_challenge(self):
        popup = tk.Toplevel(self)
        popup.title("Refocus Challenge")
        tk.Label(popup, text="You looked away!\nSolve: 5 + 3 = ?").pack(pady=10)
        answer = tk.Entry(popup)
        answer.pack()
        def check():
            if answer.get() == "8":
                popup.destroy()
            else:
                tk.Label(popup, text="Try again").pack()
        tk.Button(popup, text="Submit", command=check).pack()

    # ---------- REPORT ----------
    def show_report(self, duration, points):
        popup = tk.Toplevel(self)
        popup.title("Report")
        tk.Label(popup, text=f"Time: {duration}s").pack()
        tk.Label(popup, text=f"Points Earned: {points}").pack()

    # ---------- REWARDS ----------
    def build_rewards_tab(self):
        frame = self.rewards_tab
        tk.Label(frame, text="Rewards Shop", font=("Arial", 18)).pack(pady=10)

        self.points_label = tk.Label(frame, text=f"Points: {self.points.get()}", font=("Arial", 16, "bold"))
        self.points_label.pack(pady=5)
        self.points.trace_add("write", lambda *args: self.points_label.config(text=f"Points: {self.points.get()}"))

        rewards_frame = tk.Frame(frame)
        rewards_frame.pack(pady=10)

        # Column 1: Breaks
        breaks_col = tk.Frame(rewards_frame)
        breaks_col.pack(side="left", padx=50, anchor="n")
        tk.Label(breaks_col, text="Breaks", font=("Arial", 14)).pack(pady=5)
        self.break_btn = tk.Button(breaks_col, text="Buy 5 min Break (50 pts)",
                                   command=lambda: self.buy_reward(50))
        self.break_btn.pack(pady=5)

        # Column 2: Themes
        themes_col = tk.Frame(rewards_frame)
        themes_col.pack(side="left", padx=50, anchor="n")
        tk.Label(themes_col, text="Themes", font=("Arial", 14)).pack(pady=5)

        self.theme_buttons = {}
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for name, theme in self.themes.items():
            if name in ["light", "dark"]:
                continue
            btn_frame = tk.Frame(themes_col)
            btn_frame.pack(pady=5)

            # Load preview image
            if theme["preview"]:
                img_path = os.path.join(script_dir, theme["preview"])
                if os.path.exists(img_path):
                    img = Image.open(img_path).resize((60, 40), Image.Resampling.LANCZOS)
                    # Locked overlay
                    if theme["locked"]:
                        overlay = Image.new('RGBA', img.size, (0,0,0,120))
                        img = img.convert("RGBA")
                        img = Image.alpha_composite(img, overlay)
                        draw = ImageDraw.Draw(img)
                        try:
                            font = ImageFont.truetype("arial.ttf", 12)
                        except:
                            font = ImageFont.load_default()
                        text = "LOCKED"
                        bbox = font.getbbox(text)
                        w = bbox[2] - bbox[0]
                        h = bbox[3] - bbox[1]
                        draw.text(((img.width-w)//2, (img.height-h)//2), text, fill=(255,255,255,255), font=font)
                    theme["preview_tk"] = ImageTk.PhotoImage(img)
                    lbl = tk.Label(btn_frame, image=theme["preview_tk"])
                    lbl.pack(side="left", padx=5)

            btn = tk.Button(btn_frame, text=f"Unlock {name.capitalize()} (100 pts)",
                            command=lambda n=name: self.buy_theme(n), width=20)
            btn.pack(side="left")
            theme["button"] = btn
            self.theme_buttons[name] = btn

        self.update_rewards_buttons()

    def update_rewards_buttons(self):
        self.break_btn.config(state="normal" if self.points.get() >= 50 else "disabled")
        for name, theme in self.themes.items():
            if name in ["light","dark"]:
                continue
            if not theme["locked"]:
                theme["button"].config(state="disabled")
            else:
                theme["button"].config(state="normal" if self.points.get() >=100 else "disabled")

    def buy_reward(self, cost):
        if self.points.get() >= cost:
            self.points.set(self.points.get()-cost)
            self.save_data()
            self.update_rewards_buttons()

    def buy_theme(self, theme_name):
        theme = self.themes[theme_name]
        if self.points.get()>=100 and theme["locked"]:
            self.points.set(self.points.get()-100)
            theme["locked"] = False
            theme["button"].config(state="disabled")
            # Update preview to remove overlay
            if theme["preview"]:
                img_path = theme["preview"]
                img = Image.open(img_path).resize((60,40), Image.Resampling.LANCZOS)
                theme["preview_tk"] = ImageTk.PhotoImage(img)
                # update label
                for widget in theme["button"].master.winfo_children():
                    if isinstance(widget, tk.Label):
                        widget.config(image=theme["preview_tk"])
            # Unlock in settings
            self.settings_buttons[theme_name].config(state="normal")
            self.save_data()
            self.update_rewards_buttons()
            print(f"{theme_name.capitalize()} theme unlocked!")

    # ---------- SETTINGS ----------
    def build_settings_tab(self):
        frame = self.settings_tab
        tk.Label(frame, text="Settings", font=("Arial", 18)).pack(pady=20)
        self.settings_buttons = {}
        for theme_name, theme in self.themes.items():
            btn = tk.Button(frame, text=f"Switch to {theme_name.capitalize()} Theme",
                            command=lambda t=theme_name: self.apply_theme(t))
            btn.pack(pady=5)
            self.settings_buttons[theme_name] = btn
            if theme["locked"]:
                btn.config(state="disabled")

    # ---------- APPLY THEME ----------
    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        self.configure(bg=theme["bg_color"])
        for tab in [self.main_tab, self.rewards_tab, self.settings_tab]:
            tab.config(bg=theme["bg_color"])
            for widget in tab.winfo_children():
                try:
                    widget.config(bg=theme["bg_color"], fg=theme["text_color"])
                except:
                    pass
        self.start_button.config(bg=theme["start_btn"], fg="white")
        self.stop_button.config(bg=theme["stop_btn"], fg="white")

        if theme["bg_image"]:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            img_path = os.path.join(script_dir, theme["bg_image"])
            if os.path.exists(img_path):
                self.original_bg_img = Image.open(img_path)
                self.resize_bg()
            else:
                print(f"Warning: {img_path} not found. Using color only.")
                self.main_bg_label.config(image="", bg=theme["bg_color"])
        else:
            self.main_bg_label.config(image="", bg=theme["bg_color"])

    def resize_bg(self, event=None):
        if hasattr(self, 'original_bg_img'):
            width = self.winfo_width()
            height = self.winfo_height()
            resized = self.original_bg_img.resize((width,height), Image.Resampling.LANCZOS)
            self.bg_img_tk = ImageTk.PhotoImage(resized)
            self.main_bg_label.config(image=self.bg_img_tk)

    # ---------- SAVE / LOAD DATA ----------
    def save_data(self):
        data = {
            "points": self.points.get(),
            "unlocked_themes": [name for name, t in self.themes.items() if not t["locked"]],
            "blocked_sites": self.blocked_sites
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.points.set(data.get("points", 100))
                unlocked = data.get("unlocked_themes", [])
                for name in unlocked:
                    if name in self.themes:
                        self.themes[name]["locked"] = False
                self.blocked_sites = data.get("blocked_sites", [])

if __name__ == "__main__":
    app = App()
    app.mainloop()
