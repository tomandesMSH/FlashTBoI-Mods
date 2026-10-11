"""Tkinter window: pick the mods, install them into the game, copy the Steam launch option, play."""
import os
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__, game, install, releases
from .mods import MODS

TITLE = "TBoI Flash Mods " + __version__


class App:
    def __init__(self, root, out_dir, source=None):
        self.root, self.source = root, source
        self.events = queue.Queue()
        self.busy = False
        state = install.installed(out_dir)
        self.latest = {}

        root.title(TITLE)
        root.minsize(620, 520)
        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="The Binding of Isaac (Flash) mods", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(frm, text="Choose the mods you want. The newest version of each is downloaded and added to "
                            "your own copy of the game; your installation is not changed.",
                  wraplength=580).grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 10))

        self.game_var = tk.StringVar(value=state.get("game") or game.find_game() or "")
        self.out_var = tk.StringVar(value=os.path.abspath(out_dir))
        for row, (label, var, cmd) in enumerate([("Game folder:", self.game_var, self.browse_game),
                                                 ("Install to:", self.out_var, self.browse_out)], start=2):
            ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w")
            ttk.Entry(frm, textvariable=var).grid(row=row, column=1, sticky="ew", padx=6, pady=2)
            ttk.Button(frm, text="Browse...", command=cmd).grid(row=row, column=2)
        self.out_var.trace_add("write", lambda *a: self.refresh_versions())

        box = ttk.LabelFrame(frm, text="Mods", padding=8)
        box.grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
        box.columnconfigure(0, weight=1)
        self.checks, self.version_labels = {}, {}
        for i, m in enumerate(MODS):
            var = tk.BooleanVar(value=m["id"] in state.get("mods", {}) if state else True)
            var.trace_add("write", lambda *a: self.update_buttons())
            self.checks[m["id"]] = var
            ttk.Checkbutton(box, text=m["name"], variable=var).grid(row=2 * i, column=0, sticky="w")
            lbl = ttk.Label(box, text="", foreground="#666")
            lbl.grid(row=2 * i, column=1, sticky="e")
            self.version_labels[m["id"]] = lbl
            ttk.Label(box, text=m["description"], foreground="#444", wraplength=540).grid(
                row=2 * i + 1, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=(0, 6))

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=3, sticky="ew")
        self.install_btn = ttk.Button(btns, text="Install / update selected mods", command=self.start_install)
        self.install_btn.pack(side="left")
        self.play_btn = ttk.Button(btns, text="Play", command=self.play)
        self.play_btn.pack(side="left", padx=6)

        opt = ttk.LabelFrame(frm, text="Steam launch option (Steam's Play button starts the modded game)", padding=8)
        opt.grid(row=6, column=0, columnspan=3, sticky="ew", pady=10)
        opt.columnconfigure(0, weight=1)
        self.opt_var = tk.StringVar()
        ttk.Entry(opt, textvariable=self.opt_var, state="readonly").grid(row=0, column=0, sticky="ew")
        self.copy_btn = ttk.Button(opt, text="Copy", command=self.copy_option)
        self.copy_btn.grid(row=0, column=1, padx=(6, 0))
        ttk.Label(opt, text="Steam > Library > right-click The Binding of Isaac > Properties > General > Launch Options. "
                            "Clear it again to play the normal game.", foreground="#444", wraplength=580).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        frm.rowconfigure(7, weight=1)
        self.log_box = tk.Text(frm, height=8, state="disabled", wrap="word", font=("Consolas", 9))
        self.log_box.grid(row=7, column=0, columnspan=3, sticky="nsew")

        self.refresh_versions()
        self.fetch_latest()
        self.root.after(100, self.poll)

    # ------------------------------------------------------------- helpers

    def out_dir(self):
        return self.out_var.get().strip()

    def log(self, msg):
        self.events.put(("log", msg))

    def poll(self):
        try:
            while True:
                kind, arg = self.events.get_nowait()
                if kind == "log":
                    self.log_box.configure(state="normal")
                    self.log_box.insert("end", arg + "\n")
                    self.log_box.see("end")
                    self.log_box.configure(state="disabled")
                elif kind == "latest":
                    self.latest.update(arg)
                    self.refresh_versions()
                elif kind == "done":
                    self.busy = False
                    self.refresh_versions()
                    if arg:
                        self.copy_option()
                        messagebox.showinfo(TITLE, "The mods are installed.\n\nThe Steam launch option is on your "
                                                   "clipboard. You can also start the game with Play.")
                elif kind == "error":
                    self.busy = False
                    self.update_buttons()
                    messagebox.showerror(TITLE, arg)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def refresh_versions(self):
        state = install.installed(self.out_dir())
        have = state.get("mods", {})
        for m in MODS:
            parts = []
            if m["id"] in have:
                parts.append("installed " + have[m["id"]])
            new = self.latest.get(m["id"])
            if new and new != have.get(m["id"]):
                parts.append(("newest " + new) if not new.startswith("(") else new)
            self.version_labels[m["id"]].configure(text=", ".join(parts))
        self.opt_var.set(install.launch_option(self.out_dir()) if have else "")
        self.update_buttons()

    def update_buttons(self):
        have = bool(install.installed(self.out_dir()).get("mods"))
        any_selected = any(v.get() for v in self.checks.values())
        self.install_btn.configure(state="normal" if any_selected and not self.busy else "disabled")
        self.play_btn.configure(state="normal" if have and not self.busy else "disabled")
        self.copy_btn.configure(state="normal" if have else "disabled")

    def fetch_latest(self):
        def run():
            found = {}
            for m in MODS:
                try:
                    found[m["id"]] = releases.latest(m, self.source)["version"]
                except releases.NoRelease:
                    found[m["id"]] = "(no release yet)"
                except Exception:
                    found[m["id"]] = "(offline)"
            self.events.put(("latest", found))
        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------- actions

    def browse_game(self):
        d = filedialog.askdirectory(title="Folder with Isaac.exe", initialdir=self.game_var.get() or None)
        if d:
            self.game_var.set(os.path.normpath(d))

    def browse_out(self):
        d = filedialog.askdirectory(title="Install the modded game to", initialdir=self.out_dir() or None)
        if d:
            self.out_var.set(os.path.normpath(d))

    def start_install(self):
        game_dir = self.game_var.get().strip()
        if not os.path.exists(os.path.join(game_dir, "Isaac.exe")):
            messagebox.showerror(TITLE, "Choose the game folder (the one with Isaac.exe).")
            return
        ids = [i for i, v in self.checks.items() if v.get()]
        self.busy = True
        self.update_buttons()

        def run():
            try:
                option = install.install(ids, game_dir, self.out_dir(), log=self.log, source=self.source)
                self.events.put(("done", option))
            except Exception as e:
                self.log("Error: " + str(e))
                self.events.put(("error", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def copy_option(self):
        if self.opt_var.get():
            self.root.clipboard_clear()
            self.root.clipboard_append(self.opt_var.get())
            self.log("Copied the Steam launch option to the clipboard.")

    def play(self):
        exe = os.path.join(self.out_dir(), install.LAUNCHER)
        if os.path.exists(exe):
            subprocess.Popen([exe], cwd=self.out_dir())


def main(out_dir, source=None):
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    App(root, out_dir, source)
    root.mainloop()
