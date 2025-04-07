$('#policy-form').submit(function(e) {
    e.preventDefault();
    
    const taxYoung = parseFloat($('#tax-young').val());
    const taxMiddle = parseFloat($('#tax-middle').val());
    const taxOld = parseFloat($('#tax-old').val());
    const pensionRate = parseFloat($('#pension-rate').val());
    const borrowingLimit = parseFloat($('#borrowing-limit').val()); // Debt limit value
    const targetStock = parseFloat($('#target-stock').val());
    const numTestPlayers = parseInt($('#num-test-players').val());
    
    // Get income parameters
    const incomeYoung = parseFloat($('#income-young').val());
    const incomeMiddle = parseFloat($('#income-middle').val());
    const incomeOld = parseFloat($('#income-old').val());
    
    fetch('/api/set_policy', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tax_rates: {
                young: taxYoung,
                middle: taxMiddle,
                old: taxOld
            },
            pension_rate: pensionRate,
            borrowing_limit: borrowingLimit,
            target_stock: targetStock,
            num_test_players: numTestPlayers,
            // Add income parameters
            income_young: incomeYoung,
            income_middle: incomeMiddle,
            income_old: incomeOld
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateDashboard();
            showAlert('Policy updated successfully', 'success');
        } else {
            showAlert('Failed to update policy: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while updating policy', 'danger');
    });
});

// Add the updateDashboard function to update the form with current policy values
function updateDashboard() {
    fetch('/api/get_game_state')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const gameState = data.game_state;
                
                // Update tax rates
                $('#tax-young').val(gameState.tax_rates.young);
                $('#tax-middle').val(gameState.tax_rates.middle);
                $('#tax-old').val(gameState.tax_rates.old);
                
                // Update other policy parameters
                $('#pension-rate').val(gameState.pension_rate);
                $('#borrowing-limit').val(gameState.borrowing_limit);
                $('#target-stock').val(gameState.target_stock);
                $('#num-test-players').val(gameState.num_test_players);
                
                // Update income parameters
                $('#income-young').val(gameState.income_young);
                $('#income-middle').val(gameState.income_middle);
                $('#income-old').val(gameState.income_old);
                
                // Update interest rate display
                updateInterestRateDisplay(gameState.equilibrium_interest_rate);
                
                // Update other UI elements as needed
                $('#current-round').text(gameState.current_round);
                $('#num-players').text(gameState.num_players);
                $('#num-waiting').text(gameState.num_waiting);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Failed to fetch game state', 'danger');
        });
}

// Update interest rate display with color coding
function updateInterestRateDisplay(rate) {
    const rateElement = $('#equilibrium-interest-rate');
    rateElement.text(rate.toFixed(2));
    
    // Color coding based on rate value
    if (rate < 0) {
        rateElement.removeClass('text-success text-warning').addClass('text-danger');
    } else if (rate < 1) {
        rateElement.removeClass('text-success text-danger').addClass('text-warning');
    } else {
        rateElement.removeClass('text-warning text-danger').addClass('text-success');
    }
}

// Show alert message
function showAlert(message, type) {
    const alertDiv = $('<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">')
        .text(message)
        .append('<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="close"></button>');
    
    $('#alerts-container').append(alertDiv);
    
    // Auto-dismiss after 5 seconds - commenting out to eliminate delays
    /*
    setTimeout(() => {
        alertDiv.alert('close');
    }, 5000);
    */
}

// Initialize tooltips
$(function() {
    updateDashboard();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 