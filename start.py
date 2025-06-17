#!/usr/bin/env python3
"""
GitAIOps Platform - Ultra-Simple Launcher
Single command to set up and start everything
"""
import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Ensure Python 3.12+ is being used"""
    if sys.version_info < (3, 12):
        print("❌ Python 3.12+ required. You have:", sys.version)
        sys.exit(1)
    print("✅ Python version:", sys.version.split()[0])

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print("❌ Failed to install dependencies:", e)
        sys.exit(1)

def setup_dashboard():
    """Set up React dashboard"""
    dashboard_path = Path("dashboard")
    if not dashboard_path.exists():
        print("⚠️ Dashboard directory not found, skipping...")
        return
    
    package_json = dashboard_path / "package.json"
    if not package_json.exists():
        print("⚠️ No package.json found, skipping dashboard setup...")
        return
    
    print("🎨 Setting up React dashboard...")
    try:
        # Install npm dependencies
        subprocess.run(["npm", "install"], cwd=dashboard_path, check=True, capture_output=True)
        print("✅ Dashboard dependencies installed")
        
        # Build dashboard
        subprocess.run(["npm", "run", "build"], cwd=dashboard_path, check=True, capture_output=True)
        print("✅ Dashboard built")
        
    except subprocess.CalledProcessError as e:
        print("⚠️ Dashboard setup failed, but continuing...")
    except FileNotFoundError:
        print("⚠️ npm not found, skipping dashboard setup...")

def run_tests():
    """Run basic system tests"""
    print("🧪 Running system tests...")
    try:
        # Test Python imports
        import gitaiops
        print("✅ Main module imports successfully")
        
        # Test basic functionality
        from gitaiops import get_settings
        settings = get_settings()
        print("✅ Configuration loaded")
        
        print("✅ All tests passed")
        return True
    except Exception as e:
        print("⚠️ Test failed:", e)
        return False

def main():
    """Main launcher function"""
    print("🚀 GitAIOps Platform - Ultra-Simple Setup & Launch")
    print("=" * 55)
    
    # Check system requirements
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Setup dashboard
    setup_dashboard()
    
    # Run tests
    if not run_tests():
        print("⚠️ Some tests failed, but continuing...")
    
    print("\n🎉 Setup complete! Starting GitAIOps Platform...")
    print("=" * 55)
    
    # Import and run the main application
    try:
        from gitaiops import main
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 GitAIOps Platform stopped")
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()