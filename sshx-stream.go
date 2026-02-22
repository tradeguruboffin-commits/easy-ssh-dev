package main

import (
	"fmt"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

func fatal(msg string, err error) {
	if err != nil {
		fmt.Printf("❌ %s: %v\n", msg, err)
	} else {
		fmt.Printf("❌ %s\n", msg)
	}
	os.Exit(1)
}

func main() {
	if len(os.Args) != 5 {
		fmt.Println("Usage:")
		fmt.Println("  sshx-stream push user@host:port <local_path> <remote_dir>")
		fmt.Println("  sshx-stream pull user@host:port <remote_path> <local_dir>")
		os.Exit(1)
	}

	mode := os.Args[1]
	target := os.Args[2]
	src := os.Args[3]
	dst := os.Args[4]

	user, host, port := parseTarget(target)

	switch mode {
	case "push":
		push(user, host, port, src, dst)
	case "pull":
		pull(user, host, port, src, dst)
	default:
		fatal("Mode must be push or pull", nil)
	}
}

func parseTarget(target string) (string, string, string) {
	atIdx := strings.LastIndex(target, "@")
	if atIdx == -1 {
		fatal("Invalid target format. Missing @", nil)
	}

	user := target[:atIdx]
	hostPort := target[atIdx+1:]

	var host, port string

	if strings.HasPrefix(hostPort, "[") {
		endBracket := strings.Index(hostPort, "]")
		if endBracket == -1 {
			fatal("Invalid IPv6 format in target", nil)
		}
		host = hostPort[1:endBracket]
		if len(hostPort) <= endBracket+2 || hostPort[endBracket+1] != ':' {
			fatal("Port missing after IPv6 brackets", nil)
		}
		port = hostPort[endBracket+2:]
	} else {
		colonIdx := strings.LastIndex(hostPort, ":")
		if colonIdx == -1 {
			fatal("Invalid target format. Missing :port", nil)
		}
		host = hostPort[:colonIdx]
		port = hostPort[colonIdx+1:]
	}

	if net.ParseIP(host) == nil && host == "" {
		fatal("Host is empty", nil)
	}

	if port == "" {
		fatal("Port is empty", nil)
	}

	p, err := strconv.Atoi(port)
	if err != nil || p < 1 || p > 65535 {
		fatal("Invalid port number", nil)
	}

	return user, host, port
}

func push(user, host, port, localPath, remoteDir string) {
	absLocal, err := filepath.Abs(localPath)
	if err != nil {
		fatal("Cannot resolve local path", err)
	}

	remoteDir = strings.TrimRight(remoteDir, "/")

	fmt.Printf("⬆ Pushing %s → %s@%s:%s\n", absLocal, user, host, remoteDir)

	cmd := exec.Command(
		"scp",
		"-P", port,
		"-r",
		absLocal,
		fmt.Sprintf("%s@%s:%s", user, host, remoteDir),
	)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		fatal("Push failed. Check remote directory, permissions, network or SCP", err)
	}

	fmt.Println("✅ Push completed")
}

func pull(user, host, port, remotePath, localDir string) {
	absLocal, err := filepath.Abs(localDir)
	if err != nil {
		fatal("Cannot resolve local directory", err)
	}

	remotePath = strings.TrimRight(remotePath, "/")

	fmt.Printf("⬇ Pulling %s@%s:%s → %s\n", user, host, remotePath, absLocal)

	if err := os.MkdirAll(absLocal, 0755); err != nil {
		fatal("Cannot create local directory. Check permissions", err)
	}

	cmd := exec.Command(
		"scp",
		"-P", port,
		"-r",
		fmt.Sprintf("%s@%s:%s", user, host, remotePath),
		absLocal,
	)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		fatal("Pull failed. Check remote directory, permissions, network or SCP", err)
	}

	fmt.Println("✅ Pull completed")
}
