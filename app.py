import os
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
from dotenv import load_dotenv
from models.game_state import GameState
from models.user import User
from config.config import get_config
import uuid  # Add this import for generating unique IDs
import random  # Add this import for generating random numbers

# Load environment variables from .env file if present
load_dotenv()

# Get configuration based on environment
config = get_config()

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG
app.config['TESTING'] = config.TESTING
app.config['ENV'] = config.ENV
socketio = SocketIO(app)

# Initialize game state
game_state = GameState()

# List of fun names for test players
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

@app.route('/')
def index():
    """Main entry point for the game"""
    return render_template('index.html')

@app.route('/player')
def player_view():
    """Player dashboard view"""
    user_id = request.args.get('user_id')
    if not user_id:
        return render_template('login.html')
    
    display_name = request.args.get('display_name')
    avatar = request.args.get('avatar', 'fox')
    
    # Auto-register new users when they access the dashboard
    new_player = False
    if user_id not in game_state.users:
        game_state.add_user(user_id, name=display_name, avatar=avatar)
        new_player = True
    elif display_name:  # Update existing user's name if provided
        game_state.users[user_id].name = display_name
        if avatar:
            game_state.users[user_id].avatar = avatar
    
    # If this is a new player, emit an event to notify all clients
    if new_player:
        player_info = {
            "id": user_id,
            "name": display_name,
            "avatar": avatar,
            "stage": game_state.users[user_id].age_stage
        }
        socketio.emit('player_joined', {"player": player_info})
    
    return render_template('player_dashboard.html', user_id=user_id)

@app.route('/professor')
def professor_view():
    """Professor/admin dashboard view"""
    return render_template('professor_dashboard.html')

