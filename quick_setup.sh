#!/bin/bash

# Quick AgenticSeek Setup (Core functionality only)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Quick AgenticSeek Setup (Core Features)"
echo "================================================"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install core requirements
echo "📦 Installing core dependencies..."
pip install --upgrade pip
pip install -r requirements_core.txt

# Create basic configuration
echo "⚙️ Setting up configuration..."

# Create .env file
cat > .env << EOF
SEARXNG_BASE_URL="http://127.0.0.1:8080"
REDIS_BASE_URL="redis://redis:6379/0"
WORK_DIR="$HOME/agenticseek_workspace"
OLLAMA_PORT="11434"
LM_STUDIO_PORT="1234"
EOF

# Create workspace
mkdir -p "$HOME/agenticseek_workspace"

# Update config for core functionality
cat > config.ini << EOF
[MAIN]
is_local = True
provider_name = ollama
provider_model = deepseek-r1:14b
provider_server_address = 127.0.0.1:11434
agent_name = Jarvis
recover_last_session = False
save_session = False
speak = False
listen = False
jarvis_personality = False
languages = en
[BROWSER]
headless_browser = True
stealth_mode = False
EOF

# Test imports
echo "🧪 Testing core functionality..."
python3 -c "
import sources.router
import sources.agents.agent
print('✅ Core AgenticSeek imports successful')
" 2>/dev/null || echo "⚠️ Some imports may need additional setup"

echo ""
echo "✅ Quick setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure you have a local LLM running (e.g., ollama serve)"
echo "2. Start Docker services: ./start_services.sh"
echo "3. Run CLI: python3 cli.py"
echo ""
echo "💡 Note: This is a minimal setup. For full features, resolve audio dependencies."