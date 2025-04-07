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


def generate_decision_for_player(game_state, user, optimal_decisions):
    """Generates a decision (borrowing, saving, or consumption) for a single test player."""
    
    if user.age_stage == 'Y':
        # Generate demand curve using the centralized function
        interest_rates = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        demand_curve = generate_demand_curve(
            game_state.borrowing_limit, 
            interest_rates, 
            optimal_decisions
        )
        
        # Determine borrow amount based on current interest rate
        current_rate_percent = game_state.interest_rate * 100
        exact_match = next((p for p in demand_curve if abs(p['interestRate'] - current_rate_percent) < 0.1), None)
        
        if exact_match:
            borrow_amount = exact_match['borrowingAmount']
        else:
            borrow_amount = _interpolate_borrowing(demand_curve, current_rate_percent, game_state.borrowing_limit)

        # Store demand curve and record decision
        user.demand_curve = demand_curve
        game_state.record_decision(user.user_id, 'borrow', borrow_amount)

    elif user.age_stage == 'M':
        # Middle-aged decision: Save or Borrow
        income = game_state.income_middle - game_state.tax_rate_middle
        debt_repayment = (1 + game_state.interest_rate) * abs(user.assets) if user.assets < 0 else 0
        disposable_income = income - debt_repayment
        
        if random.random() < 0.8:  # 80% chance to save
            save_percentage = random.uniform(0.2, 0.6)
            save_amount = max(0, disposable_income * save_percentage) # Ensure non-negative saving
            game_state.record_decision(user.user_id, 'save', round(save_amount, 1))
        else:  # 20% chance to borrow more
            borrow_percentage = random.uniform(0.1, 0.3)
            borrow_amount = max(0, disposable_income * borrow_percentage) # Ensure non-negative borrowing
            game_state.record_decision(user.user_id, 'borrow', round(borrow_amount, 1))
            
    elif user.age_stage == 'O':
        # Old players automatically consume
        game_state.record_decision(user.user_id, 'consume', 0)

def generate_test_player_decisions(game_state, optimal_decisions):
    """Generates decisions for all existing test players who haven't submitted one."""
    for user_id in list(game_state.pending_decisions):
        if user_id.startswith("test_") and user_id in game_state.users:
            user = game_state.users[user_id]
            try:
                generate_decision_for_player(game_state, user, optimal_decisions)
            except Exception as e:
                print(f"Error generating decision for test player {user_id}: {str(e)}")


def _interpolate_borrowing(demand_curve, current_rate_percent, borrowing_limit):
    """Helper function to interpolate borrowing amount from a demand curve."""
    lower_points = [p for p in demand_curve if p['interestRate'] < current_rate_percent]
    upper_points = [p for p in demand_curve if p['interestRate'] > current_rate_percent]
    
    if lower_points and upper_points:
        lower_point = max(lower_points, key=lambda p: p['interestRate'])
        upper_point = min(upper_points, key=lambda p: p['interestRate'])
        
        rate_range = upper_point['interestRate'] - lower_point['interestRate']
        if rate_range > 0:
            position = (current_rate_percent - lower_point['interestRate']) / rate_range
            borrow_amount = lower_point['borrowingAmount'] + position * (
                upper_point['borrowingAmount'] - lower_point['borrowingAmount']
            )
            return round(borrow_amount, 1)
        else:
            return round(lower_point['borrowingAmount'], 1) # Avoid division by zero if rates are the same
            
    elif lower_points:
        return round(max(lower_points, key=lambda p: p['interestRate'])['borrowingAmount'], 1)
    elif upper_points:
        return round(min(upper_points, key=lambda p: p['interestRate'])['borrowingAmount'], 1)
    else:
        # Fallback: borrow a small fraction of the limit
        return round(min(10, borrowing_limit * 0.1), 1)
