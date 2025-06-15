import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// API base URL - use window.location.origin to get the correct base URL
const API_BASE = `${window.location.protocol}//${window.location.host}/api/v1`;

function App() {
  const [activeSection, setActiveSection] = useState('overview');
  const [platformData, setPlatformData] = useState({
    phase1: {},
    phase2: {},
    phase3: {},
    health: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all platform data
  const fetchPlatformData = async () => {
    try {
      setLoading(true);
      setError(null);

      const requests = [
        // Phase 1 - AI Features
        axios.get(`${API_BASE}/ai/triage/demo`),
        axios.get(`${API_BASE}/ai/chat/demo`),
        axios.get(`${API_BASE}/ai/scan/demo`),
        
        // Phase 2 - Expert Finder
        axios.get(`${API_BASE}/codecompass/experts/demo`),
        axios.get(`${API_BASE}/codecompass/knowledge-graph/stats`),
        
        // Phase 3 - Metrics
        axios.get(`${API_BASE}/metrics/demo`),
        axios.get(`${API_BASE}/metrics/system/stats`),
        
        // Health
        axios.get(`${API_BASE}/health/`)
      ];

      const responses = await Promise.allSettled(requests);
      
      setPlatformData({
        phase1: {
          triage: responses[0].status === 'fulfilled' ? responses[0].value.data : null,
          chatops: responses[1].status === 'fulfilled' ? responses[1].value.data : null,
          scanner: responses[2].status === 'fulfilled' ? responses[2].value.data : null
        },
        phase2: {
          experts: responses[3].status === 'fulfilled' ? responses[3].value.data : null,
          knowledgeGraph: responses[4].status === 'fulfilled' ? responses[4].value.data : null
        },
        phase3: {
          metrics: responses[5].status === 'fulfilled' ? responses[5].value.data : null,
          systemStats: responses[6].status === 'fulfilled' ? responses[6].value.data : null
        },
        health: responses[7].status === 'fulfilled' ? responses[7].value.data : null
      });

    } catch (err) {
      console.error('Failed to fetch platform data:', err);
      setError('Failed to load platform data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlatformData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchPlatformData, 30000);
    return () => clearInterval(interval);
  }, []);

  const navigationItems = [
    { id: 'overview', label: 'Overview', icon: '🚀' },
    { id: 'live-demo', label: 'Live Demo', icon: '💻' },
    { id: 'phase1', label: 'AI Features', icon: '🤖' },
    { id: 'phase2', label: 'Expert Finder', icon: '👥' },
    { id: 'phase3', label: 'Metrics', icon: '📊' }
  ];

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <h1>🚀 GitAIOps</h1>
            <p>AI-Powered DevOps Platform</p>
          </div>
          <div className="status-indicator">
            <span className={`status-dot ${platformData.health ? 'active' : 'inactive'}`}></span>
            <span>System {platformData.health ? 'Active' : 'Inactive'}</span>
          </div>
        </div>
      </header>

      <div className="main-container">
        {/* Sidebar Navigation */}
        <nav className="sidebar">
          {navigationItems.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activeSection === item.id ? 'active' : ''}`}
              onClick={() => setActiveSection(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
          
          <div className="nav-footer">
            <button className="refresh-btn" onClick={fetchPlatformData} disabled={loading}>
              {loading ? '⏳' : '🔄'} Refresh
            </button>
          </div>
        </nav>

        {/* Main Content */}
        <main className="content">
          {error && (
            <div className="error-banner">
              <span>⚠️ {error}</span>
              <button onClick={fetchPlatformData}>Retry</button>
            </div>
          )}

          {activeSection === 'overview' && <OverviewSection data={platformData} />}
          {activeSection === 'live-demo' && <LiveDemoSection />}
          {activeSection === 'phase1' && <Phase1Section data={platformData.phase1} />}
          {activeSection === 'phase2' && <Phase2Section data={platformData.phase2} />}
          {activeSection === 'phase3' && <Phase3Section data={platformData.phase3} />}
        </main>
      </div>
    </div>
  );
}

// Overview Section
function OverviewSection({ data }) {
  return (
    <div className="section overview-section">
      <h2>Platform Overview</h2>
      
      <div className="overview-grid">
        <div className="feature-card phase1">
          <div className="feature-icon">🤖</div>
          <h3>Phase 1: AI Features</h3>
          <p>Intelligent merge request analysis, pipeline optimization, and ChatOps</p>
          <div className="feature-stats">
            <div className="stat">
              <span className="stat-value">4</span>
              <span className="stat-label">AI Features</span>
            </div>
            <div className="stat">
              <span className="stat-value">
                {data.phase1?.triage ? '✅' : '⏳'}
              </span>
              <span className="stat-label">Status</span>
            </div>
          </div>
        </div>

        <div className="feature-card phase2">
          <div className="feature-icon">👥</div>
          <h3>Phase 2: Expert Finder</h3>
          <p>Knowledge graph and developer expertise mapping</p>
          <div className="feature-stats">
            <div className="stat">
              <span className="stat-value">
                {data.phase2?.knowledgeGraph?.stats?.supported_technologies || 0}
              </span>
              <span className="stat-label">Technologies</span>
            </div>
            <div className="stat">
              <span className="stat-value">
                {data.phase2?.experts ? '✅' : '⏳'}
              </span>
              <span className="stat-label">Status</span>
            </div>
          </div>
        </div>

        <div className="feature-card phase3">
          <div className="feature-icon">📊</div>
          <h3>Phase 3: Real-time Metrics</h3>
          <p>Performance monitoring and anomaly detection</p>
          <div className="feature-stats">
            <div className="stat">
              <span className="stat-value">
                {data.phase3?.systemStats?.total_metrics_collected || 0}
              </span>
              <span className="stat-label">Metrics</span>
            </div>
            <div className="stat">
              <span className="stat-value">
                {data.phase3?.systemStats?.monitoring_active ? '✅' : '⏳'}
              </span>
              <span className="stat-label">Monitoring</span>
            </div>
          </div>
        </div>
      </div>

      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="action-buttons">
          <button className="action-btn primary">
            🔍 Analyze MR
          </button>
          <button className="action-btn secondary">
            👨‍💻 Find Expert
          </button>
          <button className="action-btn secondary">
            📈 View Metrics
          </button>
          <button className="action-btn secondary">
            🤖 Ask ChatOps
          </button>
        </div>
      </div>
    </div>
  );
}

// Live Demo Section - Real Code Analysis
function LiveDemoSection() {
  const [selectedDemo, setSelectedDemo] = useState('mr-analysis');
  const [demoData, setDemoData] = useState({});
  const [loading, setLoading] = useState(false);

  const fetchDemoData = async (demoType) => {
    try {
      setLoading(true);
      let response;
      switch (demoType) {
        case 'mr-analysis':
          response = await axios.get(`${API_BASE}/ai/triage/demo`);
          break;
        case 'realtime-analysis':
          response = await axios.get(`${API_BASE}/ai/demo/realtime-analysis`);
          break;
        case 'code-analysis':
          response = await axios.get(`${API_BASE}/ai/demo/code-analysis`);
          break;
        case 'vulnerability-scan':
          response = await axios.get(`${API_BASE}/ai/demo/vulnerability-details`);
          break;
        default:
          response = await axios.get(`${API_BASE}/ai/triage/demo`);
      }
      setDemoData(response.data);
    } catch (error) {
      console.error('Failed to fetch demo data:', error);
      setDemoData({});
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchDemoData(selectedDemo);
  }, [selectedDemo]);

  return (
    <div className="section live-demo-section">
      <h2>💻 Live Code Analysis Demo</h2>
      <p className="section-description">
        See GitAIOps analyzing real projects with actual code, dependencies, and security issues.
      </p>
      
      <div className="demo-selector">
        <button 
          className={`demo-btn ${selectedDemo === 'mr-analysis' ? 'active' : ''}`}
          onClick={() => setSelectedDemo('mr-analysis')}
        >
          🔍 MR Analysis
        </button>
        <button 
          className={`demo-btn ${selectedDemo === 'realtime-analysis' ? 'active' : ''}`}
          onClick={() => setSelectedDemo('realtime-analysis')}
        >
          ⏱️ Real-time Analysis
        </button>
        <button 
          className={`demo-btn ${selectedDemo === 'code-analysis' ? 'active' : ''}`}
          onClick={() => setSelectedDemo('code-analysis')}
        >
          📝 Code Quality
        </button>
        <button 
          className={`demo-btn ${selectedDemo === 'vulnerability-scan' ? 'active' : ''}`}
          onClick={() => setSelectedDemo('vulnerability-scan')}
        >
          🛡️ Security Scan
        </button>
      </div>

      <div className="demo-content">
        {loading ? (
          <div className="demo-placeholder">
            <p>🔄 Loading realistic demo data...</p>
          </div>
        ) : (
          <>
            {selectedDemo === 'mr-analysis' && <MRAnalysisDemo data={demoData} />}
            {selectedDemo === 'realtime-analysis' && <RealtimeAnalysisDemo data={demoData} />}
            {selectedDemo === 'code-analysis' && <CodeAnalysisDemo data={demoData} />}
            {selectedDemo === 'vulnerability-scan' && <VulnerabilityDemo data={demoData} />}
          </>
        )}
      </div>
    </div>
  );
}

// MR Analysis Demo Component
function MRAnalysisDemo({ data }) {
  if (!data.analysis) return <div className="demo-placeholder">No data available</div>;

  return (
    <div className="demo-card">
      <h3>🔍 Merge Request Analysis</h3>
      <div className="project-info">
        <div className="project-header">
          <span className="project-name">{data.project_name}</span>
          <span className="mr-number">#{data.mr_iid}</span>
        </div>
        <h4 className="mr-title">{data.mr_title}</h4>
        <div className="mr-meta">
          <span className="author">👤 {data.author}</span>
          <span className="branch">🌿 {data.branch} → {data.target_branch}</span>
        </div>
      </div>

      <div className="analysis-results">
        <div className="risk-assessment">
          <h5>Risk Assessment</h5>
          <div className="risk-level">
            <span className={`risk-badge risk-${data.analysis.risk_level}`}>
              {data.analysis.risk_level.toUpperCase()}
            </span>
            <span className="risk-score">{Math.round(data.analysis.risk_score * 100)}% risk</span>
          </div>
          <div className="risk-factors">
            <h6>Risk Factors:</h6>
            <ul>
              {data.analysis.risk_factors.slice(0, 4).map((factor, idx) => (
                <li key={idx}>{factor}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="reviewers-section">
          <h5>Suggested Reviewers</h5>
          <div className="reviewers-list">
            {data.analysis.suggested_reviewers.map((reviewer, idx) => (
              <div key={idx} className="reviewer-card">
                <div className="reviewer-info">
                  <span className="reviewer-name">{reviewer.name}</span>
                  <span className="reviewer-username">@{reviewer.username}</span>
                </div>
                <div className="reviewer-expertise">
                  {reviewer.expertise.map((skill, skillIdx) => (
                    <span key={skillIdx} className="skill-tag">{skill}</span>
                  ))}
                </div>
                <div className="confidence">
                  {Math.round(reviewer.confidence * 100)}% match
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="files-changed">
          <h5>Files Changed ({data.analysis.files_changed.length})</h5>
          <div className="file-list">
            {data.analysis.files_changed.slice(0, 6).map((file, idx) => (
              <div key={idx} className="file-item">
                <span className="file-path">{file.path}</span>
                <span className="file-changes">+{file.additions} -{file.deletions}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Code Analysis Demo Component  
function CodeAnalysisDemo({ data }) {
  if (!data.analysis) return <div className="demo-placeholder">No data available</div>;

  return (
    <div className="demo-card">
      <h3>📝 Code Quality Analysis</h3>
      <div className="project-info">
        <span className="project-name">{data.project_name}</span>
        <span className="tech-stack">{data.tech_stack}</span>
      </div>

      <div className="code-scores">
        <div className="score-grid">
          <div className="score-item">
            <span className="score-label">Security</span>
            <span className="score-value security">{data.analysis.security_score}/10</span>
          </div>
          <div className="score-item">
            <span className="score-label">Performance</span>
            <span className="score-value performance">{data.analysis.performance_score}/10</span>
          </div>
          <div className="score-item">
            <span className="score-label">Maintainability</span>
            <span className="score-value maintainability">{data.analysis.maintainability_score}/10</span>
          </div>
          <div className="score-item">
            <span className="score-label">Test Coverage</span>
            <span className="score-value coverage">{data.analysis.test_coverage}%</span>
          </div>
        </div>
      </div>

      <div className="code-samples">
        <h5>Code Analysis</h5>
        {data.analysis.code_samples && data.analysis.code_samples.map((sample, idx) => (
          <div key={idx} className="code-sample">
            <div className="sample-header">
              <span className="file-name">{sample.file}</span>
              <span className={`issue-severity ${sample.severity}`}>{sample.severity}</span>
            </div>
            <div className="sample-description">{sample.description}</div>
            <pre className="code-snippet">
              <code>{sample.code_snippet}</code>
            </pre>
            {sample.suggestion && (
              <div className="suggestion">
                <strong>💡 Suggestion:</strong> {sample.suggestion}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// Vulnerability Demo Component
function VulnerabilityDemo({ data }) {
  if (!data.vulnerabilities) return <div className="demo-placeholder">No data available</div>;

  return (
    <div className="demo-card">
      <h3>🛡️ Security Vulnerability Analysis</h3>
      <div className="vuln-summary">
        <div className="vuln-stats">
          <div className="stat-item critical">
            <span className="stat-number">{data.summary.critical}</span>
            <span className="stat-label">Critical</span>
          </div>
          <div className="stat-item high">
            <span className="stat-number">{data.summary.high}</span>
            <span className="stat-label">High</span>
          </div>
          <div className="stat-item medium">
            <span className="stat-number">{data.summary.medium}</span>
            <span className="stat-label">Medium</span>
          </div>
          <div className="stat-item low">
            <span className="stat-number">{data.summary.low}</span>
            <span className="stat-label">Low</span>
          </div>
        </div>
      </div>

      <div className="vulnerabilities-list">
        {data.vulnerabilities.slice(0, 3).map((vuln, idx) => (
          <div key={idx} className="vulnerability-item">
            <div className="vuln-header">
              <span className="vuln-title">{vuln.title}</span>
              <span className={`severity-badge ${vuln.severity.toLowerCase()}`}>
                {vuln.severity}
              </span>
            </div>
            <div className="vuln-details">
              <div className="vuln-info">
                <span className="cve-id">{vuln.cve_id}</span>
                <span className="cvss-score">CVSS: {vuln.cvss_score}</span>
              </div>
              <div className="affected-package">
                📦 {vuln.package_name} {vuln.current_version}
              </div>
              <div className="vuln-description">{vuln.description}</div>
              {vuln.fix_available && (
                <div className="fix-info">
                  <strong>🔧 Fix:</strong> Upgrade to {vuln.fixed_version}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Realtime Analysis Demo Component
function RealtimeAnalysisDemo({ data }) {
  if (!data.steps) return <div className="demo-placeholder">No data available</div>;

  return (
    <div className="demo-card">
      <h3>⏱️ Real-time Analysis Progress</h3>
      <div className="project-info">
        <span className="project-name">{data.project_name}</span>
        <span className="analysis-type">{data.analysis_type}</span>
      </div>

      <div className="progress-steps">
        {data.steps.map((step, idx) => (
          <div key={idx} className={`progress-step ${step.status}`}>
            <div className="step-icon">
              {step.status === 'completed' ? '✅' : 
               step.status === 'running' ? '⏳' : '⭕'}
            </div>
            <div className="step-content">
              <div className="step-title">{step.name}</div>
              <div className="step-details">{step.description}</div>
              {step.duration && (
                <div className="step-duration">{step.duration}</div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="analysis-summary">
        <h5>Analysis Results</h5>
        <div className="summary-stats">
          <div className="summary-item">
            <span className="summary-label">Files Analyzed</span>
            <span className="summary-value">{data.results.files_analyzed}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Issues Found</span>
            <span className="summary-value">{data.results.issues_found}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Processing Time</span>
            <span className="summary-value">{data.results.total_time}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Phase 1 Section - AI Features
function Phase1Section({ data }) {
  const [selectedDemo, setSelectedDemo] = useState('triage');

  return (
    <div className="section phase1-section">
      <h2>🤖 Phase 1: AI-Powered Features</h2>
      
      <div className="demo-selector">
        <button 
          className={`demo-btn ${selectedDemo === 'triage' ? 'active' : ''}`}
          onClick={() => setSelectedDemo('triage')}
        >
          🔍 MR Triage
        </button>
        <button 
          className={`demo-btn ${selectedDemo === 'chatops' ? 'active' : ''}`}
          onClick={() => setSelectedDemo('chatops')}
        >
          💬 ChatOps Bot
        </button>
        <button 
          className={`demo-btn ${selectedDemo === 'scanner' ? 'active' : ''}`}
          onClick={() => setSelectedDemo('scanner')}
        >
          🛡️ Vulnerability Scanner
        </button>
        <button 
          className={`demo-btn ${selectedDemo === 'optimizer' ? 'active' : ''}`}
          onClick={() => setSelectedDemo('optimizer')}
        >
          ⚡ Pipeline Optimizer
        </button>
      </div>

      <div className="demo-content">
        {selectedDemo === 'triage' && (
          <div className="demo-card">
            <h3>🔍 Merge Request Triage</h3>
            <p>AI-powered analysis of merge requests for risk assessment and automatic labeling.</p>
            
            {data.triage ? (
              <div className="demo-results">
                <div className="result-grid">
                  <div className="result-item">
                    <span className="label">Risk Level:</span>
                    <span className={`value risk-${data.triage.analysis?.risk_level}`}>
                      {data.triage.analysis?.risk_level?.toUpperCase() || 'N/A'}
                    </span>
                  </div>
                  <div className="result-item">
                    <span className="label">MR Type:</span>
                    <span className="value">{data.triage.analysis?.mr_type || 'N/A'}</span>
                  </div>
                  <div className="result-item">
                    <span className="label">Complexity:</span>
                    <span className="value">{data.triage.analysis?.complexity || 'N/A'}</span>
                  </div>
                  <div className="result-item">
                    <span className="label">Review Time:</span>
                    <span className="value">{data.triage.analysis?.estimated_review_hours || 0}h</span>
                  </div>
                </div>
                
                {data.triage.analysis?.risk_factors && (
                  <div className="risk-factors">
                    <h4>Risk Factors:</h4>
                    <ul>
                      {data.triage.analysis.risk_factors.slice(0, 3).map((factor, idx) => (
                        <li key={idx}>{factor}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="demo-placeholder">
                <p>🔄 Loading triage analysis...</p>
              </div>
            )}
          </div>
        )}

        {selectedDemo === 'chatops' && (
          <div className="demo-card">
            <h3>💬 ChatOps Bot</h3>
            <p>Intelligent assistant for build diagnostics and DevOps support.</p>
            
            {data.chatops ? (
              <div className="demo-results">
                <div className="chat-examples">
                  <h4>Supported Commands:</h4>
                  <div className="command-list">
                    {data.chatops.supported_commands?.slice(0, 4).map((cmd, idx) => (
                      <div key={idx} className="command-item">
                        <code>{cmd}</code>
                      </div>
                    )) || [
                      <div key="1" className="command-item"><code>diagnose build #123</code></div>,
                      <div key="2" className="command-item"><code>analyze MR !456</code></div>,
                      <div key="3" className="command-item"><code>optimize pipeline</code></div>
                    ]}
                  </div>
                </div>
                
                <div className="chat-demo">
                  <div className="chat-message user">
                    <span>👤</span>
                    <div>Why did build #123 fail?</div>
                  </div>
                  <div className="chat-message bot">
                    <span>🤖</span>
                    <div>I'll analyze build #123 for you. Let me check the pipeline logs and identify the root cause...</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="demo-placeholder">
                <p>🔄 Loading ChatOps demo...</p>
              </div>
            )}
          </div>
        )}

        {selectedDemo === 'scanner' && (
          <div className="demo-card">
            <h3>🛡️ Vulnerability Scanner</h3>
            <p>Multi-language dependency scanning with SBOM generation.</p>
            
            {data.scanner ? (
              <div className="demo-results">
                <div className="scan-summary">
                  <div className="scan-stat">
                    <span className="stat-number">{data.scanner.scan_summary?.dependencies_found || 0}</span>
                    <span className="stat-label">Dependencies Scanned</span>
                  </div>
                  <div className="scan-stat">
                    <span className="stat-number">{data.scanner.scan_summary?.vulnerabilities_found || 0}</span>
                    <span className="stat-label">Vulnerabilities Found</span>
                  </div>
                  <div className="scan-stat">
                    <span className="stat-number">{data.scanner.scan_summary?.critical_vulns || 0}</span>
                    <span className="stat-label">Critical Issues</span>
                  </div>
                </div>
                
                <div className="scan-features">
                  <h4>Scanner Capabilities:</h4>
                  <ul>
                    <li>✅ Multi-language support (Python, JavaScript, Java, Go)</li>
                    <li>✅ OSV database integration</li>
                    <li>✅ CycloneDX SBOM generation</li>
                    <li>✅ Real-time vulnerability alerts</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="demo-placeholder">
                <p>🔄 Loading scanner demo...</p>
              </div>
            )}
          </div>
        )}

        {selectedDemo === 'optimizer' && (
          <div className="demo-card">
            <h3>⚡ Pipeline Optimizer</h3>
            <p>AI-powered pipeline performance analysis and optimization recommendations.</p>
            
            <div className="demo-results">
              <div className="optimization-tips">
                <h4>Optimization Strategies:</h4>
                <div className="tip-grid">
                  <div className="tip-item">
                    <span className="tip-icon">🔄</span>
                    <div>
                      <h5>Parallelization</h5>
                      <p>Run independent jobs simultaneously</p>
                    </div>
                  </div>
                  <div className="tip-item">
                    <span className="tip-icon">💾</span>
                    <div>
                      <h5>Caching</h5>
                      <p>Cache dependencies and build artifacts</p>
                    </div>
                  </div>
                  <div className="tip-item">
                    <span className="tip-icon">🐳</span>
                    <div>
                      <h5>Docker Optimization</h5>
                      <p>Use smaller, optimized base images</p>
                    </div>
                  </div>
                  <div className="tip-item">
                    <span className="tip-icon">⚡</span>
                    <div>
                      <h5>Resource Tuning</h5>
                      <p>Optimize CPU and memory allocation</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Phase 2 Section - Expert Finder
function Phase2Section({ data }) {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="section phase2-section">
      <h2>👥 Phase 2: Expert Finder & Knowledge Graph</h2>
      
      <div className="expert-search">
        <h3>🔍 Find Code Experts</h3>
        <div className="search-box">
          <input
            type="text"
            placeholder="e.g., 'Who knows Python and FastAPI?' or 'React experts'"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button className="search-btn">Search</button>
        </div>
      </div>

      <div className="knowledge-stats">
        <h3>📊 Knowledge Graph Statistics</h3>
        {data.knowledgeGraph ? (
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-icon">🔧</span>
              <div>
                <span className="stat-number">{data.knowledgeGraph.stats?.supported_technologies || 25}</span>
                <span className="stat-label">Technologies Tracked</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">👨‍💻</span>
              <div>
                <span className="stat-number">
                  {data.knowledgeGraph.stats?.knowledge_graph?.nodes?.developers || 0}
                </span>
                <span className="stat-label">Developers Mapped</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">📁</span>
              <div>
                <span className="stat-number">
                  {data.knowledgeGraph.stats?.knowledge_graph?.nodes?.files || 0}
                </span>
                <span className="stat-label">Files Analyzed</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">🔗</span>
              <div>
                <span className="stat-number">
                  {data.knowledgeGraph.stats?.knowledge_graph?.relationships?.expertise || 0}
                </span>
                <span className="stat-label">Expertise Links</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="demo-placeholder">
            <p>🔄 Loading knowledge graph stats...</p>
          </div>
        )}
      </div>

      <div className="module-types">
        <h3>🏗️ Module Types Detected</h3>
        <div className="module-grid">
          {data.knowledgeGraph?.stats?.module_types?.map((type, idx) => (
            <div key={idx} className="module-tag">
              {type}
            </div>
          )) || [
            'controller', 'service', 'model', 'repository', 'api', 'test', 'config', 'util'
          ].map((type, idx) => (
            <div key={idx} className="module-tag">
              {type}
            </div>
          ))}
        </div>
      </div>

      <div className="expert-capabilities">
        <h3>🎯 Expert Finder Capabilities</h3>
        <div className="capability-list">
          <div className="capability-item">
            <span className="capability-icon">🤖</span>
            <div>
              <h4>Natural Language Queries</h4>
              <p>Ask questions in plain English to find experts</p>
            </div>
          </div>
          <div className="capability-item">
            <span className="capability-icon">🔍</span>
            <div>
              <h4>Technology Expertise Mapping</h4>
              <p>Track developer skills across languages and frameworks</p>
            </div>
          </div>
          <div className="capability-item">
            <span className="capability-icon">📊</span>
            <div>
              <h4>Code Ownership Analysis</h4>
              <p>Identify file and module owners based on contributions</p>
            </div>
          </div>
          <div className="capability-item">
            <span className="capability-icon">🌐</span>
            <div>
              <h4>Knowledge Graph Visualization</h4>
              <p>Interactive maps of team expertise and relationships</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Phase 3 Section - Metrics
function Phase3Section({ data }) {
  return (
    <div className="section phase3-section">
      <h2>📊 Phase 3: Real-time Metrics & Monitoring</h2>
      
      <div className="monitoring-status">
        <h3>🎛️ System Status</h3>
        {data.systemStats ? (
          <div className="status-grid">
            <div className="status-card active">
              <span className="status-icon">🟢</span>
              <div>
                <span className="status-label">Monitoring</span>
                <span className="status-value">
                  {data.systemStats.monitoring_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
            <div className="status-card">
              <span className="status-icon">📈</span>
              <div>
                <span className="status-label">Metrics Collected</span>
                <span className="status-value">{data.systemStats.total_metrics_collected}</span>
              </div>
            </div>
            <div className="status-card">
              <span className="status-icon">⚠️</span>
              <div>
                <span className="status-label">Anomalies</span>
                <span className="status-value">{data.systemStats.total_anomalies}</span>
              </div>
            </div>
            <div className="status-card">
              <span className="status-icon">🔔</span>
              <div>
                <span className="status-label">Active Alerts</span>
                <span className="status-value">{data.systemStats.total_alerts}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="demo-placeholder">
            <p>🔄 Loading system status...</p>
          </div>
        )}
      </div>

      <div className="metrics-overview">
        <h3>📊 Supported Metrics</h3>
        {data.metrics ? (
          <div className="metrics-grid">
            {data.metrics.supported_metrics?.map((metric, idx) => (
              <div key={idx} className="metric-card">
                <span className="metric-icon">
                  {getMetricIcon(metric)}
                </span>
                <div>
                  <h4>{formatMetricName(metric)}</h4>
                  <p>{getMetricDescription(metric)}</p>
                </div>
              </div>
            )) || []}
          </div>
        ) : (
          <div className="demo-placeholder">
            <p>🔄 Loading metrics overview...</p>
          </div>
        )}
      </div>

      <div className="monitoring-features">
        <h3>🎯 Monitoring Capabilities</h3>
        <div className="feature-list">
          <div className="feature-item">
            <span className="feature-icon">⏱️</span>
            <div>
              <h4>Real-time Collection</h4>
              <p>Continuous monitoring with 5-minute intervals</p>
            </div>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🔍</span>
            <div>
              <h4>Anomaly Detection</h4>
              <p>Statistical analysis with automated alert generation</p>
            </div>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📈</span>
            <div>
              <h4>Trend Analysis</h4>
              <p>Historical data analysis with predictive insights</p>
            </div>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🚨</span>
            <div>
              <h4>Smart Alerts</h4>
              <p>Context-aware notifications with recommendations</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper functions
function getMetricIcon(metric) {
  const icons = {
    pipeline_duration: '⏱️',
    pipeline_success_rate: '✅',
    build_frequency: '🔄',
    deployment_frequency: '🚀',
    mr_cycle_time: '📋',
    code_quality_score: '⭐',
    vulnerability_count: '🛡️',
    test_coverage: '🧪'
  };
  return icons[metric] || '📊';
}

function formatMetricName(metric) {
  return metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getMetricDescription(metric) {
  const descriptions = {
    pipeline_duration: 'Time taken for CI/CD pipelines to complete',
    pipeline_success_rate: 'Percentage of successful pipeline runs',
    build_frequency: 'Number of builds per day',
    deployment_frequency: 'Number of deployments per day',
    mr_cycle_time: 'Time from MR creation to merge',
    code_quality_score: 'Overall code quality assessment',
    vulnerability_count: 'Number of security vulnerabilities detected',
    test_coverage: 'Percentage of code covered by tests'
  };
  return descriptions[metric] || 'Platform monitoring metric';
}

export default App;