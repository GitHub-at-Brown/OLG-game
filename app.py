import os
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
from dotenv import load_dotenv
from models.game_state import GameState
from models.user import User
from config.config import get_config
from services import test_player_service
import uuid
import random

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

# List of fun names for test players - MOVED to test_player_service.py
# TEST_PLAYER_NAMES = [...]

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
    # Set professor status in session
    session['is_professor'] = True
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
            # Get updated aggregated data needed by the professor dashboard
            young_users = [u for u in game_state.users.values() if u.age_stage == 'Y']
            middle_users = [u for u in game_state.users.values() if u.age_stage == 'M']
            
            total_young_borrowing = sum(u.current_borrowing for u in young_users)
            total_middle_saving = sum(u.current_saving for u in middle_users if u.current_saving > 0)
            
            # Create aggregate demand data
            aggregate_demand = None
            if decision_type == 'borrow' and demand_curve:
                # Generate aggregate demand data if we have a young borrower with a demand curve
                standard_rates = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                aggregate_demand = []
                
                # Calculate aggregate borrowing for each standard interest rate
                young_players = [u for u in game_state.users.values() if u.age_stage == 'Y' and hasattr(u, 'demand_curve') and u.demand_curve]
                
                for rate in standard_rates:
                    total_borrowing = 0
                    for player in young_players:
                        # Find the borrowing amount at this interest rate in the player's demand curve
                        exact_match = next((point for point in player.demand_curve 
                                        if abs(point['interestRate'] - rate) < 0.001), None)
                        
                        if exact_match:
                            total_borrowing += exact_match['borrowingAmount']
                        else:
                            # Get points below and above the target rate
                            lower_points = [p for p in player.demand_curve if p['interestRate'] < rate]
                            upper_points = [p for p in player.demand_curve if p['interestRate'] > rate]
                            
                            # Interpolate
                            if lower_points and upper_points:
                                lower_point = max(lower_points, key=lambda p: p['interestRate'])
                                upper_point = min(upper_points, key=lambda p: p['interestRate'])
                                
                                rate_range = upper_point['interestRate'] - lower_point['interestRate']
                                if rate_range > 0:
                                    position = (rate - lower_point['interestRate']) / rate_range
                                    borrowing = lower_point['borrowingAmount'] + position * (
                                        upper_point['borrowingAmount'] - lower_point['borrowingAmount']
                                    )
                                    total_borrowing += borrowing
                                else:
                                    total_borrowing += lower_point['borrowingAmount']
                            elif lower_points:
                                total_borrowing += max(lower_points, key=lambda p: p['interestRate'])['borrowingAmount']
                            elif upper_points:
                                total_borrowing += min(upper_points, key=lambda p: p['interestRate'])['borrowingAmount']
                    
                    aggregate_demand.append({
                        'interestRate': rate,
                        'borrowingAmount': total_borrowing
                    })
            
            # Calculate loan market balance
            loan_balance = total_middle_saving - (total_young_borrowing + game_state.government_debt)
            
            # Create event data with all necessary info for the professor dashboard
            event_data = {
                'user_id': user_id, 
                'decision_type': decision_type,
                'aggregates': {
                    'total_young_borrowing': total_young_borrowing,
                    'total_middle_saving': total_middle_saving,
                    'loan_balance': loan_balance
                },
                'waiting_for': list(game_state.pending_decisions)
            }
            
            # Add aggregate demand data if available
            if aggregate_demand:
                event_data['aggregate_demand'] = aggregate_demand
            
            # Notify other clients of the update with the enhanced data
            socketio.emit('decision_submitted', event_data)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid decision'}), 400
    except ValueError:
        return jsonify({'success': False, 'error': 'Amount must be a number'}), 400

