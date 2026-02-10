#!/bin/bash

# Configuration
BINARY_NAME="sshx"
SOURCE_FILE="main.go"
SHELL_SCRIPT="sshx.sh"

# Colors for professional output
GREEN="\e[32m"; BLUE="\e[34m"; RED="\e[31m"; NC="\e[0m"; BOLD="\e[1m"

echo -e "${BLUE}${BOLD}📦 Initializing Build Process...${NC}"

# 1. Validation: Check if required files exist
if [ ! -f "$SOURCE_FILE" ] || [ ! -f "$SHELL_SCRIPT" ]; then
    echo -e "${RED}❌ Error: main.go or sshx.sh not found in the current directory!${NC}"
    exit 1
fi

# 2. Go Module Setup
if [ ! -f "go.mod" ]; then
    echo -e "${BLUE}⚙️ Initializing Go module...${NC}"
    go mod init github.com/sumit/sshx &>/dev/null
    go mod tidy &>/dev/null
fi

# 3. Build ARM64 Binary
echo -e "${BLUE}🔨 Compiling ARM64 binary (Optimized)...${NC}"
# -s -w removes symbol tables and debug info to reduce size
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -ldflags="-s -w" -o "${BINARY_NAME}-arm64" "$SOURCE_FILE"

# 4. Result Check
if [ -f "${BINARY_NAME}-arm64" ]; then
    echo -e "\n${GREEN}${BOLD}✅ BUILD SUCCESSFUL!${NC}"
    echo -e "----------------------------------------"
    
    # 5. Professional Metrics
    ORIG_SIZE=$(du -h "$SHELL_SCRIPT" | cut -f1)
    BIN_SIZE=$(du -h "${BINARY_NAME}-arm64" | cut -f1)
    
    echo -e "📊 ${BOLD}Build Summary:${NC}"
    echo -e "   Platform:  Linux ARM64"
    echo -e "   Original:  $ORIG_SIZE (Shell Script)"
    echo -e "   Binary:    $BIN_SIZE (Compressed Executable)"
    echo -e "----------------------------------------"
    
    echo -e "🧪 ${BOLD}Quick Test:${NC}"
    echo -e "   ./${BINARY_NAME}-arm64 --version"
    echo -e "   ./${BINARY_NAME}-arm64 --info"
    
    echo -e "\n📦 ${BOLD}Deployment:${NC}"
    echo -e "   sudo mv ${BINARY_NAME}-arm64 /usr/local/bin/${BINARY_NAME}"
    echo -e "   sudo chmod +x /usr/local/bin/${BINARY_NAME}"
    echo "----------------------------------------"
else
    echo -e "${RED}❌ Build failed! Please check your Go installation.${NC}"
    exit 1
fi
