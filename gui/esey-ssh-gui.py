#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import pty, os, threading, select, re, signal, sys

ANSI_ESCAPE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

# -----------------------------
# Root directory fix for binaries
# -----------------------------
if getattr(sys, 'frozen', False):
    # PyInstaller runtime
    BASE_DIR = sys._MEIPASS
else:
    # Running as script
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

LIB_DIR = os.path.join(BASE_DIR, "lib")  # PyInstaller এ lib ফোল্ডার থাকবে _MEIPASS/lib

# -----------------------------
# Terminal Tab
# -----------------------------
class TerminalTab:
    def __init__(self, notebook, title="Terminal", cmd=None):
        self.notebook = notebook
        self.frame = tk.Frame(notebook)

        self.text = tk.Text(
            self.frame,
            bg="black",
            fg="white",
            insertbackground="white",
            font=("Courier", 24),
            wrap="none"
        )
        self.text.pack(fill="both", expand=True)

        # Key bindings
        self.text.bind("<Key>", self.send_input)
        self.text.bind("<Return>", self.send_input)
        self.text.bind("<BackSpace>", self.send_input)
        self.text.bind("<Delete>", self.send_input)
        self.text.bind("<Configure>", self.on_resize)

        # Terminal shortcuts
        self.text.bind("<Control-Shift-C>", self.copy_selection)
        self.text.bind("<Control-Shift-V>", self.paste_clipboard)
        self.text.bind("<Control-c>", self.send_ctrl_c)

        # Right Click Menu
        self.menu = tk.Menu(self.text, tearoff=0)
        self.menu.add_command(label="Copy", command=self.copy_selection)
        self.menu.add_command(label="Paste", command=self.paste_clipboard)
        self.menu.add_command(label="Select All",
                              command=lambda: self.text.tag_add("sel", "1.0", "end"))
        self.text.bind("<Button-3>", self.show_menu)

        # Run PTY subprocess
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.environ["TERM"] = "xterm"
            os.environ["PS1"] = "$ "
            if cmd:
                try:
                    os.chmod(cmd[0], 0o755)
                except:
                    pass
                os.execvp(cmd[0], cmd)
            else:
                os.execvp("bash", ["bash", "--norc", "--noprofile"])

        threading.Thread(target=self.read_output, daemon=True).start()

        notebook.add(self.frame, text=title)
        notebook.select(self.frame)

    def show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def read_output(self):
        while True:
            try:
                r, _, _ = select.select([self.fd], [], [], 0.1)
                if self.fd in r:
                    output = os.read(self.fd, 1024).decode(errors="ignore")
                    output = ANSI_ESCAPE.sub('', output)
                    self.text.insert("end", output)
                    self.text.see("end")
            except:
                break

    def send_input(self, event):
        if event.char and ord(event.char) >= 32:
            os.write(self.fd, event.char.encode())
        else:
            if event.keysym == "Return":
                os.write(self.fd, b"\n")
            elif event.keysym == "BackSpace":
                os.write(self.fd, b"\x7f")
            elif event.keysym == "Delete":
                os.write(self.fd, b"\x1b[3~")
        return "break"

    def send_ctrl_c(self, event=None):
        try:
            os.write(self.fd, b'\x03')
        except:
            pass
        return "break"

    def copy_selection(self, event=None):
        try:
            selected = self.text.get("sel.first", "sel.last")
            self.text.clipboard_clear()
            self.text.clipboard_append(selected)
        except:
            pass
        return "break"

    def paste_clipboard(self, event=None):
        try:
            data = self.text.clipboard_get()
            os.write(self.fd, data.encode())
        except:
            pass
        return "break"

    def on_resize(self, event):
        rows = int(self.text.winfo_height() / 36)
        cols = int(self.text.winfo_width() / 18)
        try:
            os.system(f"stty rows {rows} cols {cols}")
        except:
            pass

    def close(self):
        try:
            os.kill(self.pid, signal.SIGKILL)
        except:
            pass

# -----------------------------
# Main GUI
# -----------------------------
class SSHXGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SSHX Control Panel")
        self.geometry("1920x850")
        self.minsize(1400, 800)

        self.tabs = {}

        self.build_top()
        self.build_buttons()
        self.build_notebook()

    def build_top(self):
        top = tk.Frame(self, height=100)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="SSHX Control Panel", font=("Arial", 36)).pack(side="left", padx=40)

        self.entry = tk.Entry(top, font=("Arial", 28), width=35)
        self.entry.pack(side="right", padx=40)

        # Right Click + Ctrl Copy/Paste
        self.entry.bind("<Control-c>", lambda e: self.entry.event_generate("<<Copy>>"))
        self.entry.bind("<Control-v>", lambda e: self.entry.event_generate("<<Paste>>"))
        self.entry.bind("<Control-a>", lambda e: self.entry.select_range(0, 'end'))

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Copy", command=lambda: self.entry.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: self.entry.event_generate("<<Paste>>"))
        menu.add_command(label="Select All", command=lambda: self.entry.select_range(0, 'end'))

        self.entry.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def build_buttons(self):
        bar = tk.Frame(self)
        bar.pack(fill="x", pady=20)

        buttons = [
            ("Connect", self.connect),
            ("List", lambda: self.run_cmd("sshx --list")),
            ("Menu", lambda: self.run_cmd(["sshx", "--menu"])),
            ("Doctor", lambda: self.run_cmd("sshx --doctor")),
            ("Version", lambda: self.run_cmd("sshx --version")),
            ("Help", lambda: self.run_cmd("sshx --help")),
            ("Git Auth", self.git_auth_terminal),
            ("SSHX Reset", self.sshx_reset_terminal),
            ("Close Tab", self.close_tab)
        ]

        for i, (text, cmd) in enumerate(buttons):
            btn = tk.Button(bar, text=text, command=cmd, font=("Arial", 20), width=16, height=2)
            btn.grid(row=i//5, column=i%5, padx=20, pady=15)

    def build_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

    # Terminal Launchers
    def new_terminal(self):
        tab = TerminalTab(self.notebook, "Terminal")
        self.tabs[tab.frame] = tab

    def git_auth_terminal(self):
        git_auth = os.path.join(LIB_DIR, "git-auth")
        if os.path.exists(git_auth):
            os.chmod(git_auth, 0o755)
            tab = TerminalTab(self.notebook, "GitAuth", cmd=[git_auth])
            self.tabs[tab.frame] = tab
        else:
            self.run_cmd(f"echo '{git_auth} not found'")

    def sshx_reset_terminal(self):
        reset_path = os.path.join(LIB_DIR, "sshx-reset")
        if os.path.exists(reset_path):
            os.chmod(reset_path, 0o755)
            tab = TerminalTab(self.notebook, "SSHX Reset", cmd=[reset_path])
            self.tabs[tab.frame] = tab
        else:
            self.run_cmd(f"echo '{reset_path} not found'")

    def connect(self):
        target = self.entry.get().strip()
        if target:
            tab = TerminalTab(self.notebook, target)
            self.tabs[tab.frame] = tab
            os.write(tab.fd, f"sshx {target}\n".encode())

    def run_cmd(self, cmd):
        if isinstance(cmd, str):
            cmd = ["bash", "-c", cmd]
        tab = TerminalTab(self.notebook, "Command", cmd=cmd)
        self.tabs[tab.frame] = tab

    def close_tab(self):
        current = self.notebook.select()
        if current:
            tab = self.tabs.get(self.nametowidget(current))
            if tab:
                tab.close()
            self.notebook.forget(current)

# -----------------------------
# Run GUI
# -----------------------------
if __name__ == "__main__":
    SSHXGUI().mainloop()
