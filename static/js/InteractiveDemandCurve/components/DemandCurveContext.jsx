import React, { createContext, useState, useContext } from 'react';

const DemandCurveContext = createContext();

export const DemandCurveProvider = ({ children, initialPoints, config }) => {
  const [points, setPoints] = useState(initialPoints || [
    { interestRate: 1, borrowingAmount: 50 },
    { interestRate: 2, borrowingAmount: 45 },
    { interestRate: 3, borrowingAmount: 38 },
    { interestRate: 5, borrowingAmount: 25 },
    { interestRate: 7, borrowingAmount: 15 },
    { interestRate: 10, borrowingAmount: 5 },
  ]);
  
  const [graphConfig, setGraphConfig] = useState(config || {
    minInterestRate: 0,
    maxInterestRate: 12,
    minBorrowing: 0,
    maxBorrowing: 60,
    gridStep: 1,
    interpolationMethod: 'linear'
  });
  
  const updatePoint = (index, newValues) => {
    const newPoints = [...points];
    newPoints[index] = { ...newPoints[index], ...newValues };
    setPoints(newPoints);
  };
  
  const updatePoints = (newPoints) => {
    setPoints(newPoints);
  };
  
  const resetPoints = () => {
    setPoints(initialPoints || [
      { interestRate: 1, borrowingAmount: 50 },
      { interestRate: 2, borrowingAmount: 45 },
      { interestRate: 3, borrowingAmount: 38 },
      { interestRate: 5, borrowingAmount: 25 },
      { interestRate: 7, borrowingAmount: 15 },
      { interestRate: 10, borrowingAmount: 5 },
    ]);
  };
  
  return (
    <DemandCurveContext.Provider
      value={{
        points,
        graphConfig,
        updatePoint,
        updatePoints,
        resetPoints,
        setGraphConfig
      }}
    >
      {children}
    </DemandCurveContext.Provider>
  );
};

export const useDemandCurve = () => useContext(DemandCurveContext); 