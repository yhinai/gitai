import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface AIFeaturesProps {
  projectId: number;
  projectName?: string;
}

export const AIFeatures: React.FC<AIFeaturesProps> = ({ projectId, projectName }) => {
  const [activeFeature, setActiveFeature] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const features = [
    {
      id: 'triage',
      name: 'MR Triage',
      description: 'AI-powered merge request analysis',
      icon: '🔍',
      endpoint: '/api/v1/ai/triage/demo'
    },
    {
      id: 'chat',
      name: 'AI Assistant',
      description: 'Conversational AI for project insights',
      icon: '🤖',
      endpoint: '/api/v1/ai/chat/demo'
    },
    {
      id: 'security',
      name: 'Security Scan',
      description: 'Vulnerability detection and analysis',
      icon: '🛡️',
      endpoint: '/api/v1/ai/security/scan'
    },
    {
      id: 'performance',
      name: 'Performance Analysis',
      description: 'Pipeline and code performance insights',
      icon: '⚡',
      endpoint: '/api/v1/ai/performance/analyze'
    }
  ];

  const runFeature = async (feature: any) => {
    setActiveFeature(feature.id);
    setLoading(true);
    setResults(null);

    try {
      const response = await fetch(`http://localhost:8000${feature.endpoint}?project_id=${projectId}`);
      if (response.ok) {
        const data = await response.json();
        setResults(data);
      } else {
        setResults({ error: `Failed to run ${feature.name}` });
      }
    } catch (error) {
      setResults({ error: `Network error: ${error}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-white">AI Features</h3>
        <div className="text-sm text-gray-300">
          Project #{projectId}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-6">
        {features.map((feature) => (
          <button
            key={feature.id}
            onClick={() => runFeature(feature)}
            disabled={loading}
            className={`p-4 rounded-lg text-left transition-all ${
              activeFeature === feature.id
                ? 'bg-blue-500/30 border-blue-400/50'
                : 'bg-white/5 hover:bg-white/10 border-white/10'
            } border ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <div className="text-2xl mb-2">{feature.icon}</div>
            <div className="text-sm font-medium text-white">{feature.name}</div>
            <div className="text-xs text-gray-300 mt-1">{feature.description}</div>
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
          <span className="ml-3 text-gray-300">Running AI analysis...</span>
        </div>
      )}

      {results && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-black/20 rounded-lg p-4"
        >
          <h4 className="text-sm font-medium text-white mb-3">
            Results for {features.find(f => f.id === activeFeature)?.name}
          </h4>
          
          {results.error ? (
            <div className="text-red-300 text-sm">{results.error}</div>
          ) : (
            <div className="space-y-3">
              {/* MR Triage Results */}
              {activeFeature === 'triage' && results.analysis && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded">
                      {results.analysis.risk_level?.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-300">
                      Risk Score: {results.analysis.risk_score}
                    </span>
                  </div>
                  <div className="text-sm text-gray-300">
                    <strong>MR:</strong> {results.mr_title}
                  </div>
                  <div className="text-sm text-gray-300">
                    <strong>Estimated Review Time:</strong> {results.analysis.estimated_review_hours}h
                  </div>
                  {results.analysis.suggested_reviewers && (
                    <div className="text-sm text-gray-300">
                      <strong>Suggested Reviewers:</strong>
                      <div className="mt-1 space-y-1">
                        {results.analysis.suggested_reviewers.slice(0, 2).map((reviewer: any, idx: number) => (
                          <div key={idx} className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded inline-block mr-2">
                            {reviewer.name} ({Math.round(reviewer.confidence * 100)}%)
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Chat Results */}
              {activeFeature === 'chat' && results.responses && (
                <div className="space-y-2">
                  <div className="text-sm text-gray-300">
                    <strong>AI Assistant Ready</strong>
                  </div>
                  <div className="text-xs text-gray-400">
                    Available commands: {results.supported_commands?.slice(0, 3).join(', ')}...
                  </div>
                </div>
              )}

              {/* Generic Results */}
              {!['triage', 'chat'].includes(activeFeature || '') && (
                <div className="text-sm text-gray-300">
                  <pre className="whitespace-pre-wrap text-xs">
                    {JSON.stringify(results, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}

      <div className="mt-4 text-xs text-gray-400">
        Click any feature above to run AI analysis on project {projectName || projectId}
      </div>
    </motion.div>
  );
}; 