@app.route('/api/submit_decision', methods=['POST'])
def submit_decision():
    """API endpoint for players to submit their decisions"""
    data = request.json
    user_id = data.get('user_id')
    decision_type = data.get('decision_type')  # 'borrow' or 'save'
    amount = data.get('amount')
    demand_curve = data.get('demand_curve')  # New: array of {interestRate, borrowingAmount} points
    
    # Validate inputs
    if not all([user_id, decision_type, amount is not None]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    try:
        amount = float(amount)
        
        # Store demand curve if provided (for Young agents submitting borrowing decisions)
        if decision_type == 'borrow' and demand_curve and isinstance(demand_curve, list):
            # Get user object
            user = game_state.users.get(user_id)
            if user:
                # Store the demand curve points in the user object
                user.demand_curve = demand_curve
                print(f"Stored demand curve with {len(demand_curve)} points for user {user_id}")
        
        # Save decision in game state
        success = game_state.record_decision(user_id, decision_type, amount)
        if success:
            # Notify other clients of the update
            socketio.emit('decision_submitted', 
                         {'user_id': user_id, 'decision_type': decision_type})
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid decision'}), 400
    except ValueError:
        return jsonify({'success': False, 'error': 'Amount must be a number'}), 400

@app.route('/api/current_state')
def get_current_state():
    """API endpoint to get the current game state"""
    user_id = request.args.get('user_id')
    
    # Auto-register new users when they request their state
    if user_id:
        # Auto-register new users when they request their state
        if user_id not in game_state.users:
            game_state.add_user(user_id)
            # Emit event for new user registration
            player_info = {
                "id": user_id,
                "name": game_state.users[user_id].name,
                "avatar": game_state.users[user_id].avatar,
                "stage": game_state.users[user_id].age_stage
            }
            socketio.emit('player_joined', {"player": player_info})
        state = game_state.get_user_state(user_id)
    else:
        state = game_state.get_full_state()
    
    return jsonify(state)

@app.route('/api/check_unique_user', methods=['POST'])
def check_unique_user():
    """API endpoint to check if a user ID or name is already taken"""
    data = request.json
    user_id = data.get('user_id')
    display_name = data.get('display_name')
    
    id_exists = user_id in game_state.users
    name_exists = any(user.name == display_name for user in game_state.users.values() if display_name)
    
    return jsonify({
        'unique': not (id_exists or name_exists),
        'id_exists': id_exists,
        'name_exists': name_exists
    })

@app.route('/api/add_test_players', methods=['POST'])
def add_test_players():
    """API endpoint to add test players with desired distribution of ages"""
    try:
        data = request.json
        count = data.get('count', 3)
        
        if count <= 0 or count > 50:
            return jsonify({'success': False, 'error': 'Count must be between 1 and 50'}), 400
        
        players_added = []
        
        # Calculate how many of each age to add
        young_count = count // 3
        middle_count = count // 3
        old_count = count - young_count - middle_count  # Ensure we add exactly the requested number
        
        # Shuffle the names list to get random names
        available_names = TEST_PLAYER_NAMES.copy()
        random.shuffle(available_names)
        
        # Add Young players
        for i in range(young_count):
            user_id = f"test_Y_{str(uuid.uuid4())[:8]}"
            # Use a fun name if available, otherwise use a numbered name
            name_index = i % len(available_names)
            name = f"Test {available_names[name_index]}"
            game_state.add_user(user_id, name=name, avatar="test_young")
            players_added.append({"id": user_id, "name": name, "stage": "Y"})
        
        # Add Middle-aged players
        for i in range(middle_count):
            user_id = f"test_M_{str(uuid.uuid4())[:8]}"
            name_index = (young_count + i) % len(available_names)
            name = f"Test {available_names[name_index]}"
            game_state.add_user(user_id, name=name, avatar="test_middle")
            # Set stage to Middle-aged
            user = game_state.users[user_id]
            user.age_stage = 'M'
            # Give some default assets (debt from youth)
            user.assets = -20.0  # Typical borrowing amount from youth
            players_added.append({"id": user_id, "name": name, "stage": "M"})
        
        # Add Old players
        for i in range(old_count):
            user_id = f"test_O_{str(uuid.uuid4())[:8]}"
            name_index = (young_count + middle_count + i) % len(available_names)
            name = f"Test {available_names[name_index]}"
            game_state.add_user(user_id, name=name, avatar="test_old")
            # Set stage to Old
            user = game_state.users[user_id]
            user.age_stage = 'O'
            # Give some default assets (savings from middle age)
            user.assets = 30.0  # Typical saving amount from middle age
            players_added.append({"id": user_id, "name": name, "stage": "O"})
        
        # Immediately generate decisions for all test players
        # This ensures they don't show up in the waiting list
        for player in players_added:
            user_id = player["id"]
            user = game_state.users[user_id]
            
            if user.age_stage == 'Y':
                # Young players typically borrow between 40% and 90% of the limit
                borrow_percentage = random.uniform(0.4, 0.9)
                borrow_amount = game_state.borrowing_limit * borrow_percentage
                game_state.record_decision(user_id, 'borrow', borrow_amount)
                
            elif user.age_stage == 'M':
                # Middle-aged players typically save between 20% and 60% of income
                # after repaying debt from youth
                income = game_state.income_middle - game_state.tax_middle
                debt_repayment = (1 + game_state.interest_rate) * abs(user.assets) if user.assets < 0 else 0
                disposable_income = income - debt_repayment
                
                # Some randomness - most save, some borrow more
                if random.random() < 0.8:  # 80% chance to save
                    save_percentage = random.uniform(0.2, 0.6)
                    save_amount = disposable_income * save_percentage
                    game_state.record_decision(user_id, 'save', save_amount)
                else:  # 20% chance to borrow more
                    borrow_percentage = random.uniform(0.1, 0.3)
                    borrow_amount = disposable_income * borrow_percentage
                    game_state.record_decision(user_id, 'borrow', borrow_amount)
            
            elif user.age_stage == 'O':
                # Old players automatically consume everything
                game_state.record_decision(user_id, 'consume', 0)
            
        # Notify all clients of the update
        socketio.emit('players_added', {'count': count, 'players': players_added})
        
        return jsonify({
            'success': True, 
            'count': count,
            'players': players_added
        })
    except Exception as e:
        print(f"Error adding test players: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to add test players: {str(e)}'}), 500

@app.route('/api/set_policy', methods=['POST'])
def set_policy():
    if not session.get('is_professor'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.json
        tax_rates = data.get('tax_rates', {})
        pension_rate = data.get('pension_rate', 0.5)
        borrowing_limit = data.get('borrowing_limit', 100.0)
        target_stock = data.get('target_stock', 80.0)
        num_test_players = data.get('num_test_players', 0)
        
        # Get income parameters with defaults
        income_young = data.get('income_young', 0.0)
        income_middle = data.get('income_middle', 60.0)
        income_old = data.get('income_old', 0.0)
        
        game_state.set_policy(
            tax_rate_young=tax_rates.get('young', 0.0),
            tax_rate_middle=tax_rates.get('middle', 0.2),
            tax_rate_old=tax_rates.get('old', 0.0),
            pension_rate=pension_rate,
            borrowing_limit=borrowing_limit,
            target_stock=target_stock,
            num_test_players=num_test_players,
            income_young=income_young,
            income_middle=income_middle,
            income_old=income_old
        )
        
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error setting policy: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/advance_round', methods=['POST'])
def advance_round():
    """API endpoint for professor to advance to the next round"""
    try:
        # Force auto-generation of test player decisions first
        test_player_ids = [user_id for user_id in game_state.pending_decisions 
                          if game_state.is_test_player(user_id) and user_id in game_state.users]
        
        print(f"Handling {len(test_player_ids)} pending test players before advancing round...")
        
        # First try using the game_state's built-in method
        game_state.generate_test_player_decisions()
        
        # If that didn't clear all test players, use direct override approach
        remaining_test_players = [user_id for user_id in game_state.pending_decisions 
                                if game_state.is_test_player(user_id) and user_id in game_state.users]
        
        if remaining_test_players:
            print(f"Still have {len(remaining_test_players)} test players that need force-decisions")
            for user_id in remaining_test_players:
                user = game_state.users[user_id]
                print(f"Forcing safe decision for {user.name} ({user.age_stage})...")
                
                # Force the safest possible decision based on age stage
                if user.age_stage == 'Y':
                    game_state.record_decision(user_id, 'borrow', 1)  # Minimal borrowing
                elif user.age_stage == 'M':
                    # For middle-aged, try the safest approach (save 0)
                    success = game_state.record_decision(user_id, 'save', 0)
                    if not success:
                        # If that fails, we have a bigger problem - fix it at any cost
                        # Override the internal user state directly as last resort
                        print(f"Emergency fix for Middle-aged {user.name}")
                        if user_id in game_state.pending_decisions:
                            game_state.pending_decisions.remove(user_id)
                        user.current_saving = 0
                        user.current_consumption = game_state.income_middle
                        user.current_utility = 0.1  # minimal utility
                elif user.age_stage == 'O':
                    game_state.record_decision(user_id, 'consume', 0)
        
        # Make sure no human players are left in pending decisions
        remaining_human_players = [game_state.users[uid].name for uid in game_state.pending_decisions 
                                 if not game_state.is_test_player(uid) and uid in game_state.users]
        
        if remaining_human_players:
            print(f"Cannot advance round: waiting for human players: {remaining_human_players}")
            return jsonify({
                'success': False, 
                'error': f'Waiting for decisions from human players: {", ".join(remaining_human_players)}'
            }), 400
        
        # Force the round to run, even if there are some pending decisions
        # This should only happen if there's a serious bug
        print(f"Running round {game_state.current_round}...")
        success = game_state.run_round()
        
        if not success:
            # Something is still wrong - extreme measures
            print("WARNING: Still can't advance round. Forcing advancement with emergency override...")
            
            # Force clear all pending decisions
            game_state.pending_decisions.clear()
            
            # Calculate equilibrium rate manually
            game_state.interest_rate = game_state.calculate_equilibrium()
            
            # Advance the round counter
            game_state.current_round += 1
            
            # Advance all users' age stages
            for user in game_state.users.values():
                user.advance_age()
            
            # Repopulate pending decisions for next round
            game_state.pending_decisions = set(game_state.users.keys())
            
            # Generate decisions for test players right away
            game_state.generate_test_player_decisions()
            
            # Notify clients
            socketio.emit('round_advanced', {'round': game_state.current_round})
            
            return jsonify({'success': True, 'round': game_state.current_round, 'warning': 'Emergency override used'})
        
        # Normal success case
        socketio.emit('round_advanced', {'round': game_state.current_round})
        return jsonify({'success': True, 'round': game_state.current_round})
        
    except Exception as e:
        print(f"Error advancing round: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Failed to advance round: {str(e)}'}), 500

@app.route('/api/reset_game', methods=['POST'])
def reset_game():
    """API endpoint to completely reset the game state"""
    try:
        global game_state
        # Create a brand new game state
        game_state = GameState()
        
        # Notify all clients of the reset
        socketio.emit('game_reset', {})
        
        return jsonify({
            'success': True,
            'message': 'Game has been reset to initial state'
        })
    except Exception as e:
        print(f"Error resetting game: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to reset game: {str(e)}'
        }), 500

@app.route('/api/get_game_state', methods=['GET'])
def get_game_state():
    try:
        # Create a simplified version of the game state with only what's needed for the dashboard
        state = {
            'current_round': game_state.current_round,
            'num_players': len(game_state.players),
            'num_waiting': len(game_state.pending_decisions),
            'equilibrium_interest_rate': game_state.equilibrium_interest_rate,
            'tax_rates': {
                'young': game_state.tax_rate_young,
                'middle': game_state.tax_rate_middle,
                'old': game_state.tax_rate_old
            },
            'pension_rate': game_state.pension_rate,
            'borrowing_limit': game_state.borrowing_limit,
            'target_stock': game_state.target_stock,
            'num_test_players': game_state.num_test_players,
            'income_young': game_state.income_young,
            'income_middle': game_state.income_middle,
            'income_old': game_state.income_old
        }
        return jsonify({'success': True, 'game_state': state})
    except Exception as e:
        app.logger.error(f"Error getting game state: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@socketio.on('connect')
def handle_connect():
    """Handle new socket connection"""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle socket disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    # For development - use production WSGI server in production
    port = config.PORT
    debug = config.DEBUG
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
