package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func main() {
	// ---------------- Executable Path Detect ----------------
	execPath, err := os.Executable()
	if err != nil {
		fmt.Printf("❌ Error detecting executable path: %v\n", err)
		os.Exit(1)
	}

	currDir := filepath.Dir(execPath)
	scriptPath := filepath.Join(currDir, "initialization")

	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		scriptPath = filepath.Join(filepath.Dir(currDir), "initialization")
	}

	// ---------------- Initialization Validation ----------------
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		fmt.Printf("❌ Critical Error: Initialization script not found at %s\n", scriptPath)
		fmt.Println("Please run this from the project root or ensure the script is present.")
		os.Exit(1)
	}

	// ---------------- Argument Check ----------------
	if len(os.Args) < 2 {
		fmt.Println("🚀 SSHX Initialization Wrapper")
		fmt.Println("Usage:")
		fmt.Println("  sshx-dev install")
		fmt.Println("  sshx-dev uninstall")
		os.Exit(1)
	}

	action := os.Args[1]

	// ---------------- Bash Command Execution ----------------
	bashPath, err := exec.LookPath("bash")
	if err != nil {
		// fallback
		bashPath = "/bin/bash"
	}

	cmd := exec.Command(bashPath, scriptPath, action)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	cmd.Env = os.Environ() // Environment forward

	// Run the command
	if err := cmd.Run(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			// exit code forward
			os.Exit(exitErr.ExitCode())
		}
		fmt.Printf("❌ Failed to execute initialization script: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ Action completed successfully!")
}
