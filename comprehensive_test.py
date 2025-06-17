#!/usr/bin/env python3
"""
Comprehensive GitAIOps Platform Test
Tests all features, MCP integration, and real-time capabilities
"""
import asyncio
import aiohttp
import websockets
import json
import time
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

class GitAIOpsComprehensiveTest:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.websocket_events = "ws://localhost:8766"
        self.websocket_dashboard = "ws://localhost:8767"
        self.test_results = {
            "api_health": False,
            "ai_operations": {},
            "websockets": {},
            "real_time_features": False,
            "mcp_integration": False
        }
    
    async def test_api_health(self):
        """Test API server health and endpoints"""
        print("\n🏥 Testing API Health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Main health check
                async with session.get(f"{self.api_base}/health/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Main API: {data['status']}")
                        self.test_results["api_health"] = True
                    else:
                        print(f"   ❌ Main API: Status {response.status}")
                
                # AI health check
                async with session.get(f"{self.api_base}/api/v1/ai/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ AI System: {data['status']}")
                        print(f"   🤖 AI Tools Available: {data['ai_tools_available']}")
                    else:
                        print(f"   ❌ AI System: Status {response.status}")
        
        except Exception as e:
            print(f"   ❌ API Health Check Failed: {e}")
            return False
        
        return self.test_results["api_health"]
    
    async def test_ai_operations(self):
        """Test all AI operations with MCP integration"""
        print("\n🤖 Testing AI Operations...")
        
        operations_to_test = [
            {
                "name": "MR Analysis",
                "endpoint": "/api/v1/ai/analyze-merge-request",
                "data": {
                    "mr_title": "Test: Comprehensive Platform Testing",
                    "mr_description": "Testing all GitAIOps features and MCP integration",
                    "changed_files": ["test_file.py", "src/core/test.py"]
                }
            },
            {
                "name": "Security Scan",
                "endpoint": "/api/v1/ai/security-scan",
                "data": {
                    "target_path": ".",
                    "scan_type": "full"
                }
            },
            {
                "name": "Performance Analysis",
                "endpoint": "/api/v1/ai/performance-analysis",
                "data": {
                    "target_path": ".",
                    "analysis_type": "full"
                }
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for operation in operations_to_test:
                try:
                    print(f"   🔄 Testing {operation['name']}...")
                    
                    # Start operation
                    async with session.post(
                        f"{self.api_base}{operation['endpoint']}", 
                        json=operation['data']
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            operation_id = result.get("operation_id")
                            print(f"     ✅ Started: {operation_id}")
                            
                            # Wait for completion
                            for attempt in range(10):
                                await asyncio.sleep(1)
                                async with session.get(
                                    f"{self.api_base}/api/v1/ai/operations/{operation_id}"
                                ) as status_response:
                                    status_data = await status_response.json()
                                    
                                    if status_data["status"] == "completed":
                                        print(f"     ✅ Completed: {operation['name']}")
                                        self.test_results["ai_operations"][operation['name']] = {
                                            "success": True,
                                            "result": status_data["result"]
                                        }
                                        break
                                    elif status_data["status"] == "failed":
                                        print(f"     ❌ Failed: {status_data.get('error', 'Unknown')}")
                                        break
                        else:
                            print(f"     ❌ HTTP {response.status}")
                
                except Exception as e:
                    print(f"     ❌ Error: {e}")
                    self.test_results["ai_operations"][operation['name']] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Test AI Assistant Chat
            try:
                print("   💬 Testing AI Assistant...")
                chat_data = {
                    "query": "Analyze the performance of this GitAIOps platform and suggest improvements",
                    "context": "Comprehensive testing session"
                }
                
                async with session.post(
                    f"{self.api_base}/api/v1/ai/assistant/chat",
                    json=chat_data
                ) as response:
                    if response.status == 200:
                        chat_result = await response.json()
                        print(f"     ✅ Chat Response: {len(chat_result['response'])} chars")
                        print(f"     🎯 Confidence: {chat_result['confidence']}")
                        self.test_results["ai_operations"]["AI_Assistant"] = {
                            "success": True,
                            "response_length": len(chat_result['response'])
                        }
                    else:
                        print(f"     ❌ Chat failed: HTTP {response.status}")
            
            except Exception as e:
                print(f"     ❌ Chat Error: {e}")
    
    async def test_websocket_connections(self):
        """Test WebSocket connections and real-time features"""
        print("\n🔗 Testing WebSocket Connections...")
        
        # Test Unified Event System
        try:
            print("   📡 Testing Event System...")
            async with websockets.connect(self.websocket_events) as ws:
                print("     ✅ Connected to Event System")
                
                # Send test message
                test_message = {
                    "type": "trigger_action",
                    "action": "ai_analysis",
                    "analysis_type": "websocket_test"
                }
                await ws.send(json.dumps(test_message))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(response)
                    print(f"     📨 Received: {data.get('type', 'unknown')}")
                    self.test_results["websockets"]["event_system"] = True
                except asyncio.TimeoutError:
                    print("     ⏰ No response (timeout)")
                    self.test_results["websockets"]["event_system"] = False
        
        except Exception as e:
            print(f"     ❌ Event System failed: {e}")
            self.test_results["websockets"]["event_system"] = False
        
        # Test Unified Dashboard
        try:
            print("   🎛️ Testing Dashboard WebSocket...")
            async with websockets.connect(self.websocket_dashboard) as ws:
                print("     ✅ Connected to Dashboard")
                
                # Wait for initial state
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "initial_state":
                        state = data.get("state", {})
                        components = len(state.get("components", {}))
                        health_score = state.get("performance_metrics", {}).get("health_score", 0)
                        
                        print(f"     📊 Components: {components}")
                        print(f"     💚 Health Score: {health_score:.2f}")
                        self.test_results["websockets"]["dashboard"] = True
                        self.test_results["real_time_features"] = True
                    else:
                        print(f"     📨 Unexpected message type: {data.get('type')}")
                
                except asyncio.TimeoutError:
                    print("     ⏰ No initial state received")
                    self.test_results["websockets"]["dashboard"] = False
        
        except Exception as e:
            print(f"     ❌ Dashboard WebSocket failed: {e}")
            self.test_results["websockets"]["dashboard"] = False
    
    async def test_mcp_integration(self):
        """Test MCP (Model Context Protocol) integration"""
        print("\n🔧 Testing MCP Integration...")
        
        try:
            # Check if MCP tools are available
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/api/v1/ai/health") as response:
                    data = await response.json()
                    
                    if data.get("ai_tools_available"):
                        print("   ✅ MCP Tools Available")
                        
                        # Test operations history (indicates MCP working)
                        async with session.get(f"{self.api_base}/api/v1/ai/operations") as ops_response:
                            operations = await ops_response.json()
                            print(f"   📊 Operations History: {len(operations)} records")
                            
                            if operations:
                                latest_op = operations[0]
                                print(f"   🕐 Latest: {latest_op['operation_id']} ({latest_op['status']})")
                                self.test_results["mcp_integration"] = True
                            else:
                                print("   ⚠️ No operations found")
                    else:
                        print("   ❌ MCP Tools Not Available")
        
        except Exception as e:
            print(f"   ❌ MCP Test Failed: {e}")
    
    async def start_services(self):
        """Start the unified services for testing"""
        print("🚀 Starting GitAIOps Services...")
        
        try:
            from src.core.unified_event_system import start_unified_system
            from src.core.unified_dashboard import start_unified_dashboard
            
            # Start services
            self.event_server = await start_unified_system("localhost", 8766)
            print("   ✅ Event System started on port 8766")
            
            self.dashboard_server = await start_unified_dashboard("localhost", 8767) 
            print("   ✅ Dashboard started on port 8767")
            
            # Wait for services to be ready
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to start services: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("🧪 GitAIOps Comprehensive Test Suite")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Start services
        services_started = await self.start_services()
        if not services_started:
            print("❌ Cannot proceed without services")
            return
        
        # Wait for API server to be ready (assume it's already running)
        await asyncio.sleep(3)
        
        # Run all tests
        await self.test_api_health()
        await self.test_ai_operations()
        await self.test_websocket_connections()
        await self.test_mcp_integration()
        
        # Generate report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # API Health
        status = "✅ PASS" if self.test_results["api_health"] else "❌ FAIL"
        print(f"🏥 API Health: {status}")
        
        # AI Operations
        ai_ops = self.test_results["ai_operations"]
        successful_ops = sum(1 for op in ai_ops.values() if op.get("success", False))
        total_ops = len(ai_ops)
        print(f"🤖 AI Operations: {successful_ops}/{total_ops} successful")
        
        for op_name, result in ai_ops.items():
            status = "✅" if result.get("success", False) else "❌"
            print(f"   {status} {op_name}")
        
        # WebSocket Connections
        ws_results = self.test_results["websockets"]
        event_status = "✅" if ws_results.get("event_system", False) else "❌"
        dashboard_status = "✅" if ws_results.get("dashboard", False) else "❌"
        print(f"🔗 WebSocket Connections:")
        print(f"   {event_status} Event System")
        print(f"   {dashboard_status} Dashboard")
        
        # Real-time Features
        rt_status = "✅ WORKING" if self.test_results["real_time_features"] else "❌ FAILED"
        print(f"⚡ Real-time Features: {rt_status}")
        
        # MCP Integration
        mcp_status = "✅ INTEGRATED" if self.test_results["mcp_integration"] else "❌ NOT WORKING"
        print(f"🔧 MCP Integration: {mcp_status}")
        
        # Overall Status
        all_critical_passed = (
            self.test_results["api_health"] and
            successful_ops >= total_ops * 0.8 and  # 80% AI ops success
            any(ws_results.values()) and  # At least one WebSocket working
            self.test_results["mcp_integration"]
        )
        
        overall_status = "🎉 PLATFORM OPERATIONAL" if all_critical_passed else "⚠️ ISSUES DETECTED"
        print(f"\n🎯 Overall Status: {overall_status}")
        
        print("\n📍 Access Points:")
        print("   🌐 Main Dashboard: http://localhost:8000/dashboard")
        print("   🔧 API Docs: http://localhost:8000/docs")
        print("   📡 Event System: ws://localhost:8766")
        print("   🎛️ Dashboard WS: ws://localhost:8767")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

async def main():
    """Main test execution"""
    tester = GitAIOpsComprehensiveTest()
    
    try:
        await tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n⌨️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())