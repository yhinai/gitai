import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface AutomationCommand {
  id: string;
  type: string;
  action: string;
  status: string;
  priority: number;
  created_at: string;
  reasoning: string;
  executed_at?: string;
  result?: any;
  error?: string;
}

interface AutomationInsights {
  project_id: number;
  health_overview: {
    open_mrs: number;
    stale_mrs: number;
    automation_candidates: number;
    pipeline_success_rate: number;
    open_issues: number;
  };
  automation_opportunities: Array<{
    type: string;
    description: string;
    impact: string;
    effort: string;
  }>;
  workflow_bottlenecks: Array<{
    type: string;
    description: string;
    impact: string;
    suggestion: string;
  }>;
  productivity_score: number;
  recommendations: string[];
}

interface AutomationDashboardProps {
  projectId: number;
  projectName?: string;
}

export const AutomationDashboard: React.FC<AutomationDashboardProps> = ({ 
  projectId, 
  projectName 
}) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [insights, setInsights] = useState<AutomationInsights | null>(null);
  const [commands, setCommands] = useState<AutomationCommand[]>([]);
  const [executionHistory, setExecutionHistory] = useState<AutomationCommand[]>([]);
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  // Load automation insights
  useEffect(() => {
    loadAutomationInsights();
    loadAutomationCommands();
  }, [projectId]);

  const loadAutomationInsights = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/automation/insights/${projectId}`);
      if (response.ok) {
        const data = await response.json();
        setInsights(data);
      }
    } catch (error) {
      console.error('Failed to load automation insights:', error);
    }
  };

  const loadAutomationCommands = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/automation/commands');
      if (response.ok) {
        const data = await response.json();
        setCommands(data.commands || []);
        setExecutionHistory(data.execution_history || []);
      }
    } catch (error) {
      console.error('Failed to load automation commands:', error);
    }
  };

  const runAutonomousAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisResults(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/automation/analyze/${projectId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const results = await response.json();
        setAnalysisResults(results);
        
        // Reload commands and insights
        await loadAutomationCommands();
        await loadAutomationInsights();
      } else {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Autonomous analysis failed:', error);
      setAnalysisResults({ error: String(error) });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const executeCommand = async (commandId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/automation/execute/${commandId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        await loadAutomationCommands();
      } else {
        console.error('Failed to execute command');
      }
    } catch (error) {
      console.error('Command execution failed:', error);
    }
  };

  const getPriorityColor = (priority: number) => {
    if (priority >= 8) return 'text-red-600 bg-red-50 border-red-200';
    if (priority >= 6) return 'text-orange-600 bg-orange-50 border-orange-200';
    return 'text-blue-600 bg-blue-50 border-blue-200';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50 border-green-200';
      case 'executing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'failed': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">🤖 Autonomous GitLab Operations</h2>
          <p className="text-gray-600 mt-1">
            AI-powered automation and intelligent decision making for {projectName || `Project #${projectId}`}
          </p>
        </div>
        
        <button
          onClick={runAutonomousAnalysis}
          disabled={isAnalyzing}
          className={`px-6 py-3 rounded-lg font-medium transition-all ${
            isAnalyzing
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-lg'
          }`}
        >
          {isAnalyzing ? (
            <div className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              Analyzing...
            </div>
          ) : (
            '🚀 Run Deep Analysis'
          )}
        </button>
      </div>

      {/* Project Health Overview */}
      {insights && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow border p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Project Health Overview</h3>
          
          <div className="grid grid-cols-5 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-700">{insights.health_overview.open_mrs}</div>
              <div className="text-sm text-blue-600">Open MRs</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-700">{insights.health_overview.stale_mrs}</div>
              <div className="text-sm text-orange-600">Stale MRs</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-700">{insights.health_overview.automation_candidates}</div>
              <div className="text-sm text-green-600">Auto-Merge Ready</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-700">{insights.health_overview.pipeline_success_rate.toFixed(0)}%</div>
              <div className="text-sm text-purple-600">Pipeline Success</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-700">{insights.productivity_score}</div>
              <div className="text-sm text-gray-600">Productivity Score</div>
            </div>
          </div>

          {/* Automation Opportunities */}
          {insights.automation_opportunities.length > 0 && (
            <div className="mb-4">
              <h4 className="font-medium text-gray-900 mb-2">🎯 Automation Opportunities</h4>
              <div className="space-y-2">
                {insights.automation_opportunities.map((opp, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded">
                    <div>
                      <div className="font-medium text-green-800">{opp.description}</div>
                      <div className="text-sm text-green-600">Impact: {opp.impact} • Effort: {opp.effort}</div>
                    </div>
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                      {opp.type.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Workflow Bottlenecks */}
          {insights.workflow_bottlenecks.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">⚠️ Workflow Bottlenecks</h4>
              <div className="space-y-2">
                {insights.workflow_bottlenecks.map((bottleneck, index) => (
                  <div key={index} className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                    <div className="font-medium text-yellow-800">{bottleneck.description}</div>
                    <div className="text-sm text-yellow-600 mt-1">💡 {bottleneck.suggestion}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Analysis Results */}
      <AnimatePresence>
        {analysisResults && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-white rounded-lg shadow border p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🔍 Analysis Results</h3>
            
            {analysisResults.error ? (
              <div className="bg-red-50 border border-red-200 rounded p-4">
                <div className="text-red-800">Analysis failed: {analysisResults.error}</div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-blue-50 rounded p-4">
                    <div className="text-2xl font-bold text-blue-700">{analysisResults.commands_generated || 0}</div>
                    <div className="text-sm text-blue-600">Commands Generated</div>
                  </div>
                  <div className="bg-green-50 rounded p-4">
                    <div className="text-2xl font-bold text-green-700">{analysisResults.commands_executed || 0}</div>
                    <div className="text-sm text-green-600">Commands Executed</div>
                  </div>
                  <div className="bg-purple-50 rounded p-4">
                    <div className="text-2xl font-bold text-purple-700">{analysisResults.analysis?.health_score || 'N/A'}</div>
                    <div className="text-sm text-purple-600">Health Score</div>
                  </div>
                </div>

                {analysisResults.execution_results && analysisResults.execution_results.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">⚡ Executed Actions</h4>
                    <div className="space-y-2">
                      {analysisResults.execution_results.map((result: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 border rounded">
                          <div>
                            <div className="font-medium text-gray-900">{result.action.replace('_', ' ').toUpperCase()}</div>
                            <div className="text-sm text-gray-600">{result.reasoning}</div>
                          </div>
                          <span className={`text-xs px-2 py-1 rounded ${getStatusColor(result.status)}`}>
                            {result.status.toUpperCase()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Command Queue */}
      {commands.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow border p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Automation Command Queue</h3>
          
          <div className="space-y-3">
            {commands.map((command) => (
              <div key={command.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-medium text-gray-900">
                      {command.action.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded border ${getPriorityColor(command.priority)}`}>
                      Priority {command.priority}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded border ${getStatusColor(command.status)}`}>
                      {command.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">{command.reasoning}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Created: {new Date(command.created_at).toLocaleString()}
                  </div>
                </div>
                
                {command.status === 'pending' && (
                  <button
                    onClick={() => executeCommand(command.id)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                  >
                    Execute
                  </button>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Execution History */}
      {executionHistory.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow border p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📜 Recent Execution History</h3>
          
          <div className="space-y-2">
            {executionHistory.map((execution) => (
              <div key={execution.id} className="flex items-center justify-between p-3 bg-gray-50 border rounded">
                <div>
                  <div className="font-medium text-gray-900">
                    {execution.action.replace('_', ' ').toUpperCase()}
                  </div>
                  <div className="text-sm text-gray-600">
                    {execution.result?.status || execution.error || 'No result data'}
                  </div>
                  {execution.executed_at && (
                    <div className="text-xs text-gray-500">
                      Executed: {new Date(execution.executed_at).toLocaleString()}
                    </div>
                  )}
                </div>
                <span className={`text-xs px-2 py-1 rounded border ${getStatusColor(execution.status)}`}>
                  {execution.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* AI Recommendations */}
      {insights && insights.recommendations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🧠 AI Recommendations</h3>
          
          <div className="grid gap-3">
            {insights.recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-white/70 rounded border">
                <span className="w-6 h-6 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-xs font-bold">
                  {index + 1}
                </span>
                <div className="flex-1 text-sm text-gray-700">{recommendation}</div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};