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
    command -v "\$1" >/dev/null 2>&1
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
# if ! command_exists docker; then
#     handle_error "Docker is not installed. Please install Docker first."
# fi

# if ! command_exists docker-compose; then
#     handle_error "Docker Compose is not installed. Please install Docker Compose first."
# fi

# Script configuration
PROJECT_NAME="money-wizardry"
COMPOSE_FILE="docker-compose.yaml"
CONTAINER_NAME="money-wizardry"

# Parse command line arguments
ACTION=${1:-"bash"} # Default to "bash" if no argument provided

# Function to build and start containers
start_containers() {
    print_message "Building Docker images..." "$YELLOW"
    docker-compose -f $COMPOSE_FILE build || handle_error "Failed to build Docker images"
    
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
        docker-compose -f $COMPOSE_FILE down -v
        ;;
    *)
        print_message "Usage: ./run.sh [bash|server|stop|restart|logs|clean]" "$YELLOW"
        print_message "  bash    - Start containers and enter bash (default)" "$NC"
        print_message "  server  - Start containers and run FastAPI server" "$NC"
        print_message "  stop    - Stop all containers" "$NC"
        print_message "  restart - Restart containers and enter bash" "$NC"
        print_message "  logs    - Show container logs" "$NC"
        print_message "  clean   - Stop containers and remove volumes" "$NC"
        exit 1
        ;;
esac