@app.route('/api/current_state')
def get_current_state():
    """API endpoint to get the current game state"""
    user_id = request.args.get('user_id')
    
    # User registration is handled by the /player endpoint when the dashboard is loaded
    # Removed auto-registration from here to avoid duplication
    # if user_id:
    #     if user_id not in game_state.users:
    #         game_state.add_user(user_id)
    #         player_info = { ... }
    #         socketio.emit('player_joined', {"player": player_info})
    #     state = game_state.get_user_state(user_id)
    # else:
    #     state = game_state.get_full_state()

    if user_id:
        if user_id in game_state.users:
            state = game_state.get_user_state(user_id)
        else:
            # If user somehow isn't registered but requests state, return empty state or error
            # Or potentially redirect to login/player view?
            # For now, return an error state or indicate user not found
            return jsonify({'error': 'User not found or not registered.'}), 404 
    else:
        # If no user_id, return the full state (likely for professor view)
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
    """API endpoint to add test players using the test player service"""
    try:
        data = request.json
        count = data.get('count', 3)
        optimal_decisions = data.get('optimal_decisions', False)
        
        if not isinstance(count, int) or not (1 <= count <= 50):
            return jsonify({'success': False, 'error': 'Count must be an integer between 1 and 50'}), 400
        
        # Set the optimal decisions flag (this might be better moved to game_state or config)
        game_state.set_optimal_decisions(optimal_decisions)
        
        # Call the service function to add players
        players_added = test_player_service.add_test_players(game_state, count, optimal_decisions)
                
        # Notify all clients of the update
        socketio.emit('players_added', {'count': count, 'players': players_added})
        
        return jsonify({
            'success': True, 
            'count': len(players_added),
            'players': players_added
        })
    except Exception as e:
        app.logger.error(f"Error adding test players: {str(e)}")
        # Consider more specific error handling/logging
        return jsonify({'success': False, 'error': f'Failed to add test players: {str(e)}'}), 500

