/**
 * Utility functions for interpolating between demand curve points
 */

/**
 * Linear interpolation between two points
 * @param {number} x - Interest rate to interpolate at
 * @param {Object} p1 - First point {interestRate, borrowingAmount}
 * @param {Object} p2 - Second point {interestRate, borrowingAmount}
 * @returns {number} Interpolated borrowing amount
 */
export const linearInterpolate = (x, p1, p2) => {
  // If x is outside the range, return the closest value
  if (x <= p1.interestRate) return p1.borrowingAmount;
  if (x >= p2.interestRate) return p2.borrowingAmount;
  
  // Linear interpolation formula: y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
  const t = (x - p1.interestRate) / (p2.interestRate - p1.interestRate);
  return p1.borrowingAmount + t * (p2.borrowingAmount - p1.borrowingAmount);
};

/**
 * Get the full interpolated demand curve
 * @param {Array} points - Array of {interestRate, borrowingAmount} points
 * @param {number} step - Step size for interpolation (e.g., 0.1)
 * @param {Function} method - Interpolation method (default: linearInterpolate)
 * @returns {Array} Array of interpolated points
 */
export const getInterpolatedCurve = (points, step = 0.1, method = linearInterpolate) => {
  if (!points || points.length < 2) return points || [];
  
  // Sort points by interest rate
  const sortedPoints = [...points].sort((a, b) => a.interestRate - b.interestRate);
  
  const result = [];
  const minRate = sortedPoints[0].interestRate;
  const maxRate = sortedPoints[sortedPoints.length - 1].interestRate;
  
  // Generate points at regular intervals
  for (let rate = minRate; rate <= maxRate; rate += step) {
    // Find the two surrounding points
    let i = 0;
    while (i < sortedPoints.length - 1 && sortedPoints[i + 1].interestRate < rate) {
      i++;
    }
    
    if (i === sortedPoints.length - 1) {
      // We're at the end
      result.push({
        interestRate: rate,
        borrowingAmount: sortedPoints[i].borrowingAmount
      });
    } else if (Math.abs(rate - sortedPoints[i].interestRate) < 0.001) {
      // We're exactly at a known point
      result.push({
        interestRate: rate,
        borrowingAmount: sortedPoints[i].borrowingAmount
      });
    } else {
      // Interpolate
      result.push({
        interestRate: rate,
        borrowingAmount: method(rate, sortedPoints[i], sortedPoints[i + 1])
      });
    }
  }
  
  return result;
}; 