#!/bin/bash

# Enhanced AgenticSeek Setup Script with MCP Integration
# This script provides a streamlined setup process for AgenticSeek

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_PATH="/home/gui/Claude_Code"

echo -e "${BLUE}🚀 Enhanced AgenticSeek Setup${NC}"
echo "================================================"

# Function to print status
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python found: $PYTHON_VERSION"
    else
        print_error "Python 3 is required but not found"
        exit 1
    fi
    
    # Check Docker
    if command_exists docker; then
        print_success "Docker found"
    else
        print_error "Docker is required but not found"
        echo "Please install Docker and try again"
        exit 1
    fi
    
    # Check Node.js (for MCP integration)
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js found: $NODE_VERSION"
    else
        print_warning "Node.js not found - MCP integration may not work"
    fi
    
    # Check available memory
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 8 ]; then
        print_warning "Less than 8GB RAM detected. Performance may be limited."
    else
        print_success "Sufficient memory: ${TOTAL_MEM}GB"
    fi
}

# Function to setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    cd "$SCRIPT_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_status "Installing Python dependencies..."
        pip install -r requirements.txt
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    print_success "Python environment setup complete"
}

# Function to setup MCP integration
setup_mcp_integration() {
    print_status "Setting up MCP integration..."
    
    if [ -d "$MCP_PATH" ]; then
        # Copy enhanced MCP configuration
        print_status "Configuring MCP servers..."
        
        # Create .env file with MCP integration
        cat > .env << EOF
# Enhanced AgenticSeek Configuration with MCP Integration
SEARXNG_BASE_URL="http://127.0.0.1:8080"
REDIS_BASE_URL="redis://redis:6379/0"
WORK_DIR="$HOME/agenticseek_workspace"
OLLAMA_PORT="11434"
LM_STUDIO_PORT="1234"
CUSTOM_ADDITIONAL_LLM_PORT="11435"

# MCP Integration Paths
MCP_CURSOR_CONTROL_PATH="$MCP_PATH/build/index.js"
MCP_MEMORY_MANAGEMENT_PATH="$MCP_PATH/memory-mcp/build/index.js"
MCP_FILE_WATCHER_PATH="$MCP_PATH/watcher-mcp/build/index.js"

# Optional API Keys (leave empty for local-only operation)
OPENAI_API_KEY=""
DEEPSEEK_API_KEY=""
OPENROUTER_API_KEY=""
TOGETHER_API_KEY=""
GOOGLE_API_KEY=""
ANTHROPIC_API_KEY=""
EOF

        # Create MCP configuration file
        cat > .mcp.json << EOF
{
  "mcpServers": {
    "cursor-control": {
      "command": "node",
      "args": ["$MCP_PATH/build/index.js"],
      "env": {}
    },
    "memory-management": {
      "command": "node",
      "args": ["$MCP_PATH/memory-mcp/build/index.js"],
      "env": {}
    },
    "file-watcher": {
      "command": "node",
      "args": ["$MCP_PATH/watcher-mcp/build/index.js"],
      "env": {}
    }
  }
}
EOF
        
        print_success "MCP integration configured"
        
        # Test MCP servers
        print_status "Testing MCP servers..."
        if [ -f "$MCP_PATH/build/index.js" ]; then
            print_success "Cursor Control MCP found"
        else
            print_warning "Cursor Control MCP not found - please build MCP servers first"
        fi
        
    else
        print_warning "MCP path not found at $MCP_PATH"
        print_warning "MCP integration will be limited"
        
        # Create basic .env file
        cat > .env << EOF
SEARXNG_BASE_URL="http://127.0.0.1:8080"
REDIS_BASE_URL="redis://redis:6379/0"
WORK_DIR="$HOME/agenticseek_workspace"
OLLAMA_PORT="11434"
LM_STUDIO_PORT="1234"
CUSTOM_ADDITIONAL_LLM_PORT="11435"
EOF
    fi
}

