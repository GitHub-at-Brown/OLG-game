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
import threading

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

# List of fun names for test users - MOVED to test_player_service.py
# TEST_PLAYER_NAMES = test_player_service.TEST_PLAYER_NAMES

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
                app.logger.info(f"Stored demand curve with {len(demand_curve)} points for user {user_id}")
        
        # Save decision in game state
        success = game_state.record_decision(user_id, decision_type, amount)
        if success:
            # Get updated aggregated data using the compute_aggregates method
            aggregates = game_state.compute_aggregates()
            
            # Create aggregate demand data if we have a young borrower with a demand curve
            aggregate_demand = None
            if decision_type == 'borrow' and demand_curve:
                # Generate aggregate demand data for standard interest rates
                standard_rates = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                aggregate_demand = []
                
                # Calculate aggregate borrowing for each standard interest rate
                young_users = [u for u in game_state.users.values() 
                              if u.age_stage == 'Y' and hasattr(u, 'demand_curve') and u.demand_curve]
                
                for rate in standard_rates:
                    total_borrowing = 0
                    for user in young_users:
                        # Find the borrowing amount at this interest rate in the player's demand curve
                        exact_match = next((point for point in user.demand_curve 
                                        if abs(point['interestRate'] - rate) < 0.001), None)
                        
                        if exact_match:
                            total_borrowing += exact_match['borrowingAmount']
                        else:
                            # Interpolate between points
                            lower_points = [p for p in user.demand_curve if p['interestRate'] < rate]
                            upper_points = [p for p in user.demand_curve if p['interestRate'] > rate]
                            
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
            
            # Create event data with all necessary info for client updates
            event_data = {
                'user_id': user_id, 
                'decision_type': decision_type,
                'aggregates': aggregates,
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
    """API endpoint to add test users using the test player service"""
    try:
        data = request.json
        count = data.get('count', 3)
        optimal_decisions = data.get('optimal_decisions', False)
        
        if not isinstance(count, int) or not (1 <= count <= 50):
            return jsonify({'success': False, 'error': 'Count must be an integer between 1 and 50'}), 400
        
        # Set the optimal decisions flag (this might be better moved to game_state or config)
        game_state.set_optimal_decisions(optimal_decisions)
        
        # Call the service function to add test users
        users_added = test_player_service.add_test_players(game_state, count, optimal_decisions)
                
        # Notify all clients of the update
        socketio.emit('players_added', {'count': count, 'users': users_added})
        
        return jsonify({
            'success': True, 
            'count': len(users_added),
            'users': users_added
        })
    except Exception as e:
        app.logger.error(f"Error adding test users: {str(e)}")
        # Consider more specific error handling/logging
        return jsonify({'success': False, 'error': 'Failed to add test users due to an internal error'}), 500

@app.route('/api/set_policy', methods=['POST'])
def set_policy():
    if not session.get('is_professor'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.json
        app.logger.info(f"Received policy update data: {data}")
        
        # Standardize tax rates format - always use a tax_rates object
        tax_rates = data.get('tax_rates', {})
        if not tax_rates:
            # If tax_rates not provided, look for individual tax fields
            tax_rates = {
                'young': data.get('tax_young', 0.0),
                'middle': data.get('tax_middle', 0.2),
                'old': data.get('tax_old', 0.0)
            }
        
        # Get tax rates from the standardized object
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
        
        # Update the game state parameters (but don't calculate equilibrium yet)
        # This allows us to return a quick response to the user
        if tax_rate_young is not None:
            game_state.tax_rate_young = tax_rate_young
        if tax_rate_middle is not None:
            game_state.tax_rate_middle = tax_rate_middle
        if tax_rate_old is not None:
            game_state.tax_rate_old = tax_rate_old
        if pension_rate is not None:
            game_state.pension_rate = pension_rate
        if borrowing_limit is not None:
            game_state.borrowing_limit = borrowing_limit
        if target_stock is not None:
            game_state.target_stock = target_stock
        if num_test_players is not None:
            game_state._update_test_players(num_test_players)
        if income_young is not None:
            game_state.income_young = income_young
        if income_middle is not None:
            game_state.income_middle = income_middle
        if income_old is not None:
            game_state.income_old = income_old
            
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
        
        # Send initial update to clients with current values
        app.logger.info(f"Sending initial policy update to clients. Borrowing limit: {policy_update['policy']['borrowing_limit']}")
        socketio.emit('policy_updated', policy_update)
        
        # Only if the interest rate is not manually set, we need to calculate the equilibrium
        if interest_rate is None:
            # Launch a background thread to calculate the equilibrium
            def background_equilibrium_calculation():
                try:
                    # Calculate equilibrium interest rate
                    new_rate = game_state.calculate_equilibrium()
                    
                    # Update the game state with the new rate
                    game_state.interest_rate = new_rate
                    
                    # Create an updated policy payload
                    updated_policy = {
                        'policy': {
                            'interest_rate': new_rate,
                            'borrowing_limit': game_state.borrowing_limit,
                            'taxes': {
                                'young': game_state.tax_rate_young,
                                'middle': game_state.tax_rate_middle,
                                'old': game_state.tax_rate_old
                            },
                            'government_debt': game_state.government_debt
                        },
                        'is_equilibrium_update': True
                    }
                    
                    app.logger.info(f"Equilibrium calculation complete. New interest rate: {new_rate}")
                    
                    # Send the updated interest rate to all clients
                    socketio.emit('policy_updated', updated_policy)
                except Exception as e:
                    app.logger.error(f"Error in background equilibrium calculation: {str(e)}")
                    app.logger.exception("Full traceback:")
            
            # Start the background thread
            app.logger.info("Starting background equilibrium calculation...")
            thread = threading.Thread(target=background_equilibrium_calculation)
            thread.daemon = True  # Make sure the thread doesn't block app shutdown
            thread.start()
            
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error setting policy: {str(e)}")
        app.logger.exception("Full traceback:")
        return jsonify({'success': False, 'message': 'Failed to set policy due to an internal error'})

@app.route('/api/advance_round', methods=['POST'])
def advance_round():
    """API endpoint for professor to advance to the next round"""
    try:
        data = request.json or {}
        force = data.get('force', False)
        
        # Force auto-generation of test user decisions first
        test_user_ids = [user_id for user_id in game_state.pending_decisions 
                          if game_state.is_test_user(user_id) and user_id in game_state.users]
        
        app.logger.info(f"Handling {len(test_user_ids)} pending test users before advancing round...")
        
        # First try using the game_state's built-in method
        game_state.generate_test_player_decisions()
        
        # If that didn't clear all test users, use direct override approach
        remaining_test_users = [user_id for user_id in game_state.pending_decisions 
                                if game_state.is_test_user(user_id) and user_id in game_state.users]
        
        if remaining_test_users:
            app.logger.info(f"Still have {len(remaining_test_users)} test users that need force-decisions")
            for user_id in remaining_test_users:
                force_minimal_decision(user_id)
        
        # Make sure no human users are left in pending decisions
        remaining_human_users = [game_state.users[uid].name for uid in game_state.pending_decisions 
                                 if not game_state.is_test_user(uid) and uid in game_state.users]
        
        if remaining_human_users and not force:
            app.logger.warning(f"Cannot advance round: waiting for human users: {remaining_human_users}")
            return jsonify({
                'success': False, 
                'error': f'Waiting for decisions from human users: {", ".join(remaining_human_users)}'
            }), 400
        
        # If there are human users pending but force is True, remove them from pending
        if remaining_human_users and force:
            app.logger.info(f"Force advancing round with {len(remaining_human_users)} human users pending")
            for uid in list(game_state.pending_decisions):
                if not game_state.is_test_user(uid) and uid in game_state.users:
                    force_minimal_decision(uid)
        
        # At this point we should be ready to run the round
        # But we'll split this into two phases:
        # 1. First, do everything except calculate_equilibrium so we can respond quickly
        # 2. Then do the slower equilibrium calculation in the background and update when done

        # PHASE 1: Fast round advancement
        app.logger.info(f"Running initial phase of round {game_state.current_round}...")
        
        # Store round data (with current interest rate, will be updated later)
        round_data = {
            'round': game_state.current_round,
            'interest_rate': game_state.interest_rate,
            'tax_young': game_state.tax_rate_young,
            'tax_middle': game_state.tax_rate_middle,
            'tax_old': game_state.tax_rate_old,
            'government_debt': game_state.government_debt,
            'borrowing_limit': game_state.borrowing_limit,
            'users': {user_id: game_state.users[user_id].get_state() for user_id in game_state.users}
        }
        game_state.previous_rounds.append(round_data)
        
        # Advance to next round
        game_state.current_round += 1
        
        # Advance all users' age stages
        for user in game_state.users.values():
            user.advance_age()
        
        # Reset pending decisions for the new round
        game_state.pending_decisions = set(game_state.users.keys())
        
        # Immediately generate decisions for test users for the next round
        game_state.generate_test_player_decisions()
        
        # Get aggregates for the initial update
        aggregates = game_state.compute_aggregates()
        
        # Create initial event data with current policy and aggregates
        initial_event_data = {
            'round': game_state.current_round,
            'policy': {
                'interest_rate': game_state.interest_rate,  # Current rate, will be updated
                'borrowing_limit': game_state.borrowing_limit,
                'taxes': {
                    'young': game_state.tax_rate_young,
                    'middle': game_state.tax_rate_middle,
                    'old': game_state.tax_rate_old
                }
            },
            'aggregates': aggregates,
            'waiting_for': list(game_state.pending_decisions),
            'phase': 'initial'
        }

        # Send the initial notification to all clients
        socketio.emit('round_advanced', initial_event_data)
        
        # Start the background phase
        def background_equilibrium_for_round():
            try:
                # PHASE 2: Calculate the equilibrium interest rate (slow operation)
                app.logger.info("Computing equilibrium interest rate in background...")
                new_rate = game_state.calculate_equilibrium()
                
                # Update the stored rate
                game_state.interest_rate = new_rate
                
                # Update the stored round data with the new rate
                if len(game_state.previous_rounds) > 0:
                    game_state.previous_rounds[-1]['interest_rate'] = new_rate
                
                # Get updated aggregates with the new rate
                updated_aggregates = game_state.compute_aggregates()
                
                # Create complete event data
                updated_event_data = {
                    'round': game_state.current_round,
                    'policy': {
                        'interest_rate': new_rate,
                        'borrowing_limit': game_state.borrowing_limit,
                        'taxes': {
                            'young': game_state.tax_rate_young,
                            'middle': game_state.tax_rate_middle,
                            'old': game_state.tax_rate_old
                        }
                    },
                    'aggregates': updated_aggregates,
                    'phase': 'complete',
                    'waiting_for': list(game_state.pending_decisions)
                }
                
                # Send the updated interest rate to all clients
                socketio.emit('policy_updated', updated_event_data)
                app.logger.info(f"Background equilibrium calculation complete: {new_rate}")
            except Exception as e:
                app.logger.error(f"Error in background equilibrium calculation: {str(e)}")
                app.logger.exception("Exception during background equilibrium calculation:")
        
        # Start the background thread
        thread = threading.Thread(target=background_equilibrium_for_round)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'round': game_state.current_round})
            
    except Exception as e:
        app.logger.error(f"Error advancing round: {str(e)}")
        app.logger.exception("Exception during round advancement:")
        return jsonify({'success': False, 'error': 'An internal error has occurred.'}), 500

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
        app.logger.error(f"Error resetting game: {str(e)}")
        app.logger.exception("Exception during game reset:")
        return jsonify({
            'success': False,
            'error': 'Failed to reset game due to an internal error.'
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
        app.logger.exception("Exception during game state retrieval:")
        return jsonify({'success': False, 'message': 'Failed to retrieve game state due to an internal error.'})

@socketio.on('connect')
def handle_connect():
    """Handle new socket connection"""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle socket disconnection"""
    print('Client disconnected')

# Add this after imports but before route definitions
def force_minimal_decision(user_id):
    """
    Force a minimal safe decision for a user who hasn't submitted one.
    This is used for advancing rounds when some users haven't decided.
    
    Args:
        user_id: ID of the user to force a decision for
        
    Returns:
        bool: True if decision was successfully forced, False otherwise
    """
    if user_id not in game_state.users:
        app.logger.warning(f"Cannot force decision for unknown user: {user_id}")
        return False
        
    user = game_state.users[user_id]
    app.logger.info(f"Forcing safe decision for {user.name} ({user.age_stage})")
    
    try:
        if user.age_stage == 'Y':
            # For Young: minimal safe borrowing
            success = game_state.record_decision(user_id, 'borrow', 1.0)
            
            # Create minimal demand curve if needed
            if success and not hasattr(user, 'demand_curve') or not user.demand_curve:
                # Create a simple demand curve with minimal borrowing
                minimal_demand_curve = []
                interest_rates = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                
                if game_state.make_optimal_decisions:
                    # For optimal decisions - maximum borrowing at each rate
                    for rate in interest_rates:
                        max_borrowing = game_state.borrowing_limit / (1 + rate/100)
                        minimal_demand_curve.append({
                            'interestRate': rate,
                            'borrowingAmount': round(max_borrowing, 1)
                        })
                else:
                    # Simple conservative curve
                    for rate in interest_rates:
                        # Calculate adjusted borrowing limit based on interest rate
                        adjusted_borrowing_limit = game_state.borrowing_limit / (1 + rate/100)
                        # Use a small percentage of the adjusted limit
                        borrowing_amount = min(1.0, adjusted_borrowing_limit * 0.05)
                        minimal_demand_curve.append({
                            'interestRate': rate,
                            'borrowingAmount': round(borrowing_amount, 1)
                        })
                
                # Store the minimal demand curve
                user.demand_curve = minimal_demand_curve
                
            return success
                
        elif user.age_stage == 'M':
            # Middle-aged: minimal safe saving
            return game_state.record_decision(user_id, 'save', 1.0)
            
        elif user.age_stage == 'O':
            # Old: consume all (only option)
            return game_state.record_decision(user_id, 'consume', 0)
            
        else:
            app.logger.warning(f"Unknown age stage {user.age_stage} for user {user_id}")
            return False
            
    except Exception as e:
        app.logger.error(f"Error forcing decision for {user_id}: {str(e)}")
        return False

if __name__ == '__main__':
    # For development - use production WSGI server in production
    port = config.PORT
    debug = config.DEBUG
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
