/**
 * Utility functions for validating demand curve inputs
 */

/**
 * Validates if a borrowing amount is within allowed limits
 * @param {number} amount - The borrowing amount to validate
 * @param {number} borrowingLimit - The maximum allowed borrowing
 * @returns {boolean} Whether the borrowing amount is valid
 */
export const isValidBorrowingAmount = (amount, borrowingLimit) => {
  return amount >= 0 && amount <= borrowingLimit;
};

/**
 * Validates a complete demand curve for common issues
 * @param {Array} points - Array of {interestRate, borrowingAmount} points
 * @param {Object} config - Configuration object with validation rules
 * @returns {Object} Validation result {isValid, errors}
 */
export const validateDemandCurve = (points, config = {}) => {
  const errors = [];
  
  // Check if there are enough points
  if (!points || points.length < 2) {
    errors.push('At least two points are required to define a demand curve');
  }
  
  if (!points || points.length === 0) {
    return { isValid: false, errors };
  }
  
  // Check for negative borrowing amounts
  const negativePoints = points.filter(p => p.borrowingAmount < 0);
  if (negativePoints.length > 0) {
    errors.push('Borrowing amounts cannot be negative');
  }
  
  // Check for duplicate interest rates
  const interestRates = points.map(p => p.interestRate);
  const uniqueRates = new Set(interestRates);
  if (uniqueRates.size !== points.length) {
    errors.push('Each interest rate can only have one borrowing amount');
  }
  
  // Check if the curve is downward sloping (reasonable demand curve)
  const sortedPoints = [...points].sort((a, b) => a.interestRate - b.interestRate);
  let isDownwardSloping = true;
  
  for (let i = 1; i < sortedPoints.length; i++) {
    if (sortedPoints[i].borrowingAmount > sortedPoints[i-1].borrowingAmount) {
      isDownwardSloping = false;
      break;
    }
  }
  
  if (!isDownwardSloping && config.requireDownwardSloping) {
    errors.push('A demand curve should be downward sloping (higher interest rates should lead to lower borrowing)');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}; 