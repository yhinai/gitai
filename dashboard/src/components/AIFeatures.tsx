import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface AIFeaturesProps {
  projectId: number;
  projectName?: string;
  activeFeature?: string;
}

interface AnalysisProgress {
  stage: string;
  progress: number;
  message: string;
  timestamp: Date;
}

export const AIFeatures: React.FC<AIFeaturesProps> = ({ 
  projectId, 
  projectName, 
  activeFeature = 'triage' 
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [progress, setProgress] = useState<AnalysisProgress[]>([]);
  const [currentStage, setCurrentStage] = useState('');

  const features = {
    triage: {
      name: 'MR Triage Analysis',
      icon: '🔍',
      description: 'AI-powered merge request risk assessment and review suggestions',
      endpoint: `/api/v1/ai/triage/${projectId}/mr/2`,
      stages: [
        'Fetching merge request data...',
        'Analyzing code changes...',
        'Assessing risk factors...',
        'Generating reviewer suggestions...',
        'Calculating review time estimate...'
      ]
    },
    security: {
      name: 'Security Vulnerability Scan',
      icon: '🛡️',
      description: 'Comprehensive security analysis and vulnerability detection',
      endpoint: `/api/v1/ai/security/${projectId}/mr/2`,
      stages: [
        'Initializing security scanner...',
        'Scanning code patterns...',
        'Checking dependencies...',
        'Detecting secrets and credentials...',
        'Generating security report...'
      ]
    },
    pipeline: {
      name: 'Pipeline Optimization',
      icon: '⚡',
      description: 'Performance analysis and optimization recommendations',
      endpoint: `/api/v1/ai/pipeline/${projectId}`,
      stages: [
        'Analyzing pipeline configuration...',
        'Identifying bottlenecks...',
        'Calculating optimization potential...',
        'Generating recommendations...',
        'Estimating cost savings...'
      ]
    }
  };

  const currentFeature = features[activeFeature as keyof typeof features] || features.triage;

  const simulateProgress = (stages: string[]) => {
    setProgress([]);
    stages.forEach((stage, index) => {
      setTimeout(() => {
        setCurrentStage(stage);
        setProgress(prev => [...prev, {
          stage,
          progress: ((index + 1) / stages.length) * 100,
          message: stage,
          timestamp: new Date()
        }]);
      }, (index + 1) * 1000);
    });
  };

  const runAnalysis = async () => {
    if (isRunning) return;
    
    setIsRunning(true);
    setResults(null);
    setProgress([]);
    
    // Start progress simulation
    simulateProgress(currentFeature.stages);
    
    try {
      // Start actual API call
      const response = await fetch(`http://localhost:8000${currentFeature.endpoint}`);
      
      if (response.ok) {
        const data = await response.json();
        
        // Wait for progress animation to complete
        setTimeout(() => {
          setResults(data);
          setIsRunning(false);
          setCurrentStage('Analysis complete!');
        }, currentFeature.stages.length * 1000 + 500);
      } else {
        throw new Error(`Failed to run ${currentFeature.name}`);
      }
    } catch (error) {
      setTimeout(() => {
        setResults({ error: `Error: ${error}` });
        setIsRunning(false);
        setCurrentStage('Analysis failed');
      }, currentFeature.stages.length * 1000 + 500);
    }
  };

  // Auto-run analysis when feature changes
  useEffect(() => {
    runAnalysis();
  }, [activeFeature, projectId]);

  const formatResults = (data: any) => {
    if (!data || data.error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-700 mb-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span className="font-medium">Analysis Failed</span>
          </div>
          <p className="text-red-600 text-sm">{data?.error || 'Unknown error occurred'}</p>
        </div>
      );
    }

    switch (activeFeature) {
      case 'triage':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-blue-700">
                  {data.analysis?.risk_level?.toUpperCase() || 'N/A'}
                </div>
                <div className="text-sm text-blue-600">Risk Level</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-700">
                  {data.analysis?.estimated_review_hours || 0}h
                </div>
                <div className="text-sm text-green-600">Review Time</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-purple-700">
                  {data.analysis?.risk_score?.toFixed(1) || '0.0'}
                </div>
                <div className="text-sm text-purple-600">Risk Score</div>
              </div>
            </div>
            
            {data.analysis?.suggested_reviewers && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-3">Suggested Reviewers</h4>
                <div className="flex flex-wrap gap-2">
                  {data.analysis.suggested_reviewers.slice(0, 3).map((reviewer: any, idx: number) => (
                    <span key={idx} className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {reviewer.name} ({Math.round(reviewer.confidence * 100)}%)
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'security':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-red-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-red-700">
                  {data.vulnerability_summary?.severity_breakdown?.critical || 0}
                </div>
                <div className="text-sm text-red-600">Critical</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-orange-700">
                  {data.vulnerability_summary?.severity_breakdown?.high || 0}
                </div>
                <div className="text-sm text-orange-600">High</div>
              </div>
              <div className="bg-yellow-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-yellow-700">
                  {data.vulnerability_summary?.severity_breakdown?.medium || 0}
                </div>
                <div className="text-sm text-yellow-600">Medium</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-700">
                  {data.vulnerability_summary?.risk_level?.toUpperCase() || 'LOW'}
                </div>
                <div className="text-sm text-green-600">Risk Level</div>
              </div>
            </div>

            {data.remediation_advice && data.remediation_advice.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-3">Security Recommendations</h4>
                <div className="space-y-2">
                  {data.remediation_advice.slice(0, 3).map((advice: any, idx: number) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-white rounded border">
                      <div className={`w-2 h-2 rounded-full mt-2 ${
                        advice.priority === 'critical' ? 'bg-red-500' : 
                        advice.priority === 'high' ? 'bg-orange-500' : 'bg-yellow-500'
                      }`} />
                      <div className="flex-1">
                        <div className="font-medium text-sm text-gray-900">{advice.category}</div>
                        <div className="text-xs text-gray-600 mt-1">{advice.issue}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'pipeline':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-blue-700">
                  {data.cost_savings?.time_savings_percent || 0}%
                </div>
                <div className="text-sm text-blue-600">Time Savings</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-700">
                  ${data.cost_savings?.estimated_monthly_cost_savings?.toFixed(0) || 0}
                </div>
                <div className="text-sm text-green-600">Monthly Savings</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-purple-700">
                  {data.caching_optimizations?.length || 0}
                </div>
                <div className="text-sm text-purple-600">Optimizations</div>
              </div>
            </div>

            {data.caching_optimizations && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-3">Optimization Opportunities</h4>
                <div className="space-y-2">
                  {data.caching_optimizations.slice(0, 3).map((opt: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-white rounded border">
                      <div>
                        <div className="font-medium text-sm text-gray-900">{opt.type?.replace('_', ' ').toUpperCase()}</div>
                        <div className="text-xs text-gray-600">{opt.estimated_savings}</div>
                      </div>
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        {opt.estimated_savings?.split(' ')[0] || 'N/A'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className="bg-gray-50 rounded-lg p-4">
            <pre className="text-xs text-gray-700 whitespace-pre-wrap">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Feature Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{currentFeature.icon}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{currentFeature.name}</h3>
            <p className="text-sm text-gray-600">{currentFeature.description}</p>
          </div>
        </div>
        
        <button
          onClick={runAnalysis}
          disabled={isRunning}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            isRunning
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isRunning ? 'Running...' : 'Run Analysis'}
        </button>
      </div>

      {/* Progress Tracking */}
      <AnimatePresence>
        {isRunning && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-blue-50 border border-blue-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2 mb-4">
              <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              <span className="font-medium text-blue-700">Analysis in Progress</span>
            </div>
            
            <div className="space-y-3">
              {progress.map((step, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-3"
                >
                  <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">{step.stage}</div>
                    <div className="w-full bg-blue-200 rounded-full h-2 mt-1">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${step.progress}%` }}
                        className="bg-blue-600 h-2 rounded-full"
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                  </div>
                  <span className="text-xs text-blue-600 font-mono">
                    {step.timestamp.toLocaleTimeString()}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {results && !isRunning && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white border border-gray-200 rounded-lg p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-medium text-gray-900">Analysis Results</h4>
              <span className="text-xs text-gray-500">
                Completed at {new Date().toLocaleTimeString()}
              </span>
            </div>
            
            {formatResults(results)}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Project Info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="text-sm text-gray-600">
          <strong>Target:</strong> {projectName || `Project #${projectId}`} • 
          <strong> MR:</strong> #2 "GitAIOps AI Analysis Demo" • 
          <strong> Engine:</strong> Gemini 2.0 Flash
        </div>
      </div>
    </div>
  );
};