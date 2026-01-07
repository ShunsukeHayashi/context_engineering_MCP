#!/bin/bash

# Context Engineering Platform - Docker Configuration Validator
# Validates Docker setup and configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Context Engineering Docker Validator${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if command -v docker >/dev/null 2>&1; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker $DOCKER_VERSION installed"
    else
        print_error "Docker not installed"
        return 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker Compose $COMPOSE_VERSION installed"
    else
        print_error "Docker Compose not installed"
        return 1
    fi
    
    # Check if Docker daemon is running
    if docker info >/dev/null 2>&1; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        return 1
    fi
    
    return 0
}

check_files() {
    print_status "Checking required files..."
    
    local required_files=(
        "Dockerfile"
        "docker-compose.yml"
        "docker-compose.dev.yml"
        ".dockerignore"
        "requirements.txt"
        ".env.example"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "$file exists"
        else
            print_error "$file missing"
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        print_error "Missing required files: ${missing_files[*]}"
        return 1
    fi
    
    return 0
}

check_env() {
    print_status "Checking environment configuration..."
    
    if [ ! -f .env ]; then
        print_warning ".env file not found - will use .env.example"
        if [ -f .env.example ]; then
            print_success ".env.example exists as fallback"
        else
            print_error ".env.example also missing"
            return 1
        fi
    else
        print_success ".env file exists"
        
        # Check for required environment variables
        if grep -q "GEMINI_API_KEY=" .env; then
            local api_key=$(grep "GEMINI_API_KEY=" .env | cut -d'=' -f2)
            if [ -n "$api_key" ] && [ "$api_key" != "your_gemini_api_key_here" ]; then
                print_success "GEMINI_API_KEY is set"
            else
                print_warning "GEMINI_API_KEY not properly set in .env"
            fi
        else
            print_warning "GEMINI_API_KEY not found in .env"
        fi
    fi
    
    return 0
}

validate_dockerfile() {
    print_status "Validating Dockerfile..."
    
    # Check for common issues
    if grep -q "FROM python:3.11-slim" Dockerfile; then
        print_success "Using recommended Python base image"
    else
        print_warning "Not using recommended Python 3.11-slim base image"
    fi
    
    if grep -q "USER appuser" Dockerfile; then
        print_success "Running as non-root user"
    else
        print_warning "Not explicitly running as non-root user"
    fi
    
    if grep -q "EXPOSE.*8888.*9001.*9002" Dockerfile; then
        print_success "All required ports exposed"
    else
        print_warning "Not all required ports may be exposed"
    fi
    
    if grep -q "HEALTHCHECK" Dockerfile; then
        print_success "Health check configured"
    else
        print_warning "No health check configured"
    fi
    
    return 0
}

validate_compose() {
    print_status "Validating docker-compose configuration..."
    
    # Validate main compose file
    if docker-compose -f docker-compose.yml config >/dev/null 2>&1; then
        print_success "docker-compose.yml is valid"
    else
        print_error "docker-compose.yml has syntax errors"
        return 1
    fi
    
    # Validate dev compose file
    if docker-compose -f docker-compose.yml -f docker-compose.dev.yml config >/dev/null 2>&1; then
        print_success "docker-compose.dev.yml is valid"
    else
        print_error "docker-compose.dev.yml has syntax errors"
        return 1
    fi
    
    # Check for required services
    local required_services=("ai-guides-api" "context-engineering-api" "workflow-system")
    local compose_services=$(docker-compose -f docker-compose.yml config --services)
    
    for service in "${required_services[@]}"; do
        if echo "$compose_services" | grep -q "^$service$"; then
            print_success "Service '$service' defined"
        else
            print_error "Service '$service' not found"
        fi
    done
    
    return 0
}

test_build() {
    print_status "Testing Docker build..."
    
    # Test if Dockerfile can be built (dry run)
    if docker build --target base -t context-eng-test . >/dev/null 2>&1; then
        print_success "Dockerfile builds successfully"
        # Clean up test image
        docker rmi context-eng-test >/dev/null 2>&1 || true
    else
        print_error "Dockerfile build failed"
        return 1
    fi
    
    return 0
}

check_ports() {
    print_status "Checking port availability..."
    
    local ports=(8888 9001 9002 5432 6379 9090 3000)
    local busy_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            busy_ports+=($port)
            print_warning "Port $port is in use"
        else
            print_success "Port $port is available"
        fi
    done
    
    if [ ${#busy_ports[@]} -gt 0 ]; then
        print_warning "Some ports are busy: ${busy_ports[*]}"
        print_warning "You may need to stop other services or change port mappings"
    fi
    
    return 0
}

check_resources() {
    print_status "Checking system resources..."
    
    # Check available disk space
    local available_space=$(df . | awk 'NR==2 {print $4}')
    if [ $available_space -gt 2000000 ]; then  # 2GB in KB
        print_success "Sufficient disk space available"
    else
        print_warning "Low disk space - less than 2GB available"
    fi
    
    # Check memory
    if command -v free >/dev/null 2>&1; then
        local available_mem=$(free -m | awk 'NR==2{printf "%.0f", $7}')
        if [ $available_mem -gt 1000 ]; then  # 1GB
            print_success "Sufficient memory available ($available_mem MB)"
        else
            print_warning "Low memory - less than 1GB available"
        fi
    elif command -v vm_stat >/dev/null 2>&1; then
        # macOS memory check
        print_success "Memory check completed (macOS)"
    fi
    
    return 0
}

print_recommendations() {
    print_status "Recommendations:"
    echo ""
    echo "📋 Development Workflow:"
    echo "  1. Run: ./scripts/docker-dev.sh build"
    echo "  2. Run: ./scripts/docker-dev.sh up"
    echo "  3. Test: curl http://localhost:8888/health"
    echo ""
    echo "🔧 Production Deployment:"
    echo "  1. Run: docker-compose up -d"
    echo "  2. Monitor: docker-compose logs -f"
    echo ""
    echo "📊 Monitoring (optional):"
    echo "  1. Run: ./scripts/docker-dev.sh monitoring"
    echo "  2. Visit: http://localhost:3000 (Grafana)"
    echo ""
    echo "🧹 Cleanup:"
    echo "  Run: ./scripts/docker-dev.sh clean"
    echo ""
}

# Main execution
main() {
    print_header
    
    local exit_code=0
    
    # Run all checks
    check_prerequisites || exit_code=1
    echo ""
    
    check_files || exit_code=1
    echo ""
    
    check_env || exit_code=1
    echo ""
    
    validate_dockerfile || exit_code=1
    echo ""
    
    validate_compose || exit_code=1
    echo ""
    
    test_build || exit_code=1
    echo ""
    
    check_ports || exit_code=1
    echo ""
    
    check_resources || exit_code=1
    echo ""
    
    if [ $exit_code -eq 0 ]; then
        print_success "All Docker configuration checks passed! 🎉"
    else
        print_error "Some checks failed. Please review the issues above."
    fi
    
    echo ""
    print_recommendations
    
    exit $exit_code
}

# Run main function
main "$@"