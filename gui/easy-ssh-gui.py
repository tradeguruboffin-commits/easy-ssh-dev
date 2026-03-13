#!/usr/bin/env python3

import gi
import os
import sys

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

from gi.repository import Gtk, Vte, GLib, Gdk, Pango


# --------------------------------------------------
# ROOT PATH DETECTION (SAFE)
# --------------------------------------------------

def get_root_dir():
    """
    Detect project root in all cases:
    - Running from source
    - Installed in /opt/easy-ssh-dev
    - Running from PyInstaller --onedir
    """
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(exe_dir, ".."))
    current_dir = os.path.abspath(os.path.dirname(__file__))
    if os.path.basename(current_dir) == "gui":
        return os.path.abspath(os.path.join(current_dir, ".."))
    return current_dir


ROOT_DIR   = get_root_dir()
BIN_DIR    = os.path.join(ROOT_DIR, "bin")

SSHX_BIN   = os.path.join(BIN_DIR, "sshx")
SSHX_KEY   = os.path.join(BIN_DIR, "sshx-key")
SCPX_BIN   = os.path.join(BIN_DIR, "scpx")
SSHX_CPY   = os.path.join(BIN_DIR, "sshx-cpy")
GIT_AUTH   = os.path.join(BIN_DIR, "git-auth")
SSHX_RESET = os.path.join(BIN_DIR, "sshx-reset")


# --------------------------------------------------
# Global CSS Styling
# --------------------------------------------------

CSS = """
window {
    background-color: #1e1e2e;
}

/* Toolbar area */
#toolbar {
    background-color: #181825;
    padding: 6px 8px;
    border-bottom: 2px solid #313244;
}

/* All toolbar buttons */
#toolbar button {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 18px;
    font-weight: 600;
    min-height: 42px;
}

#toolbar button:hover {
    background-color: #45475a;
    color: #ffffff;
    border-color: #89b4fa;
}

#toolbar button:active {
    background-color: #89b4fa;
    color: #1e1e2e;
}

/* Close Tab button — red accent */
#btn_close {
    background-color: #3b1f2b;
    color: #f38ba8;
    border-color: #f38ba8;
}
#btn_close:hover {
    background-color: #f38ba8;
    color: #1e1e2e;
}

/* Notebook tabs */
notebook tab {
    background-color: #313244;
    color: #a6adc8;
    padding: 6px 16px;
    font-size: 17px;
    border-radius: 4px 4px 0 0;
    min-width: 80px;
}

notebook tab:checked {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border-bottom: 2px solid #89b4fa;
}

notebook header {
    background-color: #181825;
    border-bottom: 2px solid #313244;
}

/* Dialog */
dialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

dialog label {
    color: #cdd6f4;
    font-size: 17px;
}

dialog entry {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 8px 10px;
    font-size: 17px;
}

dialog entry:focus {
    border-color: #89b4fa;
}

dialog button {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 8px 20px;
    font-size: 17px;
    font-weight: 600;
}

dialog button:hover {
    background-color: #89b4fa;
    color: #1e1e2e;
    border-color: #89b4fa;
}

radiobutton label {
    color: #cdd6f4;
    font-size: 17px;
}

checkbutton label {
    color: #cdd6f4;
    font-size: 17px;
}

/* Tab close button */
#tab_close_btn {
    background: transparent;
    border: none;
    padding: 0px 2px;
    min-width: 20px;
    min-height: 20px;
    color: #a6adc8;
}

#tab_close_btn:hover {
    background-color: #f38ba8;
    color: #1e1e2e;
    border-radius: 4px;
}

scrollbar slider {
    background-color: #45475a;
    border-radius: 4px;
    min-width: 6px;
    min-height: 6px;
}

scrollbar slider:hover {
    background-color: #89b4fa;
}
"""


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


# --------------------------------------------------
# Terminal Tab
# --------------------------------------------------

