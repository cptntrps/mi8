#!/bin/bash
# Setup script to connect AgenticSeek to your own git repository

echo "🔧 Setting up your personal AgenticSeek repository..."

# Get your repository URL
echo "Please provide your git repository URL (e.g., https://github.com/yourusername/agenticseek-enhanced.git):"
read REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ No repository URL provided. Exiting."
    exit 1
fi

echo "📡 Configuring git remote..."

# Remove the original remote
git remote remove origin

# Add your repository as the new origin
git remote add origin "$REPO_URL"

# Verify the setup
echo "✅ New remote configured:"
git remote -v

echo "📦 Preparing to push your enhanced AgenticSeek..."

# Add all your enhancements
git add .

# Create a commit with your improvements
git commit -m "Enhanced AgenticSeek with functional tools

- Added real file operations
- Implemented shell command execution  
- Created Cursor IDE integration
- Built database operations
- Added git tools for version control
- Created self-development framework
- Functional AI agent with real capabilities

🤖 Generated with AgenticSeek collaboration"

echo "🚀 Pushing to your repository..."

# Push to your repository
git push -u origin main

echo "🎉 Success! Your enhanced AgenticSeek is now in your repository!"
echo "🔗 Repository: $REPO_URL"