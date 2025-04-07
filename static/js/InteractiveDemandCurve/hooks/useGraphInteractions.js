import { useCallback } from 'react';

// Hook for handling graph interactions (mouse/touch)
const useGraphInteractions = (xScale, yScale, updatePoints) => {
  
  // Handle point dragging
  const handlePointDrag = useCallback(
    (event, index, points) => {
      const newPoints = [...points];
      const newY = yScale.invert(event.y);
      
      // Ensure borrowing amount stays within valid range
      newPoints[index].borrowingAmount = Math.max(0, Math.round(newY));
      
      updatePoints(newPoints);
      return newPoints;
    },
    [yScale, updatePoints]
  );
  
  // Handle click on graph to potentially add a new point
  const handleGraphClick = useCallback(
    (event, points) => {
      const x = xScale.invert(event.x);
      const y = yScale.invert(event.y);
      
      // Round to reasonable values
      const interestRate = Math.round(x * 10) / 10;
      const borrowingAmount = Math.round(y);
      
      // Check if a point at this interest rate already exists
      const existingPointIndex = points.findIndex(
        p => Math.abs(p.interestRate - interestRate) < 0.1
      );
      
      if (existingPointIndex >= 0) {
        // Update existing point
        const newPoints = [...points];
        newPoints[existingPointIndex].borrowingAmount = borrowingAmount;
        updatePoints(newPoints);
        return newPoints;
      } else {
        // Add new point
        const newPoint = { interestRate, borrowingAmount };
        const newPoints = [...points, newPoint].sort(
          (a, b) => a.interestRate - b.interestRate
        );
        updatePoints(newPoints);
        return newPoints;
      }
    },
    [xScale, yScale, updatePoints]
  );
  
  return {
    handlePointDrag,
    handleGraphClick,
  };
};

export default useGraphInteractions; 