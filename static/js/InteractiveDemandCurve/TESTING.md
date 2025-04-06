# Testing the Interactive Demand Curve Component

This document provides instructions for testing the Interactive Demand Curve component.

## Running the Test Page

1. Make sure you have all the files in the InteractiveDemandCurve directory:
   - Components in the `components/` directory
   - Utility functions in the `utils/` directory
   - `styles.css`
   - `test.html`
   - `test.js`

2. Open the `test.html` file in a modern browser (Chrome, Firefox, Safari, or Edge):
   - **Option 1**: Simply double-click the file to open it in your default browser
   - **Option 2**: Start a local server (recommended) and access the file through localhost
   - **Option 3**: Use an extension like "Live Server" in VS Code

   > **Important**: Some browsers may restrict loading local files due to security settings. If you don't see the interactive graph or encounter console errors, use a local server to serve the files.

## Running a Simple Local Server

If you have Node.js installed, you can run a simple HTTP server:

1. Open a terminal or command prompt
2. Navigate to the directory containing InteractiveDemandCurve
3. Run one of these commands:

```bash
# If you have Python installed:
python -m http.server 8000  # Python 3
python -m SimpleHTTPServer 8000  # Python 2

# If you have Node.js installed:
npx http-server -p 8000
```

4. Open your browser and navigate to: `http://localhost:8000/InteractiveDemandCurve/test.html`

## What You Should See

When the test page loads correctly, you should see:

1. The main Interactive Demand Curve interface with:
   - A graph showing the demand curve with draggable points
   - A table of interest rates and borrowing amounts
   - Extension controls (Show Interpolated Curve, Show Economic Insights)
   - A borrowing limit input and submit button

2. Testing sections explaining how to test each feature
3. A console output area that shows logs from interactions

## Testing the Features

1. **Basic Functionality**:
   - Drag points up and down on the graph and observe the curve updating
   - Edit values in the table and see the graph update

2. **Interpolated Curve**:
   - Toggle the "Show Interpolated Curve" checkbox
   - Verify that a dotted line appears showing the smoothed curve

3. **Economic Insights**:
   - Toggle the "Show Economic Insights" checkbox
   - Create an upward-sloping curve (move a point higher than its left neighbor)
   - Create very high borrowing amounts (near the top of the graph)
   - Verify that appropriate insight boxes appear

4. **Borrowing Limit Indicators**:
   - Adjust the borrowing limit input at the top
   - Move points above the borrowing limit
   - Verify that points turn red when exceeding the limit
   - Verify that warning messages appear

5. **Data Submission**:
   - Click the "Submit Borrowing Schedule" button
   - Verify that the submitted data appears in the test results section

## Running Automated Tests

Click the "Run All Tests" button to execute the test script from `test.js`. The console output area will show logs of test execution.

## Troubleshooting

If the test page doesn't display properly:

1. Check the browser console for errors (F12 or right-click > Inspect > Console)
2. Make sure all files are present and in the correct directory structure
3. Try using a local server instead of opening the file directly
4. Make sure you have internet access for loading the CDN dependencies (React, D3)
5. Try a different modern browser 