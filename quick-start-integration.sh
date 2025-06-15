#!/bin/bash

# GitAIOps Quick Start Integration Script
# For immediate testing with GitLab CE project

set -e

echo "🚀 GitAIOps Quick Start Integration"
echo "=================================="
echo ""

# Check if GitAIOps is running
echo "🔍 Checking GitAIOps platform..."
if curl -s http://localhost:8080/api/v1/health/ > /dev/null; then
    echo "✅ GitAIOps platform is running"
else
    echo "❌ GitAIOps platform not found at localhost:8080"
    echo "Please start the platform first:"
    echo "  cd /path/to/gitaiops-platform && ./run.sh"
    exit 1
fi

echo ""
echo "📋 Quick Integration Options:"
echo ""
echo "1. 🧪 Test with GitLab CE Demo Project (No token required)"
echo "2. 🔗 Integrate with your own GitLab project (Token required)"
echo "3. 📚 View integration documentation"
echo ""

read -p "Choose option (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🧪 Testing with GitLab CE Demo Project"
        echo "======================================"
        
        # Test demo endpoints
        echo "🔍 Testing MR analysis..."
        if curl -s "http://localhost:8080/api/v1/ai/triage/demo" | jq '.demo' > /dev/null 2>&1; then
            echo "✅ MR analysis working"
        else
            echo "❌ MR analysis not working"
        fi
        
        echo "🛡️ Testing security scanner..."
        if curl -s "http://localhost:8080/api/v1/ai/scan/demo" | jq '.demo' > /dev/null 2>&1; then
            echo "✅ Security scanner working"
        else
            echo "❌ Security scanner not working"
        fi
        
        echo "⚡ Testing pipeline optimizer..."
        if curl -s "http://localhost:8080/api/v1/ai/optimize/demo" | jq '.demo' > /dev/null 2>&1; then
            echo "✅ Pipeline optimizer working"
        else
            echo "❌ Pipeline optimizer not working"
        fi
        
        echo "👥 Testing expert finder..."
        if curl -s "http://localhost:8080/api/v1/codecompass/experts/demo" | jq '.demo' > /dev/null 2>&1; then
            echo "✅ Expert finder working"
        else
            echo "❌ Expert finder not working"
        fi
        
        echo ""
        echo "🎯 Demo URLs:"
        echo "• Dashboard: http://localhost:8080/dashboard/"
        echo "• Live Demo: http://localhost:8080/dashboard/ → Click 'Live Demo' tab"
        echo "• Test Page: http://localhost:8080/test_live_demo.html"
        echo ""
        echo "💡 The Live Demo shows realistic analysis of actual GitLab projects!"
        ;;
        
    2)
        echo ""
        echo "🔗 Setting up GitLab Integration"
        echo "==============================="
        
        # Check for GitLab token
        if [ -z "$GITLAB_TOKEN" ]; then
            echo "❌ GITLAB_TOKEN environment variable not set"
            echo ""
            echo "📋 Setup Instructions:"
            echo "1. Go to: https://gitlab.com/-/profile/personal_access_tokens"
            echo "2. Create token with scopes: api, read_user, read_repository, write_repository"
            echo "3. Export token: export GITLAB_TOKEN='glpat-your-token-here'"
            echo "4. Run this script again"
            echo ""
            exit 1
        fi
        
        echo "✅ GitLab token found"
        echo ""
        
        # Get project ID
        read -p "Enter your GitLab project ID: " project_id
        
        if [ -z "$project_id" ]; then
            echo "❌ Project ID is required"
            exit 1
        fi
        
        echo ""
        echo "🚀 Running integration setup..."
        
        # Run the comprehensive setup script
        if [ -f "./scripts/setup-gitlab-integration.sh" ]; then
            ./scripts/setup-gitlab-integration.sh --project-id "$project_id"
        else
            echo "❌ Integration script not found"
            echo "Please run from the GitAIOps platform root directory"
            exit 1
        fi
        ;;
        
    3)
        echo ""
        echo "📚 Integration Documentation"
        echo "==========================="
        
        echo "📄 Available Documentation:"
        echo ""
        
        if [ -f "./docs/GITLAB_INTEGRATION_GUIDE.md" ]; then
            echo "✅ Complete Integration Guide: docs/GITLAB_INTEGRATION_GUIDE.md"
        else
            echo "❌ Integration guide not found"
        fi
        
        if [ -f "./GITLAB_CHALLENGE.md" ]; then
            echo "✅ GitLab Challenge Details: GITLAB_CHALLENGE.md"
        else
            echo "❌ Challenge documentation not found"
        fi
        
        if [ -f "./README.md" ]; then
            echo "✅ Project README: README.md"
        else
            echo "❌ README not found"
        fi
        
        echo ""
        echo "🌐 Online Documentation:"
        echo "• Full Documentation: https://docs.gitaiops.dev"
        echo "• GitLab Integration: https://docs.gitaiops.dev/gitlab"
        echo "• API Reference: https://docs.gitaiops.dev/api"
        echo ""
        
        echo "📖 Quick Links:"
        echo "• GitLab Challenge: https://about.gitlab.com/blog/2024/12/11/gitlab-ai-challenge/"
        echo "• GitLab CI/CD Catalog: https://docs.gitlab.com/ee/ci/components/"
        echo "• GitLab Webhooks: https://docs.gitlab.com/ee/user/project/integrations/webhooks.html"
        ;;
        
    *)
        echo "❌ Invalid option. Please choose 1, 2, or 3."
        exit 1
        ;;
esac

echo ""
echo "🎉 Thank you for using GitAIOps!"
echo ""
echo "Need help? Contact us:"
echo "• Discord: https://discord.gg/gitaiops"
echo "• Email: support@gitaiops.dev"
echo "• Issues: https://github.com/gitaiops/platform/issues"