# Function to setup configuration
setup_configuration() {
    print_status "Setting up configuration..."
    
    # Create workspace directory
    WORKSPACE_DIR="$HOME/agenticseek_workspace"
    mkdir -p "$WORKSPACE_DIR"
    print_success "Workspace created at $WORKSPACE_DIR"
    
    # Update config.ini with enhanced settings
    cat > config.ini << EOF
[MAIN]
is_local = True
provider_name = ollama
provider_model = deepseek-r1:14b
provider_server_address = 127.0.0.1:11434
agent_name = Jarvis
recover_last_session = True
save_session = True
speak = False
listen = False
jarvis_personality = False
languages = en
[BROWSER]
headless_browser = True
stealth_mode = True
[ENHANCED]
mcp_integration = True
enhanced_memory = True
smart_routing = True
debug_mode = False
EOF
    
    print_success "Configuration updated with enhanced features"
}

# Function to download LLM router model
setup_llm_router() {
    print_status "Setting up LLM router model..."
    
    cd llm_router
    if [ ! -f "model.safetensors" ]; then
        if [ -f "dl_safetensors.sh" ]; then
            print_status "Downloading LLM router model..."
            chmod +x dl_safetensors.sh
            ./dl_safetensors.sh
        else
            print_warning "LLM router download script not found"
        fi
    else
        print_success "LLM router model already exists"
    fi
    cd "$SCRIPT_DIR"
}

# Function to setup Docker services
setup_docker_services() {
    print_status "Setting up Docker services..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Pull required Docker images
    print_status "Pulling Docker images..."
    docker-compose pull
    
    print_success "Docker services ready"
}

# Function to create startup script
create_startup_script() {
    print_status "Creating enhanced startup script..."
    
    cat > start_enhanced.sh << 'EOF'
#!/bin/bash

# Enhanced AgenticSeek Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Enhanced AgenticSeek..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run enhanced_setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start Docker services
echo "📦 Starting Docker services..."
./start_services.sh full

echo "✅ Enhanced AgenticSeek is starting up!"
echo "📱 Web interface: http://localhost:3000"
echo "💻 CLI interface: python3 cli.py"
echo ""
echo "🔧 MCP Integration: Enabled"
echo "🧠 Enhanced Memory: Enabled"
echo "🎯 Smart Routing: Enabled"
EOF

    chmod +x start_enhanced.sh
    print_success "Startup script created: ./start_enhanced.sh"
}

# Function to run tests
run_tests() {
    print_status "Running system tests..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Test Python imports
    python3 -c "import sources.agents.enhanced_mcp_agent; print('✅ Enhanced MCP agent import successful')" 2>/dev/null || print_warning "Enhanced MCP agent import failed"
    
    # Test configuration
    if [ -f ".env" ] && [ -f "config.ini" ]; then
        print_success "Configuration files present"
    else
        print_warning "Configuration files missing"
    fi
    
    # Test Docker
    if docker-compose config >/dev/null 2>&1; then
        print_success "Docker configuration valid"
    else
        print_warning "Docker configuration issues detected"
    fi
}

# Function to show completion message
show_completion() {
    echo ""
    echo -e "${GREEN}🎉 Enhanced AgenticSeek Setup Complete!${NC}"
    echo "================================================"
    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "1. Start AgenticSeek: ./start_enhanced.sh"
    echo "2. Access web interface: http://localhost:3000"
    echo "3. Or use CLI: source venv/bin/activate && python3 cli.py"
    echo ""
    echo -e "${BLUE}🔧 Enhanced Features:${NC}"
    echo "✅ MCP Integration with Cursor Control"
    echo "✅ Enhanced Memory Management"
    echo "✅ Smart Agent Routing"
    echo "✅ Improved Error Handling"
    echo "✅ Development Mode Support"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "- Enhancement details: ENHANCEMENTS.md"
    echo "- Original README: README.md"
    echo ""
    echo -e "${YELLOW}💡 Tip: Run './start_enhanced.sh' to start with all enhancements!${NC}"
}

# Main setup process
main() {
    print_status "Starting Enhanced AgenticSeek setup..."
    
    check_requirements
    setup_python_env
    setup_mcp_integration
    setup_configuration
    setup_llm_router
    setup_docker_services
    create_startup_script
    run_tests
    show_completion
}

# Run main function
main "$@"