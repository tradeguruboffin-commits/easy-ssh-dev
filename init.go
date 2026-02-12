package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func main() {
	// Detect executable location
	execPath, err := os.Executable()
	if err != nil {
		fmt.Println("Error detecting executable path:", err)
		os.Exit(1)
	}

	baseDir := filepath.Dir(filepath.Dir(execPath)) // go from bin/ → project root
	scriptPath := filepath.Join(baseDir, "initialization")

	// Validate script exists
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		fmt.Println("Initialization script not found:", scriptPath)
		os.Exit(1)
	}

	if len(os.Args) < 2 {
		fmt.Println("Usage:")
		fmt.Println("  sshx-cli install")
		fmt.Println("  sshx-cli uninstall")
		os.Exit(1)
	}

	cmd := exec.Command("bash", scriptPath, os.Args[1])
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	err = cmd.Run()
	if err != nil {
		fmt.Println("Execution failed:", err)
		os.Exit(1)
	}
}
