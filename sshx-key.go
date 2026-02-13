package main

import (
	_ "embed"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// ---------------- Embed the bash script ----------------
//go:embed sshx-key
var sshScript []byte

func main() {
	tmpDir, err := os.MkdirTemp("", "sshx-key-*")
	if err != nil {
		fmt.Printf("❌ Failed to create temp dir: %v\n", err)
		os.Exit(1)
	}
	defer os.RemoveAll(tmpDir)

	tmpScript := filepath.Join(tmpDir, "sshx-key-exec.sh")
	
	err = os.WriteFile(tmpScript, sshScript, 0755) 
	if err != nil {
		fmt.Printf("❌ Failed to write embedded script: %v\n", err)
		os.Exit(1)
	}

	if len(os.Args) < 2 {
		fmt.Println("🚀 SSHX Key Setup Tool")
		fmt.Println("Usage: sshx-key your_email@example.com")
		os.Exit(1)
	}

	email := os.Args[1]

	bashPath, err := exec.LookPath("bash")
	if err != nil {
		bashPath = "/bin/bash"
	}

	cmd := exec.Command(bashPath, tmpScript, email)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	cmd.Env = os.Environ()

	if err := cmd.Run(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		fmt.Printf("❌ Failed to execute SSH key setup: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ Action completed successfully!")
}
