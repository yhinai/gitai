# 🔍 GitAIOps Troubleshooting Guide

> **Quick solutions for common issues and problems**

## 🚨 **Quick Diagnostics**

### **Health Check First**
```bash
# Check overall system health
curl http://localhost:8000/health/ | python -m json.tool

# Expected: All 5 services should be "healthy"
# If not healthy, see specific service troubleshooting below
```

### **Integration Test**
```bash
# Run comprehensive integration test
PYTHONPATH=. python scripts/integration_test.py

# Expected: 100% success rate (8/8 components)
# If failures, see detailed solutions below
```

---

## 🔧 **Common Issues & Solutions**

### **1. Server Won't Start**

#### **❌ "Port already in use"**
```bash
# Problem: Port 8000 is occupied
Error: [Errno 48] Address already in use

# Solution: Kill existing processes
pkill -f uvicorn
# Or use different port
PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8001
```

#### **❌ "Module not found" errors**
```bash
# Problem: Python path not set
ModuleNotFoundError: No module named 'src'

# Solution: Always use PYTHONPATH
PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000

# Or activate conda environment first
conda activate gitaiops
```

#### **❌ "Conda environment not found"**
```bash
# Problem: GitAIOps environment doesn't exist
CondaEnvironmentError: environment does not exist: gitaiops

# Solution: Create environment
conda env create -f environment.yml
conda activate gitaiops
```

### **2. Service Health Issues**

#### **❌ GitLab Client Unhealthy**
```bash
# Check GitLab connectivity
curl -H "Authorization: Bearer glpat-aTrQQ4EqmxGpGh3Ddcgm" \
  "https://gitlab.com/api/v4/projects/278964"

# If fails: Check internet connection and GitLab status
# If 401: Token may be expired (hardcoded tokens can expire)
```

#### **❌ OpenRouter Client Issues**
```bash
# Problem: AI service unavailable
{"service": "openrouter_client", "status": "unhealthy"}

# Solution: Check API keys in config
grep -A 5 "openrouter_api_key" src/core/config.py

# Verify keys are valid (first 10 chars)
echo "Key 1: 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" | cut -c1-20
```

#### **❌ Neo4j Connection Failed**
```bash
# Problem: Neo4j not available (this is expected and OK)
{"error": "Couldn't connect to localhost:7687"}

# Solution: This is normal - Neo4j is optional
# Expert Finder works with fallback mode
# To install Neo4j (optional):
# docker run -p 7687:7687 -p 7474:7474 neo4j:latest
```

### **3. Event Processing Issues**

#### **❌ Events Not Processing**
```bash
# Check event processing status
curl http://localhost:8000/api/v1/metrics/events | python -m json.tool

# Expected: "running": true, "worker_count": 5
# If not running:
PYTHONPATH=. python scripts/fix_event_processing.py
```

#### **❌ Workers Not Starting**
```bash
# Problem: Event workers not initialized
{"running": false, "worker_count": 0}

# Solution: Restart server (workers start on startup)
pkill -f uvicorn
PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000
```

### **4. API Issues**

#### **❌ 404 Not Found**
```bash
# Problem: Endpoint doesn't exist
curl http://localhost:8000/api/v1/nonexistent
# Returns: {"detail": "Not Found"}

# Solution: Check available endpoints
curl http://localhost:8000/openapi.json | python -c "
import sys, json
data = json.load(sys.stdin)
for path in sorted(data['paths'].keys()):
    print(path)
"
```

#### **❌ 422 Unprocessable Entity**
```bash
# Problem: Invalid request format
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Solution: Check API docs for correct format
open http://localhost:8000/docs
# Or use correct format:
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "user_id": "user", "project_id": 278964}'
```

### **5. AI Feature Issues**

#### **❌ MR Analysis Fails**
```bash
# Problem: MR not found
{"error": "Merge request 999999 not found"}

# Solution: Use real MR IID from GitLab project 278964
# Check available MRs:
curl -H "Authorization: Bearer glpat-aTrQQ4EqmxGpGh3Ddcgm" \
  "https://gitlab.com/api/v4/projects/278964/merge_requests?state=opened&per_page=5"

# Use real MR IID (e.g., 194534):
curl -X POST "http://localhost:8000/api/v1/ai/triage/merge-request" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 278964, "mr_iid": 194534}'
```

#### **❌ AI Chat Not Responding**
```bash
# Problem: AI service timeout or error
{"error": "AI service unavailable"}

# Solution: Check AI service health
curl http://localhost:8000/health/ | grep -A 3 "openrouter_client"

# If unhealthy, restart server:
pkill -f uvicorn
PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000
```

---

## 🔧 **Environment Issues**

### **Conda Environment Problems**

#### **❌ Environment Activation Fails**
```bash
# Problem: Conda not in PATH
conda: command not found

# Solution: Add conda to PATH
export PATH="$HOME/miniconda3/bin:$PATH"
# Or for Anaconda:
export PATH="$HOME/anaconda3/bin:$PATH"

# Make permanent by adding to ~/.bashrc or ~/.zshrc
echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
```

#### **❌ Package Conflicts**
```bash
# Problem: Dependency conflicts during environment creation
Solving environment: failed with initial frozen solve

# Solution: Remove and recreate environment
conda env remove -n gitaiops
conda clean --all
conda env create -f environment.yml
```

### **Python Path Issues**

