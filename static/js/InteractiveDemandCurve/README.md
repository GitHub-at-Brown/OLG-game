# Interactive Demand Curve Component

A React component that allows students to create and manipulate their borrowing demand curve for the OLG economic simulation game.

## Features

- Interactive graph where students can drag points to define their borrowing demand curve
- Tabular data entry for precise control of borrowing amounts
- Real-time visual feedback
- Responsive design that works on both desktop and mobile devices
- Support for setting borrowing limits and other constraints

## Installation

1. Install the package in your project:

```bash
npm install --save d3@7.8.5
```

2. Copy the `InteractiveDemandCurve` directory into your project

## Usage

```jsx
import React from 'react';
import InteractiveDemandCurve from './InteractiveDemandCurve';

// For the Young stage of the game
const YoungPlayerInterface = ({ currentBorrowingLimit, onSubmitBorrowingSchedule }) => {
  return (
    <div className="young-player-interface">
      <h1>You are Young</h1>
      
      <div className="game-info">
        {/* Display other game information */}
      </div>
      
      <InteractiveDemandCurve
        initialPoints={[
          { interestRate: 1, borrowingAmount: 50 },
          { interestRate: 2, borrowingAmount: 45 },
          { interestRate: 3, borrowingAmount: 38 },
          { interestRate: 5, borrowingAmount: 25 },
          { interestRate: 7, borrowingAmount: 15 },
          { interestRate: 10, borrowingAmount: 5 },
        ]}
        config={{
          minInterestRate: 0,
          maxInterestRate: 12,
          minBorrowing: 0,
          maxBorrowing: 60,
          gridStep: 1,
        }}
        onSubmit={onSubmitBorrowingSchedule}
        currentBorrowingLimit={currentBorrowingLimit}
        width={600}
        height={450}
      />
    </div>
  );
};

export default YoungPlayerInterface;
```

## Component Props

| Prop | Type | Description |
|------|------|-------------|
| `initialPoints` | Array | Initial set of points for the demand curve |
| `config` | Object | Configuration options for the graph (see below) |
| `onSubmit` | Function | Callback when student submits their borrowing schedule |
| `currentBorrowingLimit` | Number | The current borrowing limit to display |
| `width` | Number | Width of the graph in pixels |
| `height` | Number | Height of the graph in pixels |

### Config Options

| Option | Type | Description |
|--------|------|-------------|
| `minInterestRate` | Number | Minimum interest rate to display on the x-axis |
| `maxInterestRate` | Number | Maximum interest rate to display on the x-axis |
| `minBorrowing` | Number | Minimum borrowing amount to display on the y-axis |
| `maxBorrowing` | Number | Maximum borrowing amount to display on the y-axis |
| `gridStep` | Number | Step size for grid lines |
| `interpolationMethod` | String | Method for interpolating between points ('linear' or 'curveMonotoneX') |

## Server Integration

When a student submits their borrowing schedule, the `onSubmit` callback will be called with an array of points:

```javascript
[
  { interestRate: 1, borrowingAmount: 50 },
  { interestRate: 2, borrowingAmount: 45 },
  { interestRate: 3, borrowingAmount: 38 },
  { interestRate: 5, borrowingAmount: 25 },
  { interestRate: 7, borrowingAmount: 15 },
  { interestRate: 10, borrowingAmount: 5 },
]
```

The server should:

1. Store this schedule for each student
2. When all students have submitted, use these demand curves to calculate the equilibrium interest rate
3. Determine each student's actual borrowing based on their demand at the equilibrium rate
4. Update the game state accordingly

## Demo

To run the demo:

```bash
cd InteractiveDemandCurve
npm install
npm start
```

Then open your browser to `http://localhost:8080` to see the interactive demand curve in action.

## License

MIT 