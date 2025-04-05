import os
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
from dotenv import load_dotenv
from models.game_state import GameState
from models.user import User
from config.config import get_config

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
    
    # Validate inputs
    if not all([user_id, decision_type, amount is not None]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    try:
        amount = float(amount)
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
    
    # Get game state specific to this user if provided
    if user_id:
        state = game_state.get_user_state(user_id)
    else:
        state = game_state.get_full_state()
    
    return jsonify(state)

@app.route('/api/set_policy', methods=['POST'])
def set_policy():
    """API endpoint for professor to set policy parameters"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Extract policy parameters
        tax_young = data.get('tax_young', 0)
        tax_middle = data.get('tax_middle', 0)
        tax_old = data.get('tax_old', 0)
        government_debt = data.get('government_debt', 0)
        borrowing_limit = data.get('borrowing_limit', 100)
        
        # Update game state with new policies
        game_state.set_policy(
            tax_young=tax_young,
            tax_middle=tax_middle,
            tax_old=tax_old,
            government_debt=government_debt,
            borrowing_limit=borrowing_limit
        )
        
        # Notify all clients of policy update
        socketio.emit('policy_updated', data)
        
        return jsonify({'success': True})
    except Exception as e:
        # Log the error and return helpful response
        print(f"Error updating policy: {str(e)}")
        return jsonify({'error': f'Failed to update policy: {str(e)}'}), 500

@app.route('/api/advance_round', methods=['POST'])
def advance_round():
    """API endpoint for professor to advance to the next round"""
    # Calculate equilibrium and advance game state
    game_state.run_round()
    
    # Notify all clients of round advancement
    socketio.emit('round_advanced', 
                 {'round': game_state.current_round})
    
    return jsonify({'success': True, 'round': game_state.current_round})

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
