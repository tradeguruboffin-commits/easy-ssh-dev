#!/usr/bin/env python3

import gi
import os
import sys

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

from gi.repository import Gtk, Vte, GLib, Gdk


# --------------------------------------------------
# ROOT PATH DETECTION (SAFE)
# --------------------------------------------------

def get_root_dir():
    """
    Detect project root in all cases:
    - Running from source
    - Installed in /opt/esey-ssh-dev
    - Running from PyInstaller --onedir
    """
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(exe_dir, ".."))
    current_dir = os.path.abspath(os.path.dirname(__file__))
    if os.path.basename(current_dir) == "gui":
        return os.path.abspath(os.path.join(current_dir, ".."))
    return current_dir


ROOT_DIR = get_root_dir()
BIN_DIR = os.path.join(ROOT_DIR, "bin")
LIB_DIR = os.path.join(ROOT_DIR, "lib")

SSHX_BIN  = os.path.join(BIN_DIR, "sshx")
SSHX_KEY  = os.path.join(BIN_DIR, "sshx-key")
SCPX_BIN  = os.path.join(BIN_DIR, "scpx")
SSHX_CPY  = os.path.join(LIB_DIR, "sshx-cpy")
GIT_AUTH  = os.path.join(LIB_DIR, "git-auth")
SSHX_RESET = os.path.join(LIB_DIR, "sshx-reset")


# --------------------------------------------------
# Terminal Tab
# --------------------------------------------------

