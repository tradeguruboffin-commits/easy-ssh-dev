package main

import (
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"strings"
)

const (
	GREEN  = "\033[0;32m"
	YELLOW = "\033[1;33m"
	RED    = "\033[0;31m"
	BLUE   = "\033[0;34m"
	NC     = "\033[0m"
)

func die(msg string) {
	fmt.Println(RED + "❌ " + msg + NC)
	os.Exit(1)
}

func commandExists(name string) bool {
	_, err := exec.LookPath(name)
	return err == nil
}

func ensureSSHDir(path string) {
	os.MkdirAll(path, 0700)
	os.Chmod(path, 0700)
}

func generateKey(email, keyPath string) {
	if _, err := os.Stat(keyPath); os.IsNotExist(err) {
		fmt.Println(GREEN + "🔑 Generating new SSH key..." + NC)

		cmd := exec.Command("ssh-keygen",
			"-t", "ed25519",
			"-C", email,
			"-f", keyPath,
			"-N", "")

		cmd.Stdout = nil
		cmd.Stderr = nil

		if err := cmd.Run(); err != nil {
			die("Failed to generate SSH key")
		}

		fmt.Println(GREEN + "✓ SSH key generated at " + keyPath + NC)
		fmt.Println()
	} else {
		fmt.Println(YELLOW + "⚠ SSH key already exists at " + keyPath + NC)
		fmt.Println("✓ Using existing key")
		fmt.Println()
	}
}

func ensureAgent() {
	user, _ := user.Current()

	check := exec.Command("pgrep", "-u", user.Username, "ssh-agent")
	if err := check.Run(); err != nil {

		fmt.Println(GREEN + "🔄 Starting SSH agent..." + NC)

		cmd := exec.Command("ssh-agent", "-s")
		out, err := cmd.Output()
		if err != nil {
			die("Failed to start ssh-agent")
		}

		// export environment variables
		lines := strings.Split(string(out), "\n")
		for _, line := range lines {
			if strings.Contains(line, "SSH_AUTH_SOCK") ||
				strings.Contains(line, "SSH_AGENT_PID") {

				parts := strings.Split(line, ";")[0]
				env := strings.Split(parts, "=")
				if len(env) == 2 {
					os.Setenv(env[0], env[1])
				}
			}
		}

		fmt.Println(GREEN + "✓ SSH agent started" + NC)
		fmt.Println()
	} else {
		fmt.Println(YELLOW + "⚠ SSH agent already running" + NC)
		fmt.Println()
	}
}

func addKey(keyPath string) {
	fmt.Println(GREEN + "➕ Adding key to SSH agent..." + NC)

	cmd := exec.Command("ssh-add", keyPath)
	cmd.Stdout = nil
	cmd.Stderr = nil

	if err := cmd.Run(); err != nil {
		die("Failed to add SSH key to agent")
	}

	fmt.Println(GREEN + "✓ Key added to SSH agent" + NC)
	fmt.Println()
}

func copyToClipboard(pubKey string) {
	copied := false

	if commandExists("xclip") {
		cmd := exec.Command("xclip", "-selection", "clipboard")
		cmd.Stdin = strings.NewReader(pubKey)
		cmd.Run()
		copied = true
	} else if commandExists("pbcopy") {
		cmd := exec.Command("pbcopy")
		cmd.Stdin = strings.NewReader(pubKey)
		cmd.Run()
		copied = true
	} else if commandExists("clip.exe") {
		cmd := exec.Command("clip.exe")
		cmd.Stdin = strings.NewReader(pubKey)
		cmd.Run()
		copied = true
	}

	if copied {
		fmt.Println(GREEN + "✓ Public key copied to clipboard" + NC)
		fmt.Println()
	} else {
		fmt.Println(YELLOW + "⚠ Could not copy to clipboard automatically" + NC)
		fmt.Println()
	}
}

func showGitHubInstructions(pubKey string) {
	fmt.Println(BLUE + "Next Steps:" + NC)
	fmt.Println("1. Go to: https://github.com/settings/keys")
	fmt.Println("2. Click 'New SSH key'")
	fmt.Println("3. Paste the public key below (or copied to clipboard)")
	fmt.Println("4. Give it a title and click 'Add SSH key'")
	fmt.Println()

	fmt.Println(BLUE + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" + NC)
	fmt.Println(pubKey)
	fmt.Println(BLUE + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" + NC)
	fmt.Println()

	fmt.Println(YELLOW + "To test your connection:" + NC)
	fmt.Println("ssh -T git@github.com")
	fmt.Println()
}

func main() {

	if len(os.Args) < 2 {
		die("Usage:\n  sshx-key setup your@email.com\n  sshx-key local your@email.com")
	}

	mode := "setup"
	email := ""

	if os.Args[1] == "local" {
		mode = "local"
		if len(os.Args) < 3 {
			die("Email required")
		}
		email = os.Args[2]
	} else {
		email = os.Args[1]
	}

	fmt.Println(GREEN + "🚀 Starting SSH setup for: " + email + NC)
	fmt.Println()

	currentUser, _ := user.Current()
	home := currentUser.HomeDir

	sshDir := filepath.Join(home, ".ssh")
	sshKey := filepath.Join(sshDir, "id_ed25519")

	ensureSSHDir(sshDir)
	generateKey(email, sshKey)
	ensureAgent()
	addKey(sshKey)

	pubBytes, err := ioutil.ReadFile(sshKey + ".pub")
	if err != nil {
		die("Could not read public key")
	}

	pubKey := strings.TrimSpace(string(pubBytes))
	copyToClipboard(pubKey)

	if mode == "setup" {
		showGitHubInstructions(pubKey)
		fmt.Println(GREEN + "✅ GitHub SSH Setup Completed Successfully!" + NC)
	} else {
		fmt.Println(BLUE + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" + NC)
		fmt.Println(pubKey)
		fmt.Println(BLUE + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" + NC)
		fmt.Println()
		fmt.Println(GREEN + "✅ Local SSH key setup completed!" + NC)
	}
}
