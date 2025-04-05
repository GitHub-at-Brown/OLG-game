/**
 * Main JavaScript file for the OLG Classroom Game
 * Contains common functionality and utilities
 */

// Format numbers with a specified number of decimal places
function formatNumber(number, decimals = 1) {
    return Number(number).toFixed(decimals);
}

// Format percentages (e.g., 0.03 -> "3.0%")
function formatPercent(number, decimals = 1) {
    return (Number(number) * 100).toFixed(decimals) + '%';
}

// Calculate utility from consumption (log utility)
function calculateUtility(consumption) {
    return Math.log(Math.max(consumption, 0.1)); // Avoid log(0)
}

// Format utility for display
function formatUtility(utility) {
    return Number(utility).toFixed(2);
}

// Show notification to the user
function showNotification(message, type = 'info') {
    // Check if the notification container exists
    let container = document.getElementById('notification-container');
    
    // Create it if it doesn't exist
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.role = 'alert';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300); // Allow fade animation to complete
    }, 5000);
}

// Utility function to validate numeric input
function validateNumericInput(input, min = null, max = null) {
    let value = parseFloat(input.value);
    
    if (isNaN(value)) {
        input.value = '0';
        return 0;
    }
    
    if (min !== null && value < min) {
        input.value = min;
        return min;
    }
    
    if (max !== null && value > max) {
        input.value = max;
        return max;
    }
    
    return value;
}

// Add event listener for handling numeric input validation
document.addEventListener('DOMContentLoaded', function() {
    const numericInputs = document.querySelectorAll('input[type="number"]');
    
    numericInputs.forEach(input => {
        const min = input.hasAttribute('min') ? parseFloat(input.getAttribute('min')) : null;
        const max = input.hasAttribute('max') ? parseFloat(input.getAttribute('max')) : null;
        
        input.addEventListener('blur', () => {
            validateNumericInput(input, min, max);
        });
    });
});
