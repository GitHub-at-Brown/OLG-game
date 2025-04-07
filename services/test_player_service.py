"""
Test player service module.
This is a temporary compatibility module for our optimizations.
"""

def add_test_players(game_state, count, optimal_decisions=False):
    """Add test players to the game state."""
    # Set whether test players make optimal decisions
    game_state.set_optimal_decisions(optimal_decisions)
    
    # Update the number of test players in the game state
    game_state._update_test_players(count)
    
    # Return the list of test players that were added
    # For compatibility, we'll return an empty list for now
    return []

def generate_test_player_decisions(game_state, optimal_decisions=None):
    """Generate decisions for test players."""
    # If optimal_decisions is provided, update the game state setting
    if optimal_decisions is not None:
        game_state.set_optimal_decisions(optimal_decisions)
    
    # Generate decisions for test players
    game_state.generate_test_player_decisions() 