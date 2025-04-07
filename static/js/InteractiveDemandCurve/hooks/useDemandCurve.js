import { useContext } from 'react';
import { DemandCurveContext } from '../components/DemandCurveContext';

// This is just a re-export of the context hook for convenience
const useDemandCurve = () => {
  const context = useContext(DemandCurveContext);
  
  if (context === undefined) {
    throw new Error('useDemandCurve must be used within a DemandCurveProvider');
  }
  
  return context;
};

export default useDemandCurve; 