import React from 'react';
import { useDemandCurve } from './DemandCurveContext';

const DataPointList = () => {
  const { points, updatePoint } = useDemandCurve();
  
  const handleBorrowingChange = (index, value) => {
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue)) {
      updatePoint(index, { borrowingAmount: numValue });
    }
  };
  
  return (
    <div className="data-point-list">
      <h3>Your Borrowing Schedule</h3>
      <table>
        <thead>
          <tr>
            <th>Interest Rate (%)</th>
            <th>Borrowing Amount</th>
          </tr>
        </thead>
        <tbody>
          {points.map((point, index) => (
            <tr key={index}>
              <td>{point.interestRate}%</td>
              <td>
                <input
                  type="number"
                  min="0"
                  value={point.borrowingAmount}
                  onChange={(e) => handleBorrowingChange(index, e.target.value)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataPointList; 