class TerminalTab(Gtk.Box):
    def __init__(self, command=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.terminal = Vte.Terminal()

        # Visual settings
        self.terminal.set_mouse_autohide(False)
        self.terminal.set_scroll_on_output(True)
        self.terminal.set_scroll_on_keystroke(True)
        self.terminal.set_scrollback_lines(10000)

        # Font — larger, readable
        font = Pango.FontDescription("Monospace 20")
        self.terminal.set_font(font)

        # Dark color theme (Catppuccin Mocha)
        bg = Gdk.RGBA(); bg.parse("#1e1e2e")
        fg = Gdk.RGBA(); fg.parse("#cdd6f4")

        palette_hex = [
            "#45475a", "#f38ba8", "#a6e3a1", "#f9e2af",
            "#89b4fa", "#f5c2e7", "#94e2d5", "#bac2de",
            "#585b70", "#f38ba8", "#a6e3a1", "#f9e2af",
            "#89b4fa", "#f5c2e7", "#94e2d5", "#a6adc8",
        ]
        palette = []
        for c in palette_hex:
            r = Gdk.RGBA(); r.parse(c); palette.append(r)

        self.terminal.set_colors(fg, bg, palette)

        # Wrap in scrolled window
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.terminal)
        self.pack_start(scroll, True, True, 0)

        self.terminal.connect("button-press-event", self.on_right_click)
        self.terminal.connect("key-press-event",    self.on_key_press)

        self.spawn(command)
        self.show_all()

    def spawn(self, command=None):
        argv = command if command else [os.environ.get("SHELL", "/bin/bash")]

        self.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            os.environ.get("HOME", os.path.expanduser("~")),
            argv,
            None,
            GLib.SpawnFlags.SEARCH_PATH,
            None,
            None,
            -1,
            None,
            self._spawn_callback,
        )

    def _spawn_callback(self, terminal, pid, error):
        if error:
            print(f"[TerminalTab] spawn error: {error}", file=sys.stderr)

    # --------------------------------------------------
    # Right-click menu
    # --------------------------------------------------
    def on_right_click(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            menu = Gtk.Menu()
            for label, action in [
                ("Copy",       lambda w: self.terminal.copy_clipboard()),
                ("Paste",      lambda w: self.terminal.paste_clipboard()),
                ("Select All", lambda w: self.terminal.select_all()),
            ]:
                item = Gtk.MenuItem(label=label)
                item.connect("activate", action)
                menu.append(item)
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False

    # --------------------------------------------------
    # Keyboard shortcuts
    # --------------------------------------------------
    def on_key_press(self, widget, event):
        ctrl  = event.state & Gdk.ModifierType.CONTROL_MASK
        shift = event.state & Gdk.ModifierType.SHIFT_MASK
        key   = Gdk.keyval_name(event.keyval).lower()

        if ctrl and shift:
            if key == "c":
                self.terminal.copy_clipboard(); return True
            elif key == "v":
                self.terminal.paste_clipboard(); return True
            elif key == "a":
                self.terminal.select_all(); return True
        return False


# --------------------------------------------------
# Main Window
# --------------------------------------------------

class SSHXGUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="SSHX Ultimate Professional GUI")
        self.set_default_size(1600, 820)
        self.connect("destroy", Gtk.main_quit)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(main_box)

        # ---- Toolbar (scrollable so buttons never get hidden) ----
        toolbar_scroll = Gtk.ScrolledWindow()
        toolbar_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        toolbar_scroll.set_size_request(-1, 72)

        toolbar = Gtk.Box(spacing=6)
        toolbar.set_name("toolbar")
        toolbar.set_margin_start(4)
        toolbar.set_margin_end(4)
        toolbar.set_margin_top(8)
        toolbar.set_margin_bottom(8)
        toolbar_scroll.add(toolbar)
        main_box.pack_start(toolbar_scroll, False, False, 0)

        # Notebook
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        main_box.pack_start(self.notebook, True, True, 0)

        # ---- Core Buttons ----
        self.add_btn(toolbar, "Connect", self.connect_popup)
        self.add_btn(toolbar, "List",    lambda b: self.run_cmd([SSHX_BIN, "--list"],    "List"))
        self.add_btn(toolbar, "Doctor",  lambda b: self.run_cmd([SSHX_BIN, "--doctor"],  "Doctor"))
        self.add_btn(toolbar, "Version", lambda b: self.run_cmd([SSHX_BIN, "--version"], "Version"))
        self.add_btn(toolbar, "Help",    self.show_help_dialog)

        # Vertical separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_top(8)
        sep.set_margin_bottom(8)
        toolbar.pack_start(sep, False, False, 4)

        # ---- Advanced Buttons ----
        self.add_btn(toolbar, "Gen Key",          self.gen_key_popup)
        self.add_btn(toolbar, "Copy Fingerprint", self.copy_fingerprint)
        self.add_btn(toolbar, "Git Auth",         lambda b: self.run_cmd([GIT_AUTH],    "GitAuth"))
        self.add_btn(toolbar, "SSHX Copy",        self.sshx_copy_popup)
        self.add_btn(toolbar, "SSHX Reset",       lambda b: self.run_cmd([SSHX_RESET], "Reset"))
        self.add_btn(toolbar, "SCPX",             self.scpx_popup)

        # Open a default shell tab on startup
        self.new_tab(None, "Terminal", pinned=True)

        self.show_all()

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def add_btn(self, box, label, callback):
        btn = Gtk.Button(label=label)
        btn.connect("clicked", callback)
        box.pack_start(btn, False, False, 0)
        return btn

    def run_cmd(self, cmd, title):
        if not os.path.exists(cmd[0]):
            self.show_error(f"Command not found:\n{cmd[0]}")
            return
        self.new_tab(cmd, title)

    def new_tab(self, cmd=None, title="Terminal", pinned=False):
        tab = TerminalTab(cmd)

        tab_box   = Gtk.Box(spacing=6)
        tab_label = Gtk.Label(label=title)
        tab_box.pack_start(tab_label, True, True, 0)

        if not pinned:
            close_btn = Gtk.Button()
            close_btn.set_relief(Gtk.ReliefStyle.NONE)
            close_btn.set_focus_on_click(False)
            close_icon = Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
            close_btn.add(close_icon)
            close_btn.set_name("tab_close_btn")
            close_btn.connect("clicked", lambda b: self._close_tab_by_widget(tab))
            tab_box.pack_start(close_btn, False, False, 0)

        tab_box.show_all()
        page = self.notebook.append_page(tab, tab_box)
        self.notebook.set_current_page(page)
        self.show_all()

    def _close_tab_by_widget(self, tab_widget):
        page = self.notebook.page_num(tab_widget)
        if page != -1:
            self.notebook.remove_page(page)

    # --------------------------------------------------
    # Popups
    # --------------------------------------------------
    def connect_popup(self, button):
        dialog = Gtk.Dialog(title="Connect to SSHX", transient_for=self, flags=0)
        dialog.set_default_size(440, -1)
        dialog.add_buttons("Cancel",  Gtk.ResponseType.CANCEL,
                           "Connect", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        lbl = Gtk.Label(label="Enter target (user@host:port):")
        lbl.set_xalign(0)
        entry = Gtk.Entry()
        entry.set_placeholder_text("user@host:22")
        entry.set_activates_default(True)

        # Raw mode checkbox
        raw_check = Gtk.CheckButton(label="Raw mode  (ssh -p <port> <user@host>, skip cache)")

        box.pack_start(lbl,       False, False, 0)
        box.pack_start(entry,     False, False, 0)
        box.pack_start(raw_check, False, False, 4)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            value = entry.get_text().strip()
            if value:
                if raw_check.get_active():
                    self.run_cmd([SSHX_BIN, "--raw", value], f"RAW {value}")
                else:
                    self.run_cmd([SSHX_BIN, value], value)
            else:
                self.show_error("Input cannot be empty.")

        dialog.destroy()

    def show_help_dialog(self, button):
        HELP_TEXT = """\
┌─────────────────────────────────────────────────────────┐
│                  SSHX GUI — Command Reference           │
└─────────────────────────────────────────────────────────┘

━━━ sshx — SSH Connection Manager ━━━━━━━━━━━━━━━━━━━━━━━━

  sshx user@ip:port              Connect (auto key-copy + cache)
  sshx user@[ipv6]:port          Connect via IPv6
  sshx --raw user@ip:port        Direct connect — skip cache
  sshx user@ip:port --remove     Remove host from cache

  sshx --list                    List saved hosts
  sshx --menu                    Interactive fzf menu
  sshx --doctor                  Check dependencies
  sshx --version                 Show version

━━━ sshx-key — GitHub SSH Key Setup ━━━━━━━━━━━━━━━━━━━━━━

  sshx-key user@email.com        Generate key, add to agent,
                                 copy pubkey to clipboard

━━━ sshx-cpy — Copy SSH Public Key to Remote Host ━━━━━━━━

  sshx-cpy user@host[:port]      Install local pubkey on remote

━━━ scpx — File Transfer over SCP ━━━━━━━━━━━━━━━━━━━━━━━━

  scpx push user@host:port <local_path> <remote_dir>
  scpx pull user@host:port <remote_path> <local_dir>

━━━ git-auth — GitHub SSH Auth Check ━━━━━━━━━━━━━━━━━━━━━

  git-auth                       Verify GitHub SSH authentication

━━━ sshx-reset — Reset SSH Keys ━━━━━━━━━━━━━━━━━━━━━━━━━━

  sshx-reset                     Remove and regenerate SSH keys

━━━ GUI Shortcuts ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Ctrl+Shift+C                   Copy selected text
  Ctrl+Shift+V                   Paste
  Ctrl+Shift+A                   Select all
  Right-click                    Context menu (Copy/Paste/Select All)
"""
        dialog = Gtk.Dialog(title="Help — Command Reference", transient_for=self, flags=0)
        dialog.set_default_size(640, 560)
        dialog.add_buttons("Close", Gtk.ResponseType.CLOSE)

        box = dialog.get_content_area()
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_cursor_visible(False)
        tv.set_wrap_mode(Gtk.WrapMode.NONE)
        tv.set_monospace(True)
        tv.get_buffer().set_text(HELP_TEXT)
        tv.set_margin_start(8)
        tv.set_margin_end(8)
        tv.set_margin_top(8)
        tv.set_margin_bottom(8)

        scroll.add(tv)
        box.pack_start(scroll, True, True, 0)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def gen_key_popup(self, button):
        self.simple_input_popup(
            "Generate SSH Key",
            "Enter Email:",
            lambda v: self.run_cmd([SSHX_KEY, v], "KeyGen"),
        )

    def sshx_copy_popup(self, button):
        self.simple_input_popup(
            "SSHX Copy",
            "Enter user@host[:port]:",
            lambda v: self.run_cmd([SSHX_CPY, v], "SSHX Copy"),
        )

    def simple_input_popup(self, title, label_text, callback):
        dialog = Gtk.Dialog(title=title, transient_for=self, flags=0)
        dialog.set_default_size(400, -1)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
                           "OK",     Gtk.ResponseType.OK)

        box = dialog.get_content_area()
        box.set_spacing(8)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        lbl = Gtk.Label(label=label_text)
        lbl.set_xalign(0)
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        dialog.set_default_response(Gtk.ResponseType.OK)

        box.pack_start(lbl,   False, False, 0)
        box.pack_start(entry, False, False, 0)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            value = entry.get_text().strip()
            if value:
                callback(value)
            else:
                self.show_error("Input cannot be empty.")

        dialog.destroy()

    # --------------------------------------------------
    # SCPX Popup
    # --------------------------------------------------
    def scpx_popup(self, button):
        dialog = Gtk.Dialog(title="SCPX File Transfer", transient_for=self, flags=0)
        dialog.add_buttons("Cancel",   Gtk.ResponseType.CANCEL,
                           "Transfer", Gtk.ResponseType.OK)
        dialog.set_default_size(560, -1)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Mode
        mode_box   = Gtk.Box(spacing=14)
        push_radio = Gtk.RadioButton.new_with_label(None, "Push  (local → remote)")
        pull_radio = Gtk.RadioButton.new_with_label_from_widget(push_radio, "Pull  (remote → local)")
        mode_box.pack_start(Gtk.Label(label="Mode:"), False, False, 0)
        mode_box.pack_start(push_radio,               False, False, 0)
        mode_box.pack_start(pull_radio,               False, False, 0)
        box.pack_start(mode_box, False, False, 0)

        def make_row(lbl_text, placeholder):
            row = Gtk.Box(spacing=8)
            lbl = Gtk.Label(label=lbl_text)
            lbl.set_width_chars(14)
            lbl.set_xalign(0)
            ent = Gtk.Entry()
            ent.set_placeholder_text(placeholder)
            row.pack_start(lbl, False, False, 0)
            row.pack_start(ent, True,  True,  0)
            box.pack_start(row, False, False, 0)
            return ent

        host_entry   = make_row("user@host:port:", "user@192.168.1.1:22")
        remote_entry = make_row("Remote path:",    "/remote/dir/  or  /remote/file.txt")

        # Local path with File + Folder browse buttons
        local_row   = Gtk.Box(spacing=8)
        local_lbl   = Gtk.Label(label="Local path:")
        local_lbl.set_width_chars(14)
        local_lbl.set_xalign(0)
        local_entry = Gtk.Entry()
        local_entry.set_placeholder_text("/home/user/file.txt  or  /home/user/folder/")
        file_btn    = Gtk.Button(label="File…")
        folder_btn  = Gtk.Button(label="Folder…")

        def browse(action):
            fc = Gtk.FileChooserDialog(
                title="Select " + ("Folder" if action == Gtk.FileChooserAction.SELECT_FOLDER else "File"),
                transient_for=dialog,
                action=action,
            )
            fc.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
                           "Select", Gtk.ResponseType.OK)
            if fc.run() == Gtk.ResponseType.OK:
                local_entry.set_text(fc.get_filename())
            fc.destroy()

        file_btn.connect("clicked",   lambda b: browse(Gtk.FileChooserAction.OPEN))
        folder_btn.connect("clicked", lambda b: browse(Gtk.FileChooserAction.SELECT_FOLDER))

        local_row.pack_start(local_lbl,   False, False, 0)
        local_row.pack_start(local_entry, True,  True,  0)
        local_row.pack_start(file_btn,    False, False, 0)
        local_row.pack_start(folder_btn,  False, False, 0)
        box.pack_start(local_row, False, False, 0)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            mode   = "push" if push_radio.get_active() else "pull"
            host   = host_entry.get_text().strip()
            local  = local_entry.get_text().strip()
            remote = remote_entry.get_text().strip()

            if not host or not local or not remote:
                dialog.destroy()
                self.show_error("All fields are required.")
                return

            cmd = (
                [SCPX_BIN, "push", host, local, remote]
                if mode == "push"
                else [SCPX_BIN, "pull", host, remote, local]
            )
            self.run_cmd(cmd, f"SCPX {mode} → {host}")

        dialog.destroy()

    # --------------------------------------------------
    # Fingerprint
    # --------------------------------------------------
    def copy_fingerprint(self, button):
        pubkey = os.path.expanduser("~/.ssh/id_ed25519.pub")
        if not os.path.exists(pubkey):
            self.show_error("Public key not found:\n~/.ssh/id_ed25519.pub")
            return
        self.new_tab(["ssh-keygen", "-lf", pubkey], "Fingerprint")

    # --------------------------------------------------
    # Tabs
    # --------------------------------------------------
    def close_tab(self, button):
        page = self.notebook.get_current_page()
        if page != -1:
            self.notebook.remove_page(page)

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    apply_css()
    win = SSHXGUI()
    Gtk.main()
