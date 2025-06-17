import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface ProjectSelectorProps {
  currentProjectId: number;
  onProjectChange: (projectId: number) => void;
  projectName?: string;
}

export const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  currentProjectId,
  onProjectChange,
  projectName
}) => {
  const [inputValue, setInputValue] = useState(currentProjectId.toString());
  const [isEditing, setIsEditing] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newProjectId = parseInt(inputValue);
    if (!isNaN(newProjectId) && newProjectId > 0) {
      onProjectChange(newProjectId);
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setInputValue(currentProjectId.toString());
    setIsEditing(false);
  };

  return (
    <div className="space-y-4">
      {/* Current Project Display */}
      <div className="glass-light rounded-xl p-4 border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg flex items-center justify-center border border-blue-200">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 00-2 2v2a2 2 0 002 2m0 0h14m-14 0a2 2 0 002 2v2a2 2 0 01-2 2M5 9V7a2 2 0 012-2h12a2 2 0 012 2v2M7 13h10v-2H7v2z" />
              </svg>
            </div>
            <div>
              <div className="text-light-primary font-semibold mono">
                Project #{currentProjectId}
              </div>
              <div className="text-light-secondary text-sm">
                {projectName || 'Loading project details...'}
              </div>
            </div>
          </div>
          
          <button
            onClick={() => setIsEditing(true)}
            className="btn-light px-4 py-2 rounded-lg text-sm font-medium focus-light"
          >
            Change
          </button>
        </div>
      </div>

      {/* Edit Form */}
      {isEditing && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="glass-light rounded-xl p-4 border border-purple-200 shadow-sm"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-light-secondary mb-2">
                Enter New Project ID
              </label>
              <input
                type="number"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-light-primary placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all mono font-medium"
                placeholder="Enter project ID..."
                autoFocus
                min="1"
              />
            </div>
            
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={!inputValue || parseInt(inputValue) <= 0}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold"
              >
                Switch Project
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="btn-light px-4 py-3 rounded-lg transition-all duration-200 font-medium focus-light"
              >
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => {
            setInputValue('278964');
            onProjectChange(278964);
          }}
          className="p-4 glass-light rounded-lg card-hover-light transition-all duration-200 text-left border border-gray-200 shadow-sm focus-light"
        >
          <div className="text-light-secondary text-sm font-semibold">GitLab Demo</div>
          <div className="text-light-muted text-xs mono">#278964</div>
        </button>
        
        <button
          onClick={() => {
            setInputValue(currentProjectId.toString());
            onProjectChange(currentProjectId);
          }}
          className="p-4 glass-light rounded-lg card-hover-light transition-all duration-200 text-left border border-gray-200 shadow-sm focus-light"
        >
          <div className="text-light-secondary text-sm font-semibold">Refresh</div>
          <div className="text-light-muted text-xs">Reload current</div>
        </button>
      </div>
    </div>
  );
}; 