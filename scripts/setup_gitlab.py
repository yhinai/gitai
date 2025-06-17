#!/usr/bin/env python3
"""
GitLab Integration Setup Script

Helps configure GitLab integration for GitAIOps platform.
"""
import os
import sys
from pathlib import Path
import asyncio
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = structlog.get_logger(__name__)

def create_env_file():
    """Create .env file with GitLab configuration"""
    
    print("🔧 GitLab Integration Setup")
    print("=" * 50)
    
    # Check if .env already exists
    env_file = project_root / ".env"
    if env_file.exists():
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Setup cancelled.")
            return False
    
    print("\n📋 Please provide your GitLab information:")
    
    # Get GitLab API URL
    gitlab_url = input("GitLab API URL [https://gitlab.com/api/v4]: ").strip()
    if not gitlab_url:
        gitlab_url = "https://gitlab.com/api/v4"
    
    # Get access token
    print("\n🔑 GitLab Access Token:")
    print("   1. Go to GitLab → Profile → Settings → Access Tokens")
    print("   2. Create token with 'api', 'read_user', 'read_repository' scopes")
    print("   3. Copy the token")
    
    access_token = input("Access Token: ").strip()
    if not access_token:
        print("❌ Access token is required!")
        return False
    
    # Get project ID
    print("\n📁 GitLab Project ID:")
    print("   Find this in your project's main page (below project name)")
    print("   Or in project settings")
    
    project_id = input("Project ID: ").strip()
    if not project_id:
        print("❌ Project ID is required!")
        return False
    
    try:
        int(project_id)  # Validate it's a number
    except ValueError:
        print("❌ Project ID must be a number!")
        return False
    
    # Optional settings
    print("\n⚙️  Optional Settings (press Enter for defaults):")
    
    log_level = input("Log Level [INFO]: ").strip() or "INFO"
    neo4j_enabled = input("Enable Neo4j for enhanced expert finding? (y/N): ").lower().strip() in ['y', 'yes']
    
    # Create .env content
    env_content = f"""# GitLab Configuration (REQUIRED)
GITLAB_API_URL={gitlab_url}
GITLAB_ACCESS_TOKEN={access_token}
GITLAB_PROJECT_ID={project_id}

# Application Settings
APP_ENV=development
LOG_LEVEL={log_level}
DEBUG=true

# Feature Flags (Optional - all default to true)
ENABLE_MR_TRIAGE=true
ENABLE_EXPERT_FINDER=true
ENABLE_PIPELINE_OPTIMIZER=true
ENABLE_VULNERABILITY_SCANNER=true
ENABLE_CHATOPS_BOT=true

# Optional Services
NEO4J_ENABLED={str(neo4j_enabled).lower()}
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# AI Services
AI_SERVICES_ENABLED=true

# Performance Settings
MAX_CONCURRENT_ANALYSES=5
CACHE_TTL_SECONDS=3600
"""
    
    # Write .env file
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ .env file created successfully!")
        print(f"📁 Location: {env_file}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

async def test_gitlab_connection():
    """Test GitLab connection with the configured settings"""
    
    print("\n🧪 Testing GitLab Connection...")
    
    try:
        from src.core.config import get_settings
        from src.integrations.gitlab_client import get_gitlab_client
        
        settings = get_settings()
        gitlab_client = get_gitlab_client()
        
        # Test basic connection
        print("   → Testing API connection...")
        user = await gitlab_client.get_user()
        
        if user:
            print(f"   ✅ Connected successfully!")
            print(f"   👤 User: {user.get('name', 'Unknown')} (@{user.get('username', 'unknown')})")
            print(f"   📧 Email: {user.get('email', 'Not provided')}")
        else:
            print("   ❌ Failed to get user information")
            return False
        
        # Test project access
        print("   → Testing project access...")
        project_id = settings.gitlab_project_id
        project = await gitlab_client.get_project(project_id)
        
        if project:
            print(f"   ✅ Project access confirmed!")
            print(f"   📁 Project: {project.get('name', 'Unknown')} ({project.get('path_with_namespace', 'unknown')})")
            print(f"   🔗 URL: {project.get('web_url', 'Unknown')}")
        else:
            print(f"   ❌ Cannot access project {project_id}")
            print("   💡 Check project ID and token permissions")
            return False
        
        # Test additional endpoints
        print("   → Testing merge requests...")
        mrs = await gitlab_client.list_merge_requests(project_id, limit=5)
        print(f"   📋 Found {len(mrs)} recent merge requests")
        
        print("   → Testing pipelines...")
        pipelines = await gitlab_client.list_project_pipelines(project_id, limit=5)
        print(f"   🔄 Found {len(pipelines)} recent pipelines")
        
        await gitlab_client.close()
        
        print("\n🎉 GitLab integration is working perfectly!")
        return True
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your access token is valid")
        print("   2. Verify project ID is correct")
        print("   3. Ensure token has required permissions")
        print("   4. Check GitLab API URL is accessible")
        return False

def main():
    """Main setup function"""
    
    print("🚀 GitAIOps GitLab Integration Setup")
    print("=" * 50)
    
    # Step 1: Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Step 2: Test connection
    print("\n" + "=" * 50)
    
    try:
        success = asyncio.run(test_gitlab_connection())
        
        if success:
            print("\n🎯 Next Steps:")
            print("   1. Start the GitAIOps platform:")
            print("      conda activate gitaiops")
            print("      PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000")
            print("   2. Open http://localhost:8000/docs to explore the API")
            print("   3. Check http://localhost:8000/health/ for system status")
            print("\n✨ Your GitLab integration is ready!")
        else:
            print("\n❌ Setup incomplete. Please fix the issues above and try again.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 