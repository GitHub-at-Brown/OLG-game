/**
 * Utility functions for mathematical operations on demand curves
 */

import { linearInterpolate } from './interpolation';

/**
 * Calculates borrowing amount at a specific interest rate
 * @param {Array} points - Array of {interestRate, borrowingAmount} points
 * @param {number} targetRate - Interest rate to find borrowing amount for
 * @returns {number|null} Interpolated borrowing amount or null if out of range
 */
export const getBorrowingAtRate = (points, targetRate) => {
  if (!points || points.length === 0) return null;
  
  // Sort points by interest rate
  const sortedPoints = [...points].sort((a, b) => a.interestRate - b.interestRate);
  
  // Check if target rate is outside the range of defined points
  if (targetRate < sortedPoints[0].interestRate || 
      targetRate > sortedPoints[sortedPoints.length - 1].interestRate) {
    return null;
  }
  
  // Find the two points surrounding the target rate
  for (let i = 0; i < sortedPoints.length - 1; i++) {
    const p1 = sortedPoints[i];
    const p2 = sortedPoints[i + 1];
    
    if (Math.abs(targetRate - p1.interestRate) < 0.001) {
      // Exact match
      return p1.borrowingAmount;
    }
    
    if (Math.abs(targetRate - p2.interestRate) < 0.001) {
      // Exact match
      return p2.borrowingAmount;
    }
    
    if (targetRate > p1.interestRate && targetRate < p2.interestRate) {
      // Interpolate
      return linearInterpolate(targetRate, p1, p2);
    }
  }
  
  return null;
};

/**
 * Calculates the total borrowing across all interest rates
 * @param {Array} points - Array of {interestRate, borrowingAmount} points
 * @param {number} step - Step size for interpolation
 * @returns {number} Total area under the curve (approximate)
 */
export const calculateTotalBorrowing = (points, step = 0.1) => {
  if (!points || points.length < 2) return 0;
  
  // Sort points by interest rate
  const sortedPoints = [...points].sort((a, b) => a.interestRate - b.interestRate);
  
  let totalBorrowing = 0;
  const minRate = sortedPoints[0].interestRate;
  const maxRate = sortedPoints[sortedPoints.length - 1].interestRate;
  
  // Simple trapezoid rule integration
  for (let rate = minRate; rate < maxRate; rate += step) {
    const b1 = getBorrowingAtRate(sortedPoints, rate);
    const b2 = getBorrowingAtRate(sortedPoints, rate + step);
    
    if (b1 !== null && b2 !== null) {
      // Trapezoid area = average height * width
      totalBorrowing += ((b1 + b2) / 2) * step;
    }
  }
  
  return totalBorrowing;
};

/**
 * Finds the interest rate at which borrowing equals a target value
 * @param {Array} points - Array of {interestRate, borrowingAmount} points
 * @param {number} targetBorrowing - Target borrowing amount
 * @returns {number|null} Interest rate or null if no solution
 */
export const findInterestRateForBorrowing = (points, targetBorrowing) => {
  if (!points || points.length < 2) return null;
  
  // Sort points by interest rate
  const sortedPoints = [...points].sort((a, b) => a.interestRate - b.interestRate);
  
  // Check if target is outside the range of possible borrowing amounts
  const minBorrowing = Math.min(...sortedPoints.map(p => p.borrowingAmount));
  const maxBorrowing = Math.max(...sortedPoints.map(p => p.borrowingAmount));
  
  if (targetBorrowing < minBorrowing || targetBorrowing > maxBorrowing) {
    return null;
  }
  
  // Find the two points surrounding the target borrowing
  for (let i = 0; i < sortedPoints.length - 1; i++) {
    const p1 = sortedPoints[i];
    const p2 = sortedPoints[i + 1];
    
    if (Math.abs(targetBorrowing - p1.borrowingAmount) < 0.001) {
      // Exact match
      return p1.interestRate;
    }
    
    if (Math.abs(targetBorrowing - p2.borrowingAmount) < 0.001) {
      // Exact match
      return p2.interestRate;
    }
    
    // For a typical demand curve, borrowing decreases as interest rate increases
    if ((p1.borrowingAmount >= targetBorrowing && p2.borrowingAmount <= targetBorrowing) || 
        (p1.borrowingAmount <= targetBorrowing && p2.borrowingAmount >= targetBorrowing)) {
      // Linear interpolation: x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
      const t = (targetBorrowing - p1.borrowingAmount) / (p2.borrowingAmount - p1.borrowingAmount);
      return p1.interestRate + t * (p2.interestRate - p1.interestRate);
    }
  }
  
  return null;
}; 