#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to handle errors
handle_error() {
    print_message "Error: \$1" "$RED"
    exit 1
}

# cleanup the containers
cleanup() {
    echo -e "\n${YELLOW}Stopping containers...${NC}"
    docker-compose down
    echo -e "${GREEN}Containers stopped successfully${NC}"
    exit 0
}

# register the cleanup function to be called on the EXIT signal
trap cleanup EXIT SIGINT SIGTERM

# Check Docker installation
if ! command_exists docker; then
    handle_error "Docker is not installed. Please install Docker first."
fi

if ! command_exists docker-compose; then
    handle_error "Docker Compose is not installed. Please install Docker Compose first."
fi

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    print_message "Loading environment variables from .env file..." "$YELLOW"
    export $(grep -v '^#' .env | xargs)
fi

# Script configuration
COMPOSE_FILE="docker-compose.yaml"
CONTAINER_NAME="ky"

# Parse command line arguments
ACTION=${1:-"bash"} # Default to "bash" if no argument provided

# Function to build and start containers
start_containers() {
    # Clean up any existing containers first
    print_message "Cleaning up any existing containers..." "$YELLOW"
    docker-compose -f $COMPOSE_FILE down --remove-orphans 2>/dev/null || true
    
    print_message "Starting containers (will rebuild only if needed)..." "$YELLOW"
    docker-compose -f $COMPOSE_FILE up -d --build || handle_error "Failed to start containers"
    
    # Wait for containers to be ready
    print_message "Waiting for containers to be ready..." "$YELLOW"
    sleep 3
    print_message "To run the server -> uvicorn main:app --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000} --reload into the src folder." "$GREEN"
}

# Function to force rebuild and start containers
force_build_containers() {
    # Clean up any existing containers first
    print_message "Cleaning up any existing containers..." "$YELLOW"
    docker-compose -f $COMPOSE_FILE down --remove-orphans 2>/dev/null || true
    
    print_message "Force rebuilding Docker images..." "$YELLOW"
    docker-compose -f $COMPOSE_FILE build --no-cache || handle_error "Failed to build Docker images"
    
    print_message "Starting containers..." "$YELLOW"
    docker-compose -f $COMPOSE_FILE up -d || handle_error "Failed to start containers"
    
    # Wait for containers to be ready
    print_message "Waiting for containers to be ready..." "$YELLOW"
    sleep 3
    print_message "To run the server -> uvicorn main:app --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000} --reload" "$GREEN"
}

# Function to stop containers
stop_containers() {
    print_message "Stopping containers..." "$YELLOW"
    docker-compose -f $COMPOSE_FILE down
}

# Function to enter container bash
enter_bash() {
    print_message "Entering $CONTAINER_NAME bash..." "$GREEN"
    docker exec -it $CONTAINER_NAME /bin/bash || handle_error "Failed to enter container bash. Ensure the container is running."
}

# Main execution
case "$ACTION" in
    "bash")
        start_containers
        enter_bash
        ;;
    "build")
        force_build_containers
        enter_bash
        ;;
    "stop")
        stop_containers
        ;;
    "restart")
        stop_containers
        start_containers
        enter_bash
        ;;
    "logs")
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    "clean")
        print_message "Cleaning up containers and volumes..." "$YELLOW"
        docker-compose -f $COMPOSE_FILE down -v --remove-orphans
        print_message "Removing any dangling containers..." "$YELLOW"
        docker container prune -f || true
        print_message "Cleanup completed!" "$GREEN"
        ;;
    "force-clean")
        print_message "Force cleaning up containers, volumes, and images..." "$YELLOW"
        docker-compose -f $COMPOSE_FILE down -v --remove-orphans
        docker container prune -f || true
        docker image prune -f || true
        docker volume prune -f || true
        print_message "Force cleanup completed!" "$GREEN"
        ;;
    *)
        print_message "Usage: ./run.sh [bash|build|stop|restart|logs|clean|force-clean]" "$YELLOW"
        print_message "  bash        - Start containers and enter bash (default)" "$NC"
        print_message "  build       - Force rebuild containers and enter bash" "$NC"
        print_message "  stop        - Stop all containers" "$NC"
        print_message "  restart     - Restart containers and enter bash" "$NC"
        print_message "  logs        - Show container logs" "$NC"
        print_message "  clean       - Stop containers and remove volumes" "$NC"
        print_message "  force-clean - Force remove containers, volumes, and images" "$NC"
        exit 1
        ;;
esac