@app.route('/api/set_policy', methods=['POST'])
def set_policy():
    if not session.get('is_professor'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.json
        app.logger.info(f"Received policy update data: {data}")
        
        # Extract tax rates with proper handling of both formats
        if 'tax_rates' in data:
            tax_rates = data.get('tax_rates', {})
        else:
            # Handle the case where tax rates are sent directly at the root level
            tax_rates = {
                'young': data.get('tax_young', 0.0),
                'middle': data.get('tax_middle', 0.2),
                'old': data.get('tax_old', 0.0)
            }
        
        # Fix variable names to match the GameState attributes
        tax_rate_young = tax_rates.get('young', 0.0)
        tax_rate_middle = tax_rates.get('middle', 0.2)
        tax_rate_old = tax_rates.get('old', 0.0)
            
        # Get other parameters with proper defaults
        pension_rate = data.get('pension_rate', 0.5)
        borrowing_limit = data.get('borrowing_limit', 100.0)
        target_stock = data.get('target_stock', 80.0)
        num_test_players = data.get('num_test_players', 0)
        
        # Handle interest rate if provided
        interest_rate = data.get('interest_rate')
        if interest_rate is not None:
            app.logger.info(f"Setting fixed interest rate: {interest_rate}")
            game_state.interest_rate = float(interest_rate)
        
        # Get income parameters with defaults
        income_young = data.get('income_young', 0.0)
        income_middle = data.get('income_middle', 60.0)
        income_old = data.get('income_old', 0.0)
        
        # Log the values being sent to set_policy
        app.logger.info(f"Setting policy with: tax_rate_young={tax_rate_young}, "
                        f"tax_rate_middle={tax_rate_middle}, "
                        f"tax_rate_old={tax_rate_old}, "
                        f"borrowing_limit={borrowing_limit}")
        
        # Update the game state with the new policy parameters
        game_state.set_policy(
            tax_rate_young=tax_rate_young,
            tax_rate_middle=tax_rate_middle,
            tax_rate_old=tax_rate_old,
            pension_rate=pension_rate,
            borrowing_limit=borrowing_limit,
            target_stock=target_stock,
            num_test_players=num_test_players,
            income_young=income_young,
            income_middle=income_middle,
            income_old=income_old
        )
        
        # Create a policy update payload with just the essential information
        # This is more efficient than sending the full state
        policy_update = {
            'policy': {
                'interest_rate': game_state.interest_rate,
                'borrowing_limit': game_state.borrowing_limit,
                'taxes': {
                    'young': game_state.tax_rate_young,
                    'middle': game_state.tax_rate_middle,
                    'old': game_state.tax_rate_old
                },
                'government_debt': game_state.government_debt,
                'incomes': {
                    'young': game_state.income_young,
                    'middle': game_state.income_middle,
                    'old': game_state.income_old
                }
            }
        }
        
        # Calculate aggregate statistics for the professor dashboard
        young_users = [u for u in game_state.users.values() if u.age_stage == 'Y']
        middle_users = [u for u in game_state.users.values() if u.age_stage == 'M']
        
        total_young_borrowing = sum(u.current_borrowing for u in young_users)
        total_middle_saving = sum(u.current_saving for u in middle_users if u.current_saving > 0)
        
        # Add aggregates to the policy update
        policy_update['aggregates'] = {
            'total_young_borrowing': total_young_borrowing,
            'total_middle_saving': total_middle_saving,
            'loan_balance': total_middle_saving - (total_young_borrowing + game_state.government_debt)
        }
        
        app.logger.info(f"Sending policy update to clients. Borrowing limit: {policy_update['policy']['borrowing_limit']}")
        
        # Notify all clients of the policy update with our focused payload
        socketio.emit('policy_updated', policy_update)
        
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error setting policy: {str(e)}")
        app.logger.exception("Full traceback:")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/advance_round', methods=['POST'])
def advance_round():
    """API endpoint for professor to advance to the next round"""
    try:
        data = request.json or {}
        force = data.get('force', False)
        
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
                    
                    # Create a demand curve based on optimal decisions setting
                    minimal_demand_curve = []
                    interest_rates = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    
                    if game_state.make_optimal_decisions:
                        # Optimal decisions - maximum borrowing at each rate
                        for rate in interest_rates:
                            max_borrowing = game_state.borrowing_limit / (1 + rate/100)
                            minimal_demand_curve.append({
                                'interestRate': rate,
                                'borrowingAmount': round(max_borrowing, 1)
                            })
                    else:
                        # Start with maximum amount at 0% (borrowing limit)
                        borrowing_at_zero = game_state.borrowing_limit
                        minimal_demand_curve.append({
                            'interestRate': 0,
                            'borrowingAmount': borrowing_at_zero
                        })
                        
                        # Previous borrowing amount
                        prev_borrowing = borrowing_at_zero
                        
                        # Generate remaining points
                        for rate in interest_rates[1:]:
                            max_borrowing = game_state.borrowing_limit / (1 + rate/100)
                            max_possible = min(prev_borrowing, max_borrowing)
                            # Use a conservative approach for emergency fallback
                            borrowing = round(random.uniform(max(1, max_possible * 0.5), max_possible), 1)
                            
                            minimal_demand_curve.append({
                                'interestRate': rate,
                                'borrowingAmount': borrowing
                            })
                            
                            prev_borrowing = borrowing
                    
                    user.demand_curve = minimal_demand_curve
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
        
        if remaining_human_players and not force:
            print(f"Cannot advance round: waiting for human players: {remaining_human_players}")
            return jsonify({
                'success': False, 
                'error': f'Waiting for decisions from human players: {", ".join(remaining_human_players)}'
            }), 400
        
        # If there are human players pending but force is True, remove them from pending
        if remaining_human_players and force:
            print(f"Force advancing round with {len(remaining_human_players)} human players pending")
            for uid in list(game_state.pending_decisions):
                if not game_state.is_test_player(uid) and uid in game_state.users:
                    user = game_state.users[uid]
                    # Force default decisions based on age stage
                    if user.age_stage == 'Y':
                        game_state.record_decision(uid, 'borrow', 0)  # Zero borrowing is safe
                    elif user.age_stage == 'M':
                        game_state.record_decision(uid, 'save', 0)    # Zero saving is safe
                    elif user.age_stage == 'O':
                        game_state.record_decision(uid, 'consume', 0) # Zero consumption is fine for old
        
        # Force the round to run, even if there are some pending decisions
        # This should only happen if there's a serious bug
        print(f"Running round {game_state.current_round}...")
        success = game_state.run_round()
        
        if success:
            # Round advancement was successful, create enhanced event data
            # Include basic round info
            event_data = {
                'round': game_state.current_round,
                'policy': {
                    'interest_rate': game_state.interest_rate,
                    'borrowing_limit': game_state.borrowing_limit,
                    'taxes': {
                        'young': game_state.tax_rate_young,
                        'middle': game_state.tax_rate_middle,
                        'old': game_state.tax_rate_old
                    }
                }
            }
            
            # Notify all clients with enhanced data
            socketio.emit('round_advanced', event_data)
            
            return jsonify({'success': True, 'round': game_state.current_round})
        else:
            # Emergency override for cases where run_round fails
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
            
            # Create enhanced emergency event data
            emergency_event_data = {
                'round': game_state.current_round,
                'emergency_override': True,
                'policy': {
                    'interest_rate': game_state.interest_rate,
                    'borrowing_limit': game_state.borrowing_limit,
                    'taxes': {
                        'young': game_state.tax_rate_young,
                        'middle': game_state.tax_rate_middle,
                        'old': game_state.tax_rate_old
                    }
                }
            }
            
            # Notify clients with enhanced emergency data
            socketio.emit('round_advanced', emergency_event_data)
            
            return jsonify({'success': True, 'round': game_state.current_round, 'emergency_override': True})
            
    except Exception as e:
        print(f"Error advancing round: {str(e)}")
        app.logger.exception("Exception during round advancement:")
        return jsonify({'success': False, 'error': str(e)}), 500

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
