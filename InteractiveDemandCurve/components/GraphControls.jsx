import React from 'react';
import { useDemandCurve } from './DemandCurveContext';

const GraphControls = () => {
  const { resetPoints, graphConfig, updateGraphConfig } = useDemandCurve();
  
  const toggleInterpolation = () => {
    updateGraphConfig({ 
      showInterpolationCurve: !graphConfig.showInterpolationCurve 
    });
  };
  
  const toggleEconomicInsight = () => {
    updateGraphConfig({ 
      showEconomicInsight: !graphConfig.showEconomicInsight 
    });
  };
  
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
            onChange={toggleInterpolation}
          />
          <span>Show Interpolated Curve</span>
        </label>
        
        <label className="extension-control">
          <input 
            type="checkbox" 
            checked={graphConfig.showEconomicInsight || false}
            onChange={toggleEconomicInsight}
          />
          <span>Show Economic Insights</span>
        </label>
      </div>
      
      <div className="instructions">
        <p>Drag the blue points up or down to adjust your borrowing amount at each interest rate.</p>
        {graphConfig.borrowingLimit && (
          <p className="limit-info">Red points indicate borrowing amounts that exceed your current limit.</p>
        )}
      </div>
    </div>
  );
};

export default GraphControls; 