#### **❌ Import Errors**
```bash
# Problem: Can't import src modules
ImportError: attempted relative import with no known parent package

# Solution: Always set PYTHONPATH
export PYTHONPATH=.
# Or run with PYTHONPATH prefix:
PYTHONPATH=. python scripts/integration_test.py
```

---

## 📊 **Performance Issues**

### **Slow Response Times**

#### **❌ API Calls Taking Too Long**
```bash
# Problem: Slow AI analysis (>30 seconds)
# Check AI service load balancing
curl http://localhost:8000/api/v1/metrics/events | grep avg_processing_time

# Solution: Multiple API keys provide load balancing
# Check if all 4 OpenRouter keys are working:
grep -c "OpenRouter client.*initialized" logs/gitaiops.log
# Should show 4 clients initialized
```

#### **❌ High Memory Usage**
```bash
# Problem: Memory consumption growing
# Check event queue size:
curl http://localhost:8000/api/v1/metrics/events | grep total_queue_size

# Solution: Events should be processed quickly
# If queue is growing, restart server:
pkill -f uvicorn
PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000
```

---

## 🧪 **Testing Issues**

### **Integration Test Failures**

#### **❌ GitLab Integration Test Fails**
```bash
# Problem: GitLab health check failed
❌ FAIL GitLab Integration

# Solution: Check GitLab API access
curl -H "Authorization: Bearer glpat-aTrQQ4EqmxGpGh3Ddcgm" \
  "https://gitlab.com/api/v4/user"

# If 401: Token expired, update in src/core/config.py
# If network error: Check internet connection
```

#### **❌ Event Processing Test Fails**
```bash
# Problem: Event processing not working
❌ FAIL Event Processing

# Solution: Ensure workers are started
curl http://localhost:8000/api/v1/metrics/events | grep '"running": true'

# If not running, restart server and wait for startup:
pkill -f uvicorn
PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000
sleep 10  # Wait for full startup
```

---

## 🔍 **Debugging Tools**

### **Log Analysis**
```bash
# Check application logs
tail -f logs/gitaiops.log

# Check for specific errors
grep -i error logs/gitaiops.log | tail -10

# Check service initialization
grep -i "initialized" logs/gitaiops.log
```

### **Health Monitoring**
```bash
# Continuous health monitoring
watch -n 5 'curl -s http://localhost:8000/health/ | python -m json.tool'

# Event processing monitoring
watch -n 2 'curl -s http://localhost:8000/api/v1/metrics/events | python -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Workers: {data[\"worker_count\"]}, Running: {data[\"running\"]}\")
print(f\"Processed: {data[\"total_processed\"]}, Failed: {data[\"total_failed\"]}\")
"'
```

### **API Testing**
```bash
# Test all major endpoints
echo "Testing health..."
curl -s http://localhost:8000/health/ | python -c "import sys,json; print('✅' if json.load(sys.stdin)['status']=='healthy' else '❌')"

echo "Testing AI chat..."
curl -s -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test","user_id":"test","project_id":278964}' | python -c "import sys,json; print('✅' if 'response' in json.load(sys.stdin) else '❌')"

echo "Testing MR analysis..."
curl -s -X POST http://localhost:8000/api/v1/ai/triage/merge-request \
  -H "Content-Type: application/json" \
  -d '{"project_id":278964,"mr_iid":194534}' | python -c "import sys,json; print('✅' if 'risk_level' in json.load(sys.stdin) else '❌')"
```

---

## 🆘 **Emergency Recovery**

### **Complete Reset**
```bash
# Nuclear option: Reset everything
pkill -f uvicorn
conda env remove -n gitaiops
conda env create -f environment.yml
conda activate gitaiops
PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000
```

### **Quick Health Check Script**
```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
echo "🔍 GitAIOps Health Check"
echo "========================"

# Check server
if curl -s http://localhost:8000/health/ > /dev/null; then
    echo "✅ Server: Running"
    
    # Check services
    HEALTHY=$(curl -s http://localhost:8000/health/ | python -c "import sys,json; print(json.load(sys.stdin)['healthy_services'])")
    TOTAL=$(curl -s http://localhost:8000/health/ | python -c "import sys,json; print(json.load(sys.stdin)['total_services'])")
    echo "✅ Services: $HEALTHY/$TOTAL healthy"
    
    # Check event processing
    WORKERS=$(curl -s http://localhost:8000/api/v1/metrics/events | python -c "import sys,json; print(json.load(sys.stdin)['worker_count'])")
    echo "✅ Event Workers: $WORKERS running"
    
    echo "🎉 GitAIOps is healthy!"
else
    echo "❌ Server: Not running"
    echo "💡 Start with: PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000"
fi
EOF

chmod +x health_check.sh
./health_check.sh
```

---

## 📞 **Getting Help**

### **Still Having Issues?**

1. **📋 Gather Information:**
   ```bash
   # System info
   uname -a
   conda --version
   python --version
   
   # GitAIOps status
   curl -s http://localhost:8000/health/ | python -m json.tool > health_status.json
   PYTHONPATH=. python scripts/integration_test.py > test_results.txt 2>&1
   ```

2. **📧 Report Issue:**
   - Include system information
   - Attach health_status.json and test_results.txt
   - Describe what you were trying to do
   - Include exact error messages

3. **💬 Community Support:**
   - [GitHub Issues](https://github.com/gitaiops/platform/issues)
   - [GitHub Discussions](https://github.com/gitaiops/platform/discussions)

---

**🎯 Most issues are resolved by restarting the server and ensuring the conda environment is activated. When in doubt, run the integration test to identify specific problems.** 