class TerminalTab(Gtk.Box):
    def __init__(self, command=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.terminal = Vte.Terminal()
        self.pack_start(self.terminal, True, True, 0)

        self.terminal.set_mouse_autohide(False)
        self.terminal.set_rewrap_on_resize(True)

        self.terminal.connect("button-press-event", self.on_right_click)
        self.terminal.connect("key-press-event", self.on_key_press)

        self.spawn(command)
        self.show_all()

    def spawn(self, command=None):
        if command:
            argv = command
        else:
            argv = [os.environ.get("SHELL", "/bin/bash")]

        self.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            os.environ.get("HOME"),
            argv,
            [],
            GLib.SpawnFlags.DEFAULT,
            None,
            None,
            -1,
            None,
            None,
        )

    # --------------------------------------------------
    # Right-click menu
    # --------------------------------------------------
    def on_right_click(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            menu = Gtk.Menu()

            copy_item = Gtk.MenuItem(label="Copy")
            copy_item.connect("activate", lambda w: self.terminal.copy_clipboard())
            menu.append(copy_item)

            paste_item = Gtk.MenuItem(label="Paste")
            paste_item.connect("activate", lambda w: self.terminal.paste_clipboard())
            menu.append(paste_item)

            select_all_item = Gtk.MenuItem(label="Select All")
            select_all_item.connect("activate", lambda w: self.terminal.select_all())
            menu.append(select_all_item)

            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False

    # --------------------------------------------------
    # Keyboard shortcuts
    # --------------------------------------------------
    def on_key_press(self, widget, event):
        ctrl  = (event.state & Gdk.ModifierType.CONTROL_MASK)
        shift = (event.state & Gdk.ModifierType.SHIFT_MASK)
        key   = Gdk.keyval_name(event.keyval).lower()

        if ctrl and shift:
            if key == "c":
                self.terminal.copy_clipboard()
                return True
            elif key == "v":
                self.terminal.paste_clipboard()
                return True
            elif key == "a":
                self.terminal.select_all()
                return True
        return False


# --------------------------------------------------
# Main Window
# --------------------------------------------------

class SSHXGUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="SSHX Ultimate Professional GUI")
        self.set_default_size(1600, 900)
        self.connect("destroy", Gtk.main_quit)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(main_box)

        toolbar = Gtk.Box(spacing=6)
        main_box.pack_start(toolbar, False, False, 0)

        self.notebook = Gtk.Notebook()
        main_box.pack_start(self.notebook, True, True, 0)

        # Core Buttons
        self.add_btn(toolbar, "Connect",          self.connect_popup)
        self.add_btn(toolbar, "List",             lambda b: self.run_cmd([SSHX_BIN, "--list"],    "List"))
        self.add_btn(toolbar, "Doctor",           lambda b: self.run_cmd([SSHX_BIN, "--doctor"],  "Doctor"))
        self.add_btn(toolbar, "Version",          lambda b: self.run_cmd([SSHX_BIN, "--version"], "Version"))
        self.add_btn(toolbar, "Help",             lambda b: self.run_cmd([SSHX_BIN, "--help"],    "Help"))

        # Advanced Buttons
        self.add_btn(toolbar, "Gen Key",          self.gen_key_popup)
        self.add_btn(toolbar, "Copy Fingerprint", self.copy_fingerprint)
        self.add_btn(toolbar, "Git Auth",         lambda b: self.run_cmd([GIT_AUTH],    "GitAuth"))
        self.add_btn(toolbar, "SSHX Copy",        self.sshx_copy_popup)
        self.add_btn(toolbar, "SSHX Reset",       lambda b: self.run_cmd([SSHX_RESET], "Reset"))

        # SCPX Button
        self.add_btn(toolbar, "SCPX",             self.scpx_popup)

        self.add_btn(toolbar, "Close Tab",        self.close_tab)

        self.show_all()

    # --------------------------------------------------
    # Buttons
    # --------------------------------------------------
    def add_btn(self, box, label, callback):
        btn = Gtk.Button(label=label)
        btn.connect("clicked", callback)
        box.pack_start(btn, False, False, 0)

    def run_cmd(self, cmd, title):
        if not os.path.exists(cmd[0]):
            self.show_error(f"Command not found:\n{cmd[0]}")
            return
        self.new_tab(cmd, title)

    def new_tab(self, cmd=None, title="Terminal"):
        tab = TerminalTab(cmd)
        label = Gtk.Label(label=title)
        page = self.notebook.append_page(tab, label)
        self.notebook.set_current_page(page)
        self.show_all()

    # --------------------------------------------------
    # Popups
    # --------------------------------------------------
    def connect_popup(self, button):
        self.simple_input_popup(
            "Connect to SSHX",
            "Enter target (user@host):",
            lambda value: self.run_cmd([SSHX_BIN, value], value)
        )

    def gen_key_popup(self, button):
        self.simple_input_popup(
            "Generate SSH Key",
            "Enter Email:",
            lambda value: self.run_cmd([SSHX_KEY, value], "KeyGen")
        )

    def sshx_copy_popup(self, button):
        self.simple_input_popup(
            "SSHX Copy",
            "Enter user@host[:port]:",
            lambda value: self.run_cmd([SSHX_CPY, value], "SSHX Copy")
        )

    def simple_input_popup(self, title, label_text, callback):
        dialog = Gtk.Dialog(title=title, transient_for=self, flags=0)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
                           "OK",     Gtk.ResponseType.OK)

        box = dialog.get_content_area()

        label = Gtk.Label(label=label_text)
        entry = Gtk.Entry()

        box.pack_start(label, False, False, 5)
        box.pack_start(entry, False, False, 5)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            value = entry.get_text().strip()
            if value:
                callback(value)

        dialog.destroy()

    # --------------------------------------------------
    # SCPX Popup
    # --------------------------------------------------
    def scpx_popup(self, button):
        dialog = Gtk.Dialog(title="SCPX File Transfer", transient_for=self, flags=0)
        dialog.add_buttons("Cancel",   Gtk.ResponseType.CANCEL,
                           "Transfer", Gtk.ResponseType.OK)
        dialog.set_default_size(520, 320)

        box = dialog.get_content_area()
        box.set_spacing(8)

        # ---- Mode: Push / Pull ----
        mode_box = Gtk.Box(spacing=10)
        mode_label = Gtk.Label(label="Mode:")
        push_radio = Gtk.RadioButton.new_with_label(None, "Push  (local → remote)")
        pull_radio  = Gtk.RadioButton.new_with_label_from_widget(push_radio, "Pull  (remote → local)")
        mode_box.pack_start(mode_label,  False, False, 5)
        mode_box.pack_start(push_radio,  False, False, 0)
        mode_box.pack_start(pull_radio,  False, False, 0)
        box.pack_start(mode_box, False, False, 5)

        # ---- user@host:port ----
        host_box   = Gtk.Box(spacing=6)
        host_label = Gtk.Label(label="user@host:port:")
        host_label.set_width_chars(16)
        host_label.set_xalign(0)
        host_entry = Gtk.Entry()
        host_entry.set_placeholder_text("user@192.168.1.1:22")
        host_box.pack_start(host_label, False, False, 5)
        host_box.pack_start(host_entry, True,  True,  0)
        box.pack_start(host_box, False, False, 5)

        # ---- Local path (file chooser) ----
        local_box    = Gtk.Box(spacing=6)
        local_label  = Gtk.Label(label="Local path:")
        local_label.set_width_chars(16)
        local_label.set_xalign(0)
        local_entry  = Gtk.Entry()
        local_entry.set_placeholder_text("/home/user/file.txt  or  /home/user/folder/")
        local_browse = Gtk.Button(label="Browse…")

        def browse_local(b):
            fc = Gtk.FileChooserDialog(
                title="Select Local File or Folder",
                transient_for=dialog,
                action=Gtk.FileChooserAction.OPEN
            )
            fc.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
                           "Select", Gtk.ResponseType.OK)
            # Allow selecting folders too
            fc.set_action(Gtk.FileChooserAction.OPEN)
            if fc.run() == Gtk.ResponseType.OK:
                local_entry.set_text(fc.get_filename())
            fc.destroy()

        local_browse.connect("clicked", browse_local)
        local_box.pack_start(local_label,  False, False, 5)
        local_box.pack_start(local_entry,  True,  True,  0)
        local_box.pack_start(local_browse, False, False, 0)
        box.pack_start(local_box, False, False, 5)

        # ---- Remote path ----
        remote_box   = Gtk.Box(spacing=6)
        remote_label = Gtk.Label(label="Remote path:")
        remote_label.set_width_chars(16)
        remote_label.set_xalign(0)
        remote_entry = Gtk.Entry()
        remote_entry.set_placeholder_text("/remote/dir/  or  /remote/file.txt")
        remote_box.pack_start(remote_label, False, False, 5)
        remote_box.pack_start(remote_entry, True,  True,  0)
        box.pack_start(remote_box, False, False, 5)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            mode   = "push" if push_radio.get_active() else "pull"
            host   = host_entry.get_text().strip()
            local  = local_entry.get_text().strip()
            remote = remote_entry.get_text().strip()

            if not host or not local or not remote:
                self.show_error("সব field পূরণ করো।")
                dialog.destroy()
                return

            # scpx push user@host:port <local_path> <remote_dir>
            # scpx pull user@host:port <remote_path> <local_dir>
            if mode == "push":
                cmd = [SCPX_BIN, "push", host, local, remote]
            else:
                cmd = [SCPX_BIN, "pull", host, remote, local]

            self.run_cmd(cmd, f"SCPX {mode} → {host}")

        dialog.destroy()

    # --------------------------------------------------
    # Fingerprint
    # --------------------------------------------------
    def copy_fingerprint(self, button):
        pubkey = os.path.expanduser("~/.ssh/id_ed25519.pub")
        if not os.path.exists(pubkey):
            self.show_error("Public key not found.")
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
    win = SSHXGUI()
    Gtk.main()
