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
	"gui/lib/sshx-cpy",
	"gui/lib/sshx-reset",
	"gui/lib/git-auth",
	"gui/sshx-gui",
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

func info(msg string) {
	fmt.Println(Blue + Bold + msg + Reset)
}

func success(msg string) {
	fmt.Println(Green + "✔ " + msg + Reset)
}

func fail(msg string) {
	fmt.Println(Red + "✘ " + msg + Reset)
	os.Exit(1)
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
   Project Root Detection
=========================== */

func projectRoot() string {
	exe, err := os.Executable()
	if err != nil {
		log.Fatal("Cannot detect executable path:", err)
	}

	exePath, _ := filepath.EvalSymlinks(exe)
	dir := filepath.Dir(exePath)

	// If binary is inside /usr/local/bin (symlink install case)
	if filepath.Base(dir) == "bin" {
		return filepath.Dir(dir)
	}

	return dir
}

/* ===========================
   Install
=========================== */

func install() {
	info("Installing esey-ssh-dev...")

	baseDir := projectRoot()
	targetDir := "/usr/local/bin"

	for _, bin := range binaries {
		src := filepath.Join(baseDir, bin)
		name := filepath.Base(bin)
		dest := filepath.Join(targetDir, name)

		if _, err := os.Stat(src); os.IsNotExist(err) {
			fail("Missing binary: " + src)
		}

		removeIfExists(dest)

		cmd := exec.Command("sudo", "ln", "-s", src, dest)
		if err := cmd.Run(); err != nil {
			fail("Failed linking " + name + ": " + err.Error())
		}

		success(name + " linked → " + dest)
	}

	createDesktopEntry(baseDir)
	updateDesktopDatabase()

	success("Installation complete 🎉")
}

/* ===========================
   Uninstall
=========================== */

func uninstall() {
	info("Uninstalling esey-ssh-dev...")

	targetDir := "/usr/local/bin"

	for _, bin := range binaries {
		name := filepath.Base(bin)
		dest := filepath.Join(targetDir, name)

		if fileExists(dest) {
			exec.Command("sudo", "rm", "-f", dest).Run()
			success(name + " removed")
		}
	}

	desktopFile := filepath.Join(
		os.Getenv("HOME"),
		".local/share/applications/sshx-gui.desktop",
	)

	if fileExists(desktopFile) {
		os.Remove(desktopFile)
		success("Desktop entry removed")
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
		exec.Command("sudo", "rm", "-rf", path).Run()
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
