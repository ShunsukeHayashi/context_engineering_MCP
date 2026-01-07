#!/bin/bash

# Context Engineering Platform - Development Docker Management
# Provides easy commands for Docker development workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
🐳 Context Engineering Platform - Docker Development Commands

Usage: ./scripts/docker-dev.sh [COMMAND] [OPTIONS]

Commands:
  build           Build all development images
  up              Start all development services
  down            Stop all services
  restart         Restart all services
  logs [service]  Show logs (optionally for specific service)
  shell [service] Open shell in running container
  test            Run tests in container
  clean           Clean up containers, images, and volumes
  status          Show status of all services
  monitoring      Start with monitoring stack (Prometheus + Grafana)
  db              Database management commands

Examples:
  ./scripts/docker-dev.sh up
  ./scripts/docker-dev.sh logs context-engineering-api
  ./scripts/docker-dev.sh shell ai-guides-api
  ./scripts/docker-dev.sh clean
  ./scripts/docker-dev.sh monitoring

Environment:
  Set GEMINI_API_KEY in .env file before running
EOF
}

check_env() {
    if [ ! -f .env ]; then
        print_warning "No .env file found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please edit .env file and add your GEMINI_API_KEY"
        else
            print_error ".env.example not found!"
            exit 1
        fi
    fi
    
    # Source environment variables
    set -a
    source .env
    set +a
    
    if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
        print_error "GEMINI_API_KEY not set in .env file!"
        print_warning "Get your API key from: https://makersuite.google.com/app/apikey"
        exit 1
    fi
}

docker_build() {
    print_status "Building development images..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
    print_success "Build completed!"
}

docker_up() {
    print_status "Starting development services..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_services
    
    print_success "Development environment is ready!"
    print_status "Access points:"
    echo "  • AI Guides API:        http://localhost:8888"
    echo "  • AI Guides Docs:       http://localhost:8888/docs"
    echo "  • Context Engineering:  http://localhost:9001"
    echo "  • Context Eng Docs:     http://localhost:9001/docs"
    echo "  • Workflow System:      http://localhost:9002"
    echo "  • Redis:                localhost:6379"
    echo "  • PostgreSQL:           localhost:5432"
}

docker_up_monitoring() {
    print_status "Starting development services with monitoring..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile monitoring up -d
    
    print_status "Waiting for services to be ready..."
    sleep 15
    
    print_success "Development environment with monitoring is ready!"
    print_status "Access points:"
    echo "  • All previous services plus:"
    echo "  • Prometheus:           http://localhost:9090"
    echo "  • Grafana:              http://localhost:3000 (admin/admin123)"
}

docker_down() {
    print_status "Stopping all services..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile monitoring down
    print_success "All services stopped!"
}

docker_restart() {
    print_status "Restarting services..."
    docker_down
    sleep 2
    docker_up
}

docker_logs() {
    local service=$1
    if [ -z "$service" ]; then
        print_status "Showing logs for all services..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
    else
        print_status "Showing logs for $service..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f "$service"
    fi
}

docker_shell() {
    local service=${1:-ai-guides-api}
    print_status "Opening shell in $service..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec "$service" /bin/bash
}

docker_test() {
    print_status "Running tests in container..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec ai-guides-api pytest
}

docker_clean() {
    print_warning "This will remove all containers, images, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up Docker resources..."
        
        # Stop and remove containers
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile monitoring down -v
        
        # Remove images
        docker images | grep context-eng | awk '{print $3}' | xargs -r docker rmi -f
        
        # Remove volumes
        docker volume ls | grep context | awk '{print $2}' | xargs -r docker volume rm
        
        # Remove networks
        docker network ls | grep context-engineering | awk '{print $1}' | xargs -r docker network rm
        
        print_success "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

docker_status() {
    print_status "Service Status:"
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
    
    echo ""
    print_status "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

check_services() {
    local services=("ai-guides-api:8888/health" "context-engineering-api:9001/api/stats")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name endpoint <<< "$service"
        if curl -f "http://localhost:$endpoint" >/dev/null 2>&1; then
            print_success "$name is healthy"
        else
            print_warning "$name is not responding yet"
        fi
    done
}

database_commands() {
    case ${2:-help} in
        "reset")
            print_status "Resetting database..."
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres psql -U dev_user -d context_engineering -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
            print_success "Database reset!"
            ;;
        "backup")
            print_status "Creating database backup..."
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres pg_dump -U dev_user context_engineering > "backup-$(date +%Y%m%d-%H%M%S).sql"
            print_success "Backup created!"
            ;;
        "shell")
            print_status "Opening database shell..."
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres psql -U dev_user -d context_engineering
            ;;
        *)
            echo "Database commands: reset, backup, shell"
            ;;
    esac
}

# Main command processing
case ${1:-help} in
    "build")
        check_env
        docker_build
        ;;
    "up")
        check_env
        docker_up
        ;;
    "down")
        docker_down
        ;;
    "restart")
        check_env
        docker_restart
        ;;
    "logs")
        docker_logs "$2"
        ;;
    "shell")
        docker_shell "$2"
        ;;
    "test")
        docker_test
        ;;
    "clean")
        docker_clean
        ;;
    "status")
        docker_status
        ;;
    "monitoring")
        check_env
        docker_up_monitoring
        ;;
    "db")
        database_commands "$@"
        ;;
    "help"|*)
        show_help
        ;;
esac