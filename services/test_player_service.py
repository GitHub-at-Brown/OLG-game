import random
import uuid
from models.user import User

# List of fun names for test players - moved from app.py
TEST_PLAYER_NAMES = [
    "Keynes", "Smith", "Ricardo", "Friedman", "Hayek", "Marshall", 
    "Samuelson", "Krugman", "Arrow", "Solow", "Fisher", "Walras",
    "Nash", "Hicks", "Tobin", "Modigliani", "Lucas", "Akerlof",
    "Spence", "Stiglitz", "Vickrey", "Coase", "Thaler", "Kahneman",
    "Ostrom", "Sen", "Becker", "Myrdal", "Tirole", "Shiller",
    "Pigou", "Muth", "Pareto", "Hume", "Malthus", "Schumpeter",
    "Minsky", "Duflo", "Banerjee", "Robinson", "Acemoglu",
    "Diamond", "Ramsey", "Allais", "Simon", "Hotelling", "Fogel",
    "North", "Hurwicz", "Maskin", "Myerson", "Mundell", "Phelps"
]

def generate_demand_curve(borrowing_limit, interest_rates, make_optimal_decisions=False):
    """
    Centralized function to generate demand curves for Young players.
    
    Args:
        borrowing_limit: Maximum borrowing limit
        interest_rates: List of interest rates to generate demand points for
        make_optimal_decisions: If True, generates optimal demand curve
        
    Returns:
        List of demand curve points {interestRate, borrowingAmount}
    """
    demand_curve = []
    
    if make_optimal_decisions:
        # Optimal decision: borrow max at all rates
        for rate in interest_rates:
            max_borrowing = borrowing_limit / (1 + rate / 100)
            demand_curve.append({
                'interestRate': rate, 
                'borrowingAmount': round(max_borrowing, 1)
            })
    else:
        # Random demand curve generation
        max_borrowing_at_zero = borrowing_limit
        borrowing_at_zero = max_borrowing_at_zero
        demand_curve.append({
            'interestRate': 0, 
            'borrowingAmount': borrowing_at_zero
        })
        
        prev_borrowing = borrowing_at_zero
        
        for rate in interest_rates[1:]:
            max_borrowing = borrowing_limit / (1 + rate / 100)
            max_possible = min(prev_borrowing, max_borrowing)
            borrowing = round(random.uniform(0, max_possible), 1)
            demand_curve.append({
                'interestRate': rate,
                'borrowingAmount': borrowing
            })
            prev_borrowing = borrowing
    
    return demand_curve

def add_test_players(game_state, count, optimal_decisions):
    """
    Adds a specified number of test players to the game state with a 
    desired distribution of ages and generates their initial decisions.
    """
    players_added = []
    
    # Calculate how many of each age to add
    young_count = count // 3
    middle_count = count // 3
    old_count = count - young_count - middle_count  # Ensure we add exactly the requested number
    
    # Shuffle the names list to get random names
    available_names = TEST_PLAYER_NAMES.copy()
    random.shuffle(available_names)
    
    current_name_index = 0

    # Add Young players
    for _ in range(young_count):
        user_id = f"test_Y_{str(uuid.uuid4())[:8]}"
        name = f"Test {available_names[current_name_index % len(available_names)]}"
        current_name_index += 1
        game_state.add_user(user_id, name=name, avatar="test_young")
        players_added.append({"id": user_id, "name": name, "stage": "Y", "user_obj": game_state.users[user_id]})
    
    # Add Middle-aged players
    for _ in range(middle_count):
        user_id = f"test_M_{str(uuid.uuid4())[:8]}"
        name = f"Test {available_names[current_name_index % len(available_names)]}"
        current_name_index += 1
        game_state.add_user(user_id, name=name, avatar="test_middle")
        user = game_state.users[user_id]
        user.age_stage = 'M'
        user.assets = -20.0 # Typical borrowing amount from youth
        players_added.append({"id": user_id, "name": name, "stage": "M", "user_obj": user})
    
    # Add Old players
    for _ in range(old_count):
        user_id = f"test_O_{str(uuid.uuid4())[:8]}"
        name = f"Test {available_names[current_name_index % len(available_names)]}"
        current_name_index += 1
        game_state.add_user(user_id, name=name, avatar="test_old")
        user = game_state.users[user_id]
        user.age_stage = 'O'
        user.assets = 30.0 # Typical saving amount from middle age
        players_added.append({"id": user_id, "name": name, "stage": "O", "user_obj": user})
    
    # Immediately generate decisions for all newly added test players
    for player_data in players_added:
        generate_decision_for_player(game_state, player_data["user_obj"], optimal_decisions)

    # Return list without the user object
    return [{"id": p["id"], "name": p["name"], "stage": p["stage"]} for p in players_added]


