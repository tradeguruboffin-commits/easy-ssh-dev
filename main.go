package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const VERSION = "1.1"

var (
	home, _ = os.UserHomeDir()
	cache   = filepath.Join(home, ".ssh", "sshx.json")
	key     = filepath.Join(home, ".ssh", "id_ed25519")

	GREEN  = "\033[32m"
	RED    = "\033[31m"
	YELLOW = "\033[33m"
	BLUE   = "\033[34m"
	NC     = "\033[0m"
)

type Entry struct {
	User string `json:"user"`
	Host string `json:"host"`
	Port int    `json:"port"`
}

func die(msg string) {
	fmt.Println(RED + "❌ " + msg + NC)
	os.Exit(1)
}
func ok(msg string)   { fmt.Println(GREEN + "✅ " + msg + NC) }
func warn(msg string) { fmt.Println(YELLOW + "⚠️ " + msg + NC) }
func info(msg string) { fmt.Println(BLUE + "ℹ️ " + msg + NC) }

func need(cmd string) {
	if _, err := exec.LookPath(cmd); err != nil {
		die(cmd + " not installed")
	}
}

func initSSH() {
	os.MkdirAll(filepath.Join(home, ".ssh"), 0700)
	os.Chmod(filepath.Join(home, ".ssh"), 0700)

	need("ssh")

	if _, err := os.Stat(cache); os.IsNotExist(err) {
		if err := os.WriteFile(cache, []byte("{}"), 0644); err != nil {
			die("Failed to create cache file")
		}
	}

	data, _ := os.ReadFile(cache)
	var tmp map[string]Entry
	if json.Unmarshal(data, &tmp) != nil {
		warn("Cache corrupted — resetting")
		os.WriteFile(cache, []byte("{}"), 0644)
	}

	if _, err := os.Stat(key); os.IsNotExist(err) {
		info("Generating SSH key...")
		cmd := exec.Command("ssh-keygen", "-t", "ed25519", "-f", key, "-N", "")
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err != nil {
			die("Keygen failed")
		}
	}

	if _, err := os.Stat(key + ".pub"); err != nil {
		die("Public key missing")
	}

	os.Chmod(key, 0600)
	ok("Key permission fixed (600)")
}

func loadCache() map[string]Entry {
	data, _ := os.ReadFile(cache)
	var m map[string]Entry
	json.Unmarshal(data, &m)
	if m == nil {
		m = make(map[string]Entry)
	}
	return m
}

func saveCache(m map[string]Entry) {
	data, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		die("Failed to marshal cache")
	}

	if err := os.WriteFile(cache+".tmp", data, 0644); err != nil {
		die("Failed to write cache")
	}

	if err := os.Rename(cache+".tmp", cache); err != nil {
		die("Failed to rename cache file")
	}
}

func parse(input string) (string, string, int) {
	ipv6 := regexp.MustCompile(`^([^@]+)@\[(.+)\]:(\d+)$`)
	ipv4 := regexp.MustCompile(`^([^@]+)@([^:]+):(\d+)$`)

	if m := ipv6.FindStringSubmatch(input); m != nil {
		p, err := strconv.Atoi(m[3])
		if err != nil {
			die("Invalid port number")
		}
		return m[1], m[2], p
	}
	if m := ipv4.FindStringSubmatch(input); m != nil {
		p, err := strconv.Atoi(m[3])
		if err != nil {
			die("Invalid port number")
		}
		return m[1], m[2], p
	}
	die("Invalid format. Use: user@ip:port or user@[ipv6]:port")
	return "", "", 0
}

func execSSH(user, host string, port int) {
	sshHost := host
	if strings.Contains(host, ":") {
		sshHost = "[" + host + "]"
	}

	binary, _ := exec.LookPath("ssh")
	args := []string{"ssh", "-p", strconv.Itoa(port), user + "@" + sshHost}

	info("Connecting to " + user + "@" + host + ":" + strconv.Itoa(port) + " …")
	syscall.Exec(binary, args, os.Environ())
}

