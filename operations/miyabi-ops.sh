#!/bin/bash

# Miyabi Operations Script for Context Engineering MCP
# Autonomous development operations using miyabi

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║     Context Engineering MCP - Miyabi Operations           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_help() {
    print_header
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  run       - Run miyabi autonomous development"
    echo "  status    - Check miyabi status"
    echo "  doctor    - Run miyabi health check"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 run"
    echo "  $0 doctor"
    echo ""
}

check_miyabi() {
    if ! command -v npx &> /dev/null; then
        echo -e "${RED}Error: npx is not installed. Please install Node.js 18+${NC}"
        exit 1
    fi
}

run_miyabi() {
    check_miyabi
    echo -e "${GREEN}Starting Miyabi autonomous development...${NC}"
    npx miyabi run
}

status_miyabi() {
    check_miyabi
    echo -e "${BLUE}Checking Miyabi status...${NC}"
    npx miyabi status
}

doctor_miyabi() {
    check_miyabi
    echo -e "${YELLOW}Running Miyabi health check...${NC}"
    npx miyabi doctor
}

# Main
case "${1:-help}" in
    run)
        run_miyabi
        ;;
    status)
        status_miyabi
        ;;
    doctor)
        doctor_miyabi
        ;;
    help|--help|-h)
        print_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        print_help
        exit 1
        ;;
esac