def generate_decision_for_player(game_state, user, optimal_decisions=None):
    """
    Generates a decision (borrowing, saving, or consumption) for a single test player.
    
    Args:
        game_state: The GameState instance
        user: The User object to generate a decision for
        optimal_decisions: Whether to make optimal decisions. If None, uses game_state.make_optimal_decisions
    """
    # Use the provided optimal_decisions parameter if given, otherwise use game_state setting
    use_optimal = optimal_decisions if optimal_decisions is not None else game_state.make_optimal_decisions
    
    if user.age_stage == 'Y':
        # Generate demand curve using the centralized function
        interest_rates = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        demand_curve = generate_demand_curve(
            game_state.borrowing_limit, 
            interest_rates, 
            use_optimal
        )
        
        # Determine borrow amount based on current interest rate
        current_rate_percent = game_state.interest_rate * 100
        
        # Use the centralized interpolation function
        borrow_amount = interpolate_from_demand_curve(demand_curve, current_rate_percent, game_state.borrowing_limit)

        # Store demand curve and record decision
        user.demand_curve = demand_curve
        success = game_state.record_decision(user.user_id, 'borrow', borrow_amount)
        
        # Handle failure case similar to GameState implementation
        if not success:
            print(f"Failed to record Young borrowing decision for {user.user_id}: {borrow_amount}")
            # Fallback to a safer borrowing amount
            game_state.record_decision(user.user_id, 'borrow', min(10, game_state.borrowing_limit * 0.1))

    elif user.age_stage == 'M':
        # Middle-aged decision: Save or Borrow
        income = game_state.income_middle - game_state.tax_rate_middle
        debt_amount = abs(user.assets) if user.assets < 0 else 0
        debt_repayment = (1 + game_state.interest_rate) * debt_amount
        disposable_income = income - debt_repayment
        
        # Middle-aged test users with negative/zero disposable income just save 0 (consume their income)
        if disposable_income <= 0:
            print(f"Test user {user.name} has negative disposable income ({disposable_income}), saving 0")
            success = game_state.record_decision(user.user_id, 'save', 0)
            if not success:
                print(f"Failed to record zero saving for broke Middle-aged {user.user_id}")
                # Try again with the safest option
                game_state.record_decision(user.user_id, 'save', 0)
        else:
            # Normal case: disposable income is positive
            # Either save or borrow
            if random.random() < 0.8:  # 80% chance to save if they have income
                # Save a positive amount up to 60% of disposable income
                save_percentage = random.uniform(0.2, 0.6)
                save_amount = disposable_income * save_percentage
                # Ensure positive and within limits
                save_amount = max(0, min(save_amount, disposable_income * 0.9))
                
                success = game_state.record_decision(user.user_id, 'save', round(save_amount, 1))
                if not success:
                    print(f"Failed to record Middle-aged saving decision for {user.user_id}: {save_amount}")
                    # Try again with a safer amount
                    safe_amount = min(5, disposable_income * 0.1)
                    game_state.record_decision(user.user_id, 'save', safe_amount)
            else:  # 20% chance to borrow
                # Borrow a small amount (up to 30% of disposable income)
                borrow_percentage = random.uniform(0.1, 0.3)
                borrow_amount = disposable_income * borrow_percentage
                # Ensure positive and reasonable
                borrow_amount = max(0, min(borrow_amount, game_state.borrowing_limit * 0.3))
                
                success = game_state.record_decision(user.user_id, 'borrow', round(borrow_amount, 1))
                if not success:
                    print(f"Failed to record Middle-aged borrowing decision for {user.user_id}: {borrow_amount}")
                    # Try a safer amount
                    game_state.record_decision(user.user_id, 'save', 1)
            
    elif user.age_stage == 'O':
        # Old players automatically consume
        success = game_state.record_decision(user.user_id, 'consume', 0)
        if not success:
            print(f"Failed to record Old consumption decision for {user.user_id}")
            # Try again
            game_state.record_decision(user.user_id, 'consume', 0)

