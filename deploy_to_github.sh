#!/bin/bash
# Deploy to GitHub Pages
# This script updates the price data and pushes to GitHub
# Runs continuously with 5-minute updates

set -e

cd "$(dirname "$0")"

echo "🚀 Starting Continuous Price Dashboard Updates"
echo "=============================================="
echo "Updates every 5 minutes - Press Ctrl+C to stop"
echo ""

# Continuous loop
while true; do
    echo ""
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting update cycle..."
    echo "=============================================="

    # Activate virtual environment if it exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi

    # Export price drops to docs folder
    echo ""
    echo "📊 Exporting price drop data..."
    python export_price_drops_json.py sites docs/price_drops.json 100

    if [ ! -f "docs/price_drops.json" ]; then
        echo "❌ Error: JSON export failed!"
        echo "Continuing to next cycle..."
        continue
    fi

    echo "✅ Data exported successfully"

    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        echo ""
        echo "⚠️  Not a git repository! Initializing..."
        git init
        git branch -M main
        echo ""
        echo "📝 Next steps:"
        echo "   1. Create a new repository on GitHub"
        echo "   2. Run: git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
        echo "   3. Run this script again"
        exit 0
    fi

    # Add and commit changes
    echo ""
    echo "📝 Committing changes..."

    # Only add docs folder and essential files
    git add docs/
    git add .gitignore
    git add README.md
    git add export_price_drops_json.py
    git add .github/workflows/update-prices.yml
    git add deploy_to_github.sh

    if git diff --staged --quiet; then
        echo "✅ No changes to commit"
    else
        git commit -m "Update price drops data - $(date '+%Y-%m-%d %H:%M:%S')"
        
        echo ""
        echo "📤 Pushing to GitHub..."
        
        # Set up tracking information if not already set
        if ! git config branch.main.remote &>/dev/null; then
            echo "🔗 Setting up branch tracking..."
            git branch --set-upstream-to=origin/main main
        fi
        
        # Pull any remote changes first
        echo "📥 Pulling latest changes from remote..."
        git pull origin main --rebase || {
            echo "⚠️  Pull failed, attempting to push without rebase..."
        }
        
        # Now push
        git push origin main
        
        echo ""
        echo "✅ Deployment complete!"
    fi
    echo ""
    echo "🌐 Your site is live at:"
    echo "   https://marksimpsondotco.github.io/"
    echo ""
    echo "😴 Sleeping for 5 minutes before next update..."
    echo "   (Press Ctrl+C to stop)"
    sleep 300
done
