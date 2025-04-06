import React, { useState } from 'react';
import InteractiveDemandCurve from './index';
import './styles.css';

const DemandCurveDemo = () => {
  const [submittedPoints, setSubmittedPoints] = useState(null);
  const [currentBorrowingLimit, setCurrentBorrowingLimit] = useState(50);
  
  const handleSubmit = (points) => {
    console.log('Submitted points:', points);
    setSubmittedPoints(points);
    
    // Simulate finding equilibrium interest rate
    // In a real app, this would be done on the server with all students' data
    setTimeout(() => {
      alert('Borrowing schedule submitted! The equilibrium interest rate will be calculated by the server.');
    }, 500);
  };
  
  return (
    <div className="demand-curve-demo">
      <h1>Borrowing Demand Curve Demo</h1>
      
      <div className="demo-controls">
        <div>
          <label htmlFor="borrowing-limit">Current Borrowing Limit:</label>
          <input 
            type="number" 
            id="borrowing-limit"
            value={currentBorrowingLimit}
            onChange={(e) => setCurrentBorrowingLimit(Number(e.target.value))}
            min="0"
          />
        </div>
      </div>
      
      <InteractiveDemandCurve 
        onSubmit={handleSubmit}
        currentBorrowingLimit={currentBorrowingLimit}
      />
      
      {submittedPoints && (
        <div className="submission-result">
          <h3>Submitted Borrowing Schedule:</h3>
          <table>
            <thead>
              <tr>
                <th>Interest Rate (%)</th>
                <th>Borrowing Amount</th>
              </tr>
            </thead>
            <tbody>
              {submittedPoints.map((point, index) => (
                <tr key={index}>
                  <td>{point.interestRate}%</td>
                  <td>{point.borrowingAmount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      <div className="integration-instructions">
        <h3>Integration Notes:</h3>
        <p>
          This component can be integrated with the main app by:
        </p>
        <ol>
          <li>Importing the InteractiveDemandCurve component</li>
          <li>Using it in place of the existing Young player borrowing input</li>
          <li>Implementing an onSubmit handler that sends the demand schedule to the server</li>
          <li>Updating the server to calculate equilibrium based on all students' demand curves</li>
        </ol>
      </div>
    </div>
  );
};

export default DemandCurveDemo; 