func connect(user, host string, port int) {
	m := loadCache()
	keyStr := fmt.Sprintf("%s@%s:%d", user, host, port)

	if _, exists := m[keyStr]; !exists {

		info("First time connecting — testing connection...")

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		test := exec.CommandContext(ctx,
			"ssh",
			"-o", "ConnectTimeout=5",
			"-p", strconv.Itoa(port),
			user+"@"+host,
			"exit")

		if err := test.Run(); err != nil {
			warn("Connection test failed — host not added to cache")
			return
		}

		ok("Connection test successful")

		copy := exec.Command("ssh-copy-id",
			"-i", key+".pub",
			"-o", "StrictHostKeyChecking=no",
			"-p", strconv.Itoa(port),
			user+"@"+host)

		copy.Stdin = os.Stdin
		copy.Stdout = os.Stdout
		copy.Stderr = os.Stderr

		if err := copy.Run(); err != nil {
			warn("Key copy failed — host not added to cache")
			return
		}

		ok("Key copied successfully")

		m[keyStr] = Entry{user, host, port}
		saveCache(m)
		ok("Host registered")
	}

	execSSH(user, host, port)
}

func remove(user, host string, port int) {
	m := loadCache()
	keyStr := fmt.Sprintf("%s@%s:%d", user, host, port)

	if _, ok := m[keyStr]; !ok {
		die("Entry not found")
	}

	if strings.Contains(host, ":") {
		exec.Command("ssh-keygen", "-R",
			fmt.Sprintf("[%s]:%d", host, port)).Run()
	} else {
		exec.Command("ssh-keygen", "-R",
			fmt.Sprintf("%s:%d", host, port)).Run()
	}

	ok("Removed known_host entry")

	delete(m, keyStr)
	saveCache(m)

	ok("Removed entry from sshx cache")
}

func list() {
	m := loadCache()
	if len(m) == 0 {
		fmt.Println("(empty)")
		return
	}
	for k := range m {
		fmt.Println(k)
	}
}

func fzfMenu() {
	need("fzf")

	m := loadCache()
	if len(m) == 0 {
		fmt.Println("(empty)")
		return
	}

	var sb strings.Builder
	for k := range m {
		sb.WriteString(k + "\n")
	}

	cmd := exec.Command("fzf", "--prompt=SSH > ")
	cmd.Stdin = strings.NewReader(sb.String())

	out, err := cmd.Output()
	if err != nil {
		os.Exit(0)
	}

	selected := strings.TrimSpace(string(out))
	if selected == "" {
		return
	}

	user, host, port := parse(selected)
	connect(user, host, port)
}

func help() {
	fmt.Printf(`sshx v%s — Simple SSH Manager

USAGE:
  sshx user@ip:port
  sshx user@[ipv6]:port
  sshx user@ip:port --remove

OTHER:
  sshx --list
  sshx --menu
  sshx --doctor
  sshx --version | -v
  sshx --help | -h
`, VERSION)
}

func doctor() {
	fmt.Println("sshx v" + VERSION)

	need("ssh")

	if _, err := exec.LookPath("fzf"); err == nil {
		ok("fzf installed")
	} else {
		warn("fzf missing")
	}

	if _, err := os.Stat(key); err == nil {
		ok("SSH key exists")
	} else {
		warn("SSH key missing")
	}
}

func main() {
	initSSH()

	if len(os.Args) == 1 {
		help()
		return
	}

	switch os.Args[1] {
	case "--help", "-h", "help":
		help()
	case "--version", "-v", "version":
		fmt.Println("sshx v" + VERSION)
	case "--list":
		list()
	case "--menu":
		fzfMenu()
	case "--doctor":
		doctor()
	default:
		user, host, port := parse(os.Args[1])
		if len(os.Args) > 2 && os.Args[2] == "--remove" {
			remove(user, host, port)
		} else {
			connect(user, host, port)
		}
	}
}
