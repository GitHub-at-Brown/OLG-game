import React, { useContext, useEffect } from 'react';
import { DemandCurveProvider, useDemandCurve } from './components/DemandCurveContext';
import DemandGraph from './components/DemandGraph';
import GraphControls from './components/GraphControls';
import DataPointList from './components/DataPointList';
import './styles.css';

// Default initial points if none provided
const DEFAULT_POINTS = [
  { interestRate: 1, borrowingAmount: 50 },
  { interestRate: 2, borrowingAmount: 45 },
  { interestRate: 3, borrowingAmount: 38 },
  { interestRate: 5, borrowingAmount: 25 },
  { interestRate: 7, borrowingAmount: 15 },
  { interestRate: 10, borrowingAmount: 5 },
];

// Default graph configuration
const DEFAULT_CONFIG = {
  minInterestRate: 0,
  maxInterestRate: 12,
  minBorrowing: 0,
  maxBorrowing: 60,
  gridStep: 1,
  interpolationMethod: 'linear',
  // Extension options
  showInterpolationCurve: false,
  showEconomicInsight: false,
  borrowingLimit: null
};

/**
 * Interactive Demand Curve component
 * Allows users to create and modify a borrowing demand curve
 */
const InteractiveDemandCurve = ({ 
  initialPoints = DEFAULT_POINTS,
  config = DEFAULT_CONFIG,
  onSubmit,
  currentBorrowingLimit,
  width = 600,
  height = 450
}) => {
  // Merge provided config with defaults
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };
  
  return (
    <DemandCurveProvider initialPoints={initialPoints} config={mergedConfig}>
      <InteractiveDemandCurveInner
        onSubmit={onSubmit}
        currentBorrowingLimit={currentBorrowingLimit}
        width={width}
        height={height}
      />
    </DemandCurveProvider>
  );
};

// Inner component that can access context
const InteractiveDemandCurveInner = ({ 
  onSubmit,
  currentBorrowingLimit,
  width,
  height
}) => {
  const { points, graphConfig, updateGraphConfig } = useDemandCurve();
  
  // Update borrowing limit in config when it changes
  useEffect(() => {
    if (currentBorrowingLimit !== undefined && currentBorrowingLimit !== null) {
      updateGraphConfig({ borrowingLimit: currentBorrowingLimit });
    }
  }, [currentBorrowingLimit, updateGraphConfig]);
  
  const handleSubmit = () => {
    if (onSubmit) {
      onSubmit(points);
    }
  };
  
  return (
    <div className="interactive-demand-curve">
      <h2>Your Borrowing Demand Curve</h2>
      
      <div className="demand-curve-container">
        <div className="graph-section">
          <DemandGraphWithContext 
            width={width}
            height={height}
          />
          <GraphControlsWithExtensions />
        </div>
        
        <div className="data-section">
          <DataPointList />
          
          {currentBorrowingLimit && (
            <div className="borrowing-limit-info">
              <p>Current borrowing limit: {currentBorrowingLimit}</p>
              
              {/* Extension: Show warning if any point exceeds borrowing limit */}
              {points.some(p => p.borrowingAmount > currentBorrowingLimit) && (
                <p className="borrowing-limit-warning">
                  Warning: Some of your borrowing amounts exceed the current limit.
                  Points exceeding the limit are shown in red.
                </p>
              )}
            </div>
          )}
          
          <button 
            className="submit-button"
            onClick={handleSubmit}
          >
            Submit Borrowing Schedule
          </button>
        </div>
      </div>
    </div>
  );
};

// Extended Controls Component
const GraphControlsWithExtensions = () => {
  const { resetPoints, graphConfig, updateGraphConfig } = useDemandCurve();
  
  return (
    <div className="graph-controls">
      <button 
        onClick={resetPoints}
        className="reset-button"
      >
        Reset Curve
      </button>
      
      <div className="extension-controls">
        <label className="extension-control">
          <input 
            type="checkbox" 
            checked={graphConfig.showInterpolationCurve || false}
            onChange={(e) => updateGraphConfig({ showInterpolationCurve: e.target.checked })}
          />
          <span>Show Interpolated Curve</span>
        </label>
        
        <label className="extension-control">
          <input 
            type="checkbox" 
            checked={graphConfig.showEconomicInsight || false}
            onChange={(e) => updateGraphConfig({ showEconomicInsight: e.target.checked })}
          />
          <span>Show Economic Insights</span>
        </label>
      </div>
      
      <div className="instructions">
        <p>Drag the blue points up or down to adjust your borrowing amount at each interest rate.</p>
      </div>
    </div>
  );
};

// Wrapper for DemandGraph that connects to context and adds extensions
const DemandGraphWithContext = ({ width, height }) => {
  const { points, graphConfig, updatePoints } = useDemandCurve();
  
  return (
    <DemandGraph
      points={points}
      width={width}
      height={height}
      onChange={updatePoints}
      maxBorrowing={graphConfig.maxBorrowing}
      maxInterestRate={graphConfig.maxInterestRate}
      graphConfig={graphConfig}
    />
  );
};

export default InteractiveDemandCurve; 