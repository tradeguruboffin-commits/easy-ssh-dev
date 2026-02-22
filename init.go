package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
)

var binaries = []string{
	"bin/sshx",
	"bin/sshx-key",
	"bin/scpx",
	"lib/sshx-cpy",
	"lib/sshx-reset",
	"lib/git-auth",
	"gui/sshx-gui",
}

// uninstall করার সময় দুটো জায়গাই চেক করবে
var allTargetDirs = []string{
	"/usr/local/bin",
	filepath.Join(os.Getenv("HOME"), ".local/bin"),
}

/* ===========================
   Color Output
=========================== */

const (
	Green = "\033[32m"
	Blue  = "\033[34m"
	Red   = "\033[31m"
	Bold  = "\033[1m"
	Reset = "\033[0m"
)

func info(msg string)    { fmt.Println(Blue + Bold + msg + Reset) }
func success(msg string) { fmt.Println(Green + "✔ " + msg + Reset) }
func fail(msg string) {
	fmt.Println(Red + "✘ " + msg + Reset)
	os.Exit(1)
}

/* ===========================
   Privilege Detection
=========================== */

var (
	useSudo   bool
	targetDir string
)

func init() {

	// Root user
	if os.Geteuid() == 0 {
		useSudo = false
		targetDir = "/usr/local/bin"
		return
	}

	// sudo available
	if _, err := exec.LookPath("sudo"); err == nil {
		useSudo = true
		targetDir = "/usr/local/bin"
		return
	}

	// Fallback (proot / termux / no sudo)
	useSudo = false
	targetDir = filepath.Join(os.Getenv("HOME"), ".local/bin")
}

func runCommand(name string, args ...string) error {
	if useSudo {
		args = append([]string{name}, args...)
		name = "sudo"
	}
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// privilege-aware remove — system path হলে sudo, user path হলে সরাসরি
func removeFile(path string) error {
	if filepath.Dir(path) == "/usr/local/bin" {
		return runCommand("rm", "-f", path)
	}
	return os.Remove(path)
}

/* ===========================
   Main
=========================== */

func main() {
	if len(os.Args) < 2 {
		usage()
		return
	}

	switch os.Args[1] {
	case "install":
		install()
	case "uninstall":
		uninstall()
	default:
		usage()
	}
}

func usage() {
	fmt.Println("Usage:")
	fmt.Println("  sshx-dev install")
	fmt.Println("  sshx-dev uninstall")
}

/* ===========================
   Project Root
=========================== */

func projectRoot() string {
	exe, err := os.Executable()
	if err != nil {
		log.Fatal("Cannot detect executable path:", err)
	}
	exePath, _ := filepath.EvalSymlinks(exe)
	return filepath.Dir(exePath)
}

/* ===========================
   Install
=========================== */

func install() {
	info("Installing esey-ssh-dev...")

	baseDir := projectRoot()

	// targetDir না থাকলে তৈরি করো (proot fallback এর জন্য)
	os.MkdirAll(targetDir, 0755)

	guiPath := filepath.Join(baseDir, "gui/sshx-gui")
	guiExists := fileExists(guiPath)

	for _, bin := range binaries {

		if bin == "gui/sshx-gui" && !guiExists {
			info("GUI binary not found → skipping GUI install")
			continue
		}

		src := filepath.Join(baseDir, bin)
		name := filepath.Base(bin)
		dest := filepath.Join(targetDir, name)

		if _, err := os.Stat(src); os.IsNotExist(err) {
			fail("Missing binary: " + src)
		}

		removeIfExists(dest)

		if err := runCommand("ln", "-s", src, dest); err != nil {
			fail("Failed linking " + name + ": " + err.Error())
		}

		success(name + " linked → " + dest)
	}

	if guiExists {
		createDesktopEntry(baseDir)
		updateDesktopDatabase()
	} else {
		info("GUI not present → skipping desktop entry")
	}

	success("Installation complete 🎉")
	info("Installed to: " + targetDir)
}

/* ===========================
   Uninstall
   — দুটো জায়গাই চেক করে, যেখানে পাবে মুছবে
=========================== */

func uninstall() {
	info("Uninstalling esey-ssh-dev...")

	removedAny := false

	for _, bin := range binaries {
		name := filepath.Base(bin)

		for _, dir := range allTargetDirs {
			dest := filepath.Join(dir, name)

			if fileExists(dest) {
				if err := removeFile(dest); err != nil {
					info("Could not remove " + dest + ": " + err.Error())
				} else {
					success(name + " removed from " + dir)
					removedAny = true
				}
			}
		}
	}

	if !removedAny {
		info("No installed binaries found → nothing to remove")
	}

	// Desktop entry
	desktopFile := filepath.Join(
		os.Getenv("HOME"),
		".local/share/applications/sshx-gui.desktop",
	)

	if fileExists(desktopFile) {
		os.Remove(desktopFile)
		success("Desktop entry removed")
	} else {
		info("No desktop entry found → nothing to remove")
	}

	updateDesktopDatabase()

	success("Uninstall complete ✅")
}

/* ===========================
   Helpers
=========================== */

func fileExists(path string) bool {
	_, err := os.Lstat(path)
	return err == nil
}

func removeIfExists(path string) {
	if fileExists(path) {
		info("Removing existing: " + path)
		removeFile(path)
	}
}

/* ===========================
   Desktop Entry
=========================== */

func createDesktopEntry(baseDir string) {
	desktopDir := filepath.Join(
		os.Getenv("HOME"),
		".local/share/applications",
	)

	os.MkdirAll(desktopDir, 0755)

	iconPath := filepath.Join(baseDir, "bin/ssh-terminal.png")
	if !fileExists(iconPath) {
		iconPath = ""
	}

	desktopContent := fmt.Sprintf(`[Desktop Entry]
Version=1.0
Type=Application
Name=SSHX
Comment=SSH GUI Manager for QEMU / VMs
Exec=sshx-gui
Icon=%s
Terminal=false
Categories=System;Network;
StartupNotify=true
Path=%s
`, iconPath, baseDir)

	desktopFile := filepath.Join(desktopDir, "sshx-gui.desktop")

	if err := os.WriteFile(desktopFile, []byte(desktopContent), 0755); err != nil {
		fail("Failed creating desktop entry: " + err.Error())
	}

	success("Desktop entry created → " + desktopFile)
}

func updateDesktopDatabase() {
	desktopDir := filepath.Join(
		os.Getenv("HOME"),
		".local/share/applications",
	)
	exec.Command("update-desktop-database", desktopDir).Run()
}
