package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

func main() {
	for {
		if checkAuth() {
			break
		}
	}
}

func checkAuth() bool {
	fmt.Println("🔍 Checking GitHub SSH Authentication...")

	cmd := exec.Command("ssh", "-T", "git@github.com")
	output, _ := cmd.CombinedOutput()

	outStr := string(output)

	if strings.Contains(outStr, "successfully authenticated") {
		fmt.Println("✅ Success! You are now authenticated with GitHub.")
		return true
	}

	fmt.Println("❌ SSH Authentication failed.")
	fmt.Println("💡 Would you like to run 'sshx-key' to generate and copy your key? (y/n)")

	reader := bufio.NewReader(os.Stdin)
	input, _ := reader.ReadString('\n')
	input = strings.TrimSpace(strings.ToLower(input))

	if input != "y" && input != "yes" {
		fmt.Println("👋 Exiting setup.")
		os.Exit(1)
	}

	fmt.Print("📧 Enter your GitHub Email: ")
	email, _ := reader.ReadString('\n')
	email = strings.TrimSpace(email)

	runKeySetup(email)

	fmt.Println("\n--------------------------------------------------")
	fmt.Println("📢 Action Required:")
	fmt.Println("1. Go to: https://github.com/settings/keys")
	fmt.Println("2. Click 'New SSH Key' and paste your key.")
	fmt.Println("--------------------------------------------------")

	fmt.Println("\n⏳ After adding the key to GitHub, press [Enter] to verify connection...")
	reader.ReadString('\n')

	fmt.Println("🔄 Re-verifying connection...")
	time.Sleep(2 * time.Second)

	return false
}

func runKeySetup(email string) {
	keyTool, err := exec.LookPath("sshx-key")
	if err != nil {
		fmt.Println("❌ sshx-key not found in PATH.")
		return
	}

	setupCmd := exec.Command(keyTool, email)
	setupCmd.Stdout = os.Stdout
	setupCmd.Stderr = os.Stderr
	setupCmd.Stdin = os.Stdin
	setupCmd.Env = os.Environ()

	if err := setupCmd.Run(); err != nil {
		fmt.Printf("❌ Error running sshx-key: %v\n", err)
	}
}
