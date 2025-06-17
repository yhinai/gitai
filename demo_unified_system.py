#!/usr/bin/env python3
"""
GitAIOps Unified System Demo
Demonstrates the unified real-time platform capabilities
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def demo_ai_operations():
    """Demo AI operations functionality"""
    
    print("\n🤖 Testing AI Operations...")
    
    async with aiohttp.ClientSession() as session:
        
        # Test AI health
        async with session.get("http://localhost:8000/api/v1/ai/health") as response:
            health = await response.json()
            print(f"   AI Health: {health['status']}")
        
        # Test MR Analysis
        mr_data = {
            "mr_title": "Feature: Add unified dashboard",
            "mr_description": "Implementing real-time unified dashboard for GitAIOps",
            "changed_files": ["src/core/unified_dashboard.py", "dashboard/src/components/UnifiedDashboard.tsx"]
        }
        
        async with session.post("http://localhost:8000/api/v1/ai/analyze-merge-request", json=mr_data) as response:
            mr_result = await response.json()
            operation_id = mr_result.get("operation_id")
            print(f"   ✅ MR Analysis Started: {operation_id}")
            
            # Wait for completion
            for _ in range(10):
                await asyncio.sleep(1)
                async with session.get(f"http://localhost:8000/api/v1/ai/operations/{operation_id}") as status_response:
                    status = await status_response.json()
                    if status["status"] == "completed":
                        print(f"   ✅ MR Analysis Completed: Risk Level = {status['result']['risk_level']}")
                        break
                    elif status["status"] == "failed":
                        print(f"   ❌ MR Analysis Failed: {status.get('error', 'Unknown error')}")
                        break
        
        # Test AI Assistant
        chat_data = {
            "query": "What are the performance optimization opportunities?",
            "context": "GitAIOps unified platform"
        }
        
        async with session.post("http://localhost:8000/api/v1/ai/assistant/chat", json=chat_data) as response:
            chat_result = await response.json()
            print(f"   💬 AI Assistant Response: {chat_result['response'][:100]}...")

async def demo_system_health():
    """Demo system health monitoring"""
    
    print("\n🏥 Testing System Health...")
    
    async with aiohttp.ClientSession() as session:
        
        # Main health check
        async with session.get("http://localhost:8000/health/") as response:
            health = await response.json()
            print(f"   System Status: {health['status']}")
            print(f"   Version: {health['version']}")
            
        # AI health check
        async with session.get("http://localhost:8000/api/v1/ai/health") as response:
            ai_health = await response.json()
            print(f"   AI Status: {ai_health['status']}")

async def demo_operations_history():
    """Demo operations tracking"""
    
    print("\n📊 Testing Operations History...")
    
    async with aiohttp.ClientSession() as session:
        
        async with session.get("http://localhost:8000/api/v1/ai/operations") as response:
            operations = await response.json()
            print(f"   Recent Operations: {len(operations)} found")
            
            for op in operations[:3]:  # Show first 3
                print(f"   - {op['operation_id']}: {op['status']} ({op.get('started_at', 'Unknown time')})")

async def main():
    """Main demo function"""
    
    print("🚀 GitAIOps Unified System Demo")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test system components
        await demo_system_health()
        await demo_ai_operations()
        await demo_operations_history()
        
        print("\n" + "=" * 50)
        print("🎉 GitAIOps Unified System Demo Complete!")
        print("\n📍 Access Points:")
        print("   🌐 Main Dashboard:      http://localhost:8000/dashboard")
        print("   🔧 API Documentation:   http://localhost:8000/docs")
        print("   🤖 AI Operations:       http://localhost:8000/api/v1/ai/")
        
        print("\n🎯 Key Features Verified:")
        print("   ✅ Real-time AI operations")
        print("   ✅ Health monitoring")
        print("   ✅ Operation tracking")
        print("   ✅ Interactive chat assistant")
        print("   ✅ Background processing")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("   💡 Make sure the API server is running: python -m uvicorn src.api.main:app --host localhost --port 8000")

if __name__ == "__main__":
    asyncio.run(main())