package main

import (
	_ "embed"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
)

//go:embed sshx.sh
var scriptContent string

// Binary Metadata
const (
	CliName    = "sshx"
	Version    = "1.1.0"
	Author     = "Sumit"
	Icon       = "🚀"
	KeyIcon    = "🔑"
	GearIcon   = "⚙️"
)

// ANSI Color Codes
const (
	ColorReset  = "\033[0m"
	ColorCyan   = "\033[36m"
	ColorGreen  = "\033[32m"
	ColorYellow = "\033[33m"
)

func main() {
	// Handle Custom Flags (English)
	if len(os.Args) > 1 {
		switch os.Args[1] {
		case "--version", "-v":
			showVersion()
			return
		case "--info", "-i":
			showInfo()
			return
		case "--help", "-h":
			// We let the bash script handle the main help, 
			// but we can intercept or add binary-specific help here.
		}
	}

	// EXECUTION LOGIC
	tmpDir, err := os.MkdirTemp("", "sshx-wrapper-*")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Could not create runtime environment: %v\n", err)
		os.Exit(1)
	}
	defer os.RemoveAll(tmpDir)

	scriptPath := filepath.Join(tmpDir, "sshx_core.sh")
	err = os.WriteFile(scriptPath, []byte(scriptContent), 0755)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Failed to extract core logic: %v\n", err)
		os.Exit(1)
	}

	// Passing all arguments to the embedded bash script
	cmd := exec.Command("/bin/bash", append([]string{scriptPath}, os.Args[1:]...)...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	cmd.Env = os.Environ()

	err = cmd.Run()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		os.Exit(1)
	}
}

func showVersion() {
	fmt.Printf("%s %s version %s%s\n", Icon, ColorCyan+CliName, Version, ColorReset)
	fmt.Printf("%s OS/Arch: %s/%s\n", GearIcon, runtime.GOOS, runtime.GOARCH)
}

func showInfo() {
	fmt.Printf("%s %s%s - Simple SSH Manager\n", Icon, ColorGreen, CliName, ColorReset)
	fmt.Printf("%s Author: %s\n", KeyIcon, Author)
	fmt.Printf("%s Built with: Go (%s)\n", GearIcon, runtime.Version())
	fmt.Println("--------------------------------------------------")
	fmt.Println("A high-performance binary wrapper for SSH automation.")
}
