package main

import (
	"os"
	"os/exec"
)

/**
 * Project: git-auth Binary Wrapper
 * Author: Sumit
 * Description: High-performance binary to execute git-auth logic.
 */

func main() {
	// We ignore all os.Args to ensure that commands like -v or --help 
	// do not trigger anything other than the core logic.

	// Directly calling the SSH command defined in your script
	cmd := exec.Command("ssh", "-T", "git@github.com")

	// Redirecting standard streams to the terminal
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	// Inherit system environment variables (required for SSH keys)
	cmd.Env = os.Environ()

	// Execute the command
	err := cmd.Run()

	if err != nil {
		// If the command fails, exit with the corresponding error code
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		os.Exit(1)
	}
}
