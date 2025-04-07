import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import { getInterpolatedCurve } from '../utils/interpolation';

const DemandGraph = ({ 
  points, 
  width = 500, 
  height = 400, 
  onChange,
  maxBorrowing,
  maxInterestRate,
  graphConfig
}) => {
  const svgRef = useRef(null);
  
  useEffect(() => {
    if (!svgRef.current) return;
    
    // Set up scales
    const xScale = d3.scaleLinear()
      .domain([0, maxInterestRate])
      .range([50, width - 20]);
      
    const yScale = d3.scaleLinear()
      .domain([0, maxBorrowing])
      .range([height - 40, 20]);
      
    // Set up SVG and axes
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    
    // Draw axes
    const xAxis = d3.axisBottom(xScale);
    const yAxis = d3.axisLeft(yScale);
    
    svg.append("g")
      .attr("transform", `translate(0, ${height - 40})`)
      .call(xAxis);
      
    svg.append("g")
      .attr("transform", "translate(50, 0)")
      .call(yAxis);
      
    // X-axis label
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", height - 5)
      .style("text-anchor", "middle")
      .text("Interest Rate (%)");
      
    // Y-axis label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", 15)
      .style("text-anchor", "middle")
      .text("Borrowing Amount");
    
    // Sort points for line drawing
    const sortedPoints = [...points].sort((a, b) => a.interestRate - b.interestRate);
    
    // Draw the curve
    const line = d3.line()
      .x(d => xScale(d.interestRate))
      .y(d => yScale(d.borrowingAmount))
      .curve(d3.curveMonotoneX);
      
    svg.append("path")
      .datum(sortedPoints)
      .attr("fill", "none")
      .attr("stroke", "#2196f3")
      .attr("stroke-width", 2)
      .attr("d", line);
      
    // EXTENSION 1: Draw interpolated curve if enabled
    if (graphConfig && graphConfig.showInterpolationCurve) {
      // Generate interpolated points
      const interpolatedPoints = getInterpolatedCurve(points, 0.1);
      
      if (interpolatedPoints.length > 0) {
        // Create a smoother line for interpolated points
        const interpolatedLine = d3.line()
          .x(d => xScale(d.interestRate))
          .y(d => yScale(d.borrowingAmount))
          .curve(d3.curveBasis);
          
        svg.append("path")
          .datum(interpolatedPoints)
          .attr("fill", "none")
          .attr("stroke", "#42A5F5")
          .attr("stroke-width", 1.5)
          .attr("stroke-dasharray", "3,3")
          .attr("d", interpolatedLine);
      }
    }
      
    // Add draggable points
    const pointGroup = svg.append("g")
      .selectAll(".point")
      .data(points)
      .enter()
      .append("g")
      .attr("class", "point");
      
    pointGroup.append("circle")
      .attr("cx", d => xScale(d.interestRate))
      .attr("cy", d => yScale(d.borrowingAmount))
      .attr("r", 8)
      .attr("fill", d => {
        // EXTENSION 3: Visual indicators for points exceeding limits
        const borrowingLimit = graphConfig && graphConfig.borrowingLimit;
        if (borrowingLimit && d.borrowingAmount > borrowingLimit) {
          return "#f44336"; // Red for exceeding limit
        }
        return "#2196f3"; // Default blue
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .call(d3.drag()
        .on("drag", function(event, d) {
          // Update y position (borrowing amount)
          const newY = yScale.invert(Math.max(20, Math.min(height - 40, event.y)));
          d.borrowingAmount = Math.round(newY);
          
          // Redraw the point and curve
          d3.select(this)
            .attr("cy", yScale(d.borrowingAmount))
            .attr("fill", () => {
              // Update color based on borrowing limit
              const borrowingLimit = graphConfig && graphConfig.borrowingLimit;
              if (borrowingLimit && d.borrowingAmount > borrowingLimit) {
                return "#f44336"; // Red for exceeding limit
              }
              return "#2196f3"; // Default blue
            });
            
          // Update the curve
          svg.select("path")
            .datum(sortedPoints)
            .attr("d", line);
            
          // Notify parent of change
          onChange([...points]);
        })
      );
      
    // Labels for points
    pointGroup.append("text")
      .attr("x", d => xScale(d.interestRate))
      .attr("y", d => yScale(d.borrowingAmount) - 15)
      .attr("text-anchor", "middle")
      .text(d => `${d.borrowingAmount}`);
      
    // EXTENSION 2: Economic insights
    if (graphConfig && graphConfig.showEconomicInsight) {
      // Check if curve is not downward sloping (unusual for demand)
      let isUpwardSloping = false;
      for (let i = 1; i < sortedPoints.length; i++) {
        if (sortedPoints[i].borrowingAmount > sortedPoints[i-1].borrowingAmount) {
          isUpwardSloping = true;
          break;
        }
      }
      
      if (isUpwardSloping) {
        // Add insight about downward sloping demand curves
        svg.append("g")
          .attr("class", "economic-insight")
          .attr("transform", `translate(${width - 200}, 30)`)
          .append("rect")
          .attr("width", 190)
          .attr("height", 80)
          .attr("fill", "#FFF9C4")
          .attr("rx", 5)
          .attr("ry", 5)
          .attr("stroke", "#FFD600")
          .attr("stroke-width", 1);
        
        svg.select(".economic-insight")
          .append("text")
          .attr("x", 10)
          .attr("y", 20)
          .attr("fill", "#F57F17")
          .text("Economic Insight:")
          .append("tspan")
          .attr("x", 10)
          .attr("dy", "1.2em")
          .text("Demand curves typically")
          .append("tspan")
          .attr("x", 10)
          .attr("dy", "1.2em")
          .text("slope downward. Higher rates")
          .append("tspan")
          .attr("x", 10)
          .attr("dy", "1.2em")
          .text("→ lower borrowing.");
      }
      
      // Check if any points exceed borrowing limit
      const borrowingLimit = graphConfig && graphConfig.borrowingLimit;
      if (borrowingLimit) {
        const exceedingPoints = points.filter(p => p.borrowingAmount > borrowingLimit);
        
        if (exceedingPoints.length > 0) {
          // Add insight about exceeding borrowing limits
          const yPosition = isUpwardSloping ? 120 : 30;
          
          svg.append("g")
            .attr("class", "economic-insight-limit")
            .attr("transform", `translate(${width - 200}, ${yPosition})`)
            .append("rect")
            .attr("width", 190)
            .attr("height", 80)
            .attr("fill", "#FFEBEE")
            .attr("rx", 5)
            .attr("ry", 5)
            .attr("stroke", "#FFCDD2")
            .attr("stroke-width", 1);
          
          svg.select(".economic-insight-limit")
            .append("text")
            .attr("x", 10)
            .attr("y", 20)
            .attr("fill", "#C62828")
            .text("Economic Insight:")
            .append("tspan")
            .attr("x", 10)
            .attr("dy", "1.2em")
            .text("Your borrowing exceeds")
            .append("tspan")
            .attr("x", 10)
            .attr("dy", "1.2em")
            .text("the current limit at some")
            .append("tspan")
            .attr("x", 10)
            .attr("dy", "1.2em")
            .text("interest rates.");
        }
      }
      
      // Add insight for very high borrowing (relative to max)
      const maxBorrowingAmount = Math.max(...points.map(p => p.borrowingAmount));
      if (maxBorrowingAmount > maxBorrowing * 0.9) {
        const yPosition = isUpwardSloping ? (borrowingLimit ? 210 : 120) : (borrowingLimit ? 120 : 30);
        
        svg.append("g")
          .attr("class", "economic-insight-high")
          .attr("transform", `translate(${width - 200}, ${yPosition})`)
          .append("rect")
          .attr("width", 190)
          .attr("height", 80)
          .attr("fill", "#E0F7FA")
          .attr("rx", 5)
          .attr("ry", 5)
          .attr("stroke", "#B2EBF2")
          .attr("stroke-width", 1);
        
        svg.select(".economic-insight-high")
          .append("text")
          .attr("x", 10)
          .attr("y", 20)
          .attr("fill", "#006064")
          .text("Economic Insight:")
          .append("tspan")
          .attr("x", 10)
          .attr("dy", "1.2em")
          .text("Very high borrowing may")
          .append("tspan")
          .attr("x", 10)
          .attr("dy", "1.2em")
          .text("lead to repayment issues")
          .append("tspan")
          .attr("x", 10)
          .attr("dy", "1.2em")
          .text("in future periods.");
      }
    }
      
  }, [points, width, height, maxBorrowing, maxInterestRate, onChange, graphConfig]);
  
  return (
    <div className="demand-graph-container">
      <svg 
        ref={svgRef}
        width={width} 
        height={height}
        className="demand-graph"
      />
    </div>
  );
};

export default DemandGraph; 