def generate_test_player_decisions(game_state, optimal_decisions=None):
    """
    Generates decisions for all existing test players who haven't submitted one.
    
    Args:
        game_state: The GameState instance
        optimal_decisions: Whether to make optimal decisions. If None, uses game_state.make_optimal_decisions
    """
    for user_id in list(game_state.pending_decisions):
        # Support both startswith('test_') and game_state.is_test_user() methods
        is_test_user = (user_id.startswith("test_") or 
                       (hasattr(game_state, 'is_test_user') and game_state.is_test_user(user_id)))
        
        if is_test_user and user_id in game_state.users:
            user = game_state.users[user_id]
            try:
                generate_decision_for_player(game_state, user, optimal_decisions)
            except Exception as e:
                print(f"Error generating decision for test player {user_id}: {str(e)}")
                # Ensure we don't get stuck with failing test users - add fallback logic
                if user.age_stage == 'Y':
                    game_state.record_decision(user_id, 'borrow', min(10, game_state.borrowing_limit * 0.1))
                elif user.age_stage == 'M':
                    # Safest option for middle-aged: always try to save 0
                    game_state.record_decision(user_id, 'save', 0)
                elif user.age_stage == 'O':
                    game_state.record_decision(user_id, 'consume', 0)


def interpolate_from_demand_curve(demand_curve, interest_rate, borrowing_limit=None, default_amount=None):
    """
    Centralized utility function to interpolate borrowing amount from a demand curve.
    
    Args:
        demand_curve: List of {interestRate, borrowingAmount} points
        interest_rate: The interest rate to interpolate at
        borrowing_limit: Optional maximum borrowing limit for safety checks
        default_amount: Optional default amount to return if interpolation fails
                        If not provided, defaults to 10% of borrowing_limit or 10
                        
    Returns:
        float: The interpolated borrowing amount at the given interest rate
    """
    # Input validation
    if not demand_curve or not isinstance(demand_curve, list):
        if default_amount is not None:
            return default_amount
        return 10 if borrowing_limit is None else min(10, borrowing_limit * 0.1)
    
    # Check for exact match first
    exact_match = next((point for point in demand_curve 
                        if abs(point['interestRate'] - interest_rate) < 0.001), None)
    if exact_match:
        return exact_match['borrowingAmount']
    
    # Find lower and upper points for interpolation
    lower_points = [p for p in demand_curve if p['interestRate'] < interest_rate]
    upper_points = [p for p in demand_curve if p['interestRate'] > interest_rate]
    
    # Calculate interpolated value
    if lower_points and upper_points:
        # Get closest points for interpolation
        lower_point = max(lower_points, key=lambda p: p['interestRate'])
        upper_point = min(upper_points, key=lambda p: p['interestRate'])
        
        # Perform linear interpolation
        rate_range = upper_point['interestRate'] - lower_point['interestRate']
        if abs(rate_range) < 1e-6:  # Avoid division by very small numbers
            return lower_point['borrowingAmount']
            
        proportion = (interest_rate - lower_point['interestRate']) / rate_range
        interpolated_amount = lower_point['borrowingAmount'] + proportion * (
            upper_point['borrowingAmount'] - lower_point['borrowingAmount']
        )
        return round(interpolated_amount, 1)
        
    # If no interpolation possible, use the closest point
    elif lower_points:
        return round(max(lower_points, key=lambda p: p['interestRate'])['borrowingAmount'], 1)
    elif upper_points:
        return round(min(upper_points, key=lambda p: p['interestRate'])['borrowingAmount'], 1)
    
    # Fallback to default
    if default_amount is not None:
        return default_amount
    return 10 if borrowing_limit is None else min(10, borrowing_limit * 0.1)

# Replace the old _interpolate_borrowing function with the new centralized version
_interpolate_borrowing = interpolate_from_demand_curve
