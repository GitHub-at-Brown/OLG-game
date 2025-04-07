import numpy as np
import random
from models.user import User
import logging
from services.test_player_service import generate_demand_curve, interpolate_from_demand_curve, generate_test_player_decisions as service_generate_test_player_decisions

class GameState:
    """
    Manages the overall state of the OLG game, including users, rounds,
    and equilibrium calculations.
    """
    
    def __init__(self):
        self.users = {}  # Dictionary of users by user_id
        self.current_round = 1  # Start at round 1 instead of 0
        self.previous_rounds = []  # History of previous rounds
        
        # Policy parameters
        self.tax_rate_young = 0.0
        self.tax_rate_middle = 0.0
        self.tax_rate_old = 0.0
        self.government_debt = 0.0
        self.borrowing_limit = 100.0
        self.target_stock = 80.0
        self.num_test_players = 0
        
        # Equilibrium variables
        self.interest_rate = 0.03  # Initial interest rate (3%)
        self.pending_decisions = set()  # Track users who haven't submitted decisions
        
        # Income parameters (could be made configurable)
        self.income_young = 0.0
        self.income_middle = 60.0
        self.income_old = 0.0
        
        # Flag to determine if test players make optimal decisions
        self.make_optimal_decisions = False
    
    def add_user(self, user_id, name=None, avatar=None):
        """Add a new user to the game"""
        if user_id not in self.users:
            self.users[user_id] = User(user_id, name, avatar)
            self.pending_decisions.add(user_id)
            return True
        return False
    
    def remove_user(self, user_id):
        """Remove a user from the game"""
        if user_id in self.users:
            del self.users[user_id]
            if user_id in self.pending_decisions:
                self.pending_decisions.remove(user_id)
            return True
        return False
    
    def set_policy(self, tax_rate_young=None, tax_rate_middle=None, tax_rate_old=None, 
                  pension_rate=None, borrowing_limit=None, target_stock=None, num_test_players=None,
                  income_young=None, income_middle=None, income_old=None):
        """Set policy parameters."""
        print(f"Setting policy: tax_rate_young={tax_rate_young}, tax_rate_middle={tax_rate_middle}, tax_rate_old={tax_rate_old}, borrowing_limit={borrowing_limit}")
        
        if tax_rate_young is not None:
            self.tax_rate_young = tax_rate_young
            print(f"Updated tax_rate_young to {self.tax_rate_young}")
            
        if tax_rate_middle is not None:
            self.tax_rate_middle = tax_rate_middle
            print(f"Updated tax_rate_middle to {self.tax_rate_middle}")
            
        if tax_rate_old is not None:
            self.tax_rate_old = tax_rate_old
            print(f"Updated tax_rate_old to {self.tax_rate_old}")
            
        if pension_rate is not None:
            self.pension_rate = pension_rate
            
        if borrowing_limit is not None:
            self.borrowing_limit = borrowing_limit
            print(f"Updated borrowing_limit to {self.borrowing_limit}")
            
        if target_stock is not None:
            self.target_stock = target_stock
            
        if num_test_players is not None:
            self._update_test_players(num_test_players)
        
        # Set income parameters
        if income_young is not None:
            self.income_young = income_young
            
        if income_middle is not None:
            self.income_middle = income_middle
            
        if income_old is not None:
            self.income_old = income_old
            
        # Calculate equilibrium interest rate
        self._calculate_equilibrium()
    
    def record_decision(self, user_id, decision_type, amount):
        """
        Record a decision for a user
        
        Args:
            user_id: ID of the user making the decision
            decision_type: 'borrow' or 'save'
            amount: Amount to borrow or save
            
        Returns:
            True if decision was valid and recorded, False otherwise
        """
        if user_id not in self.users:
            return False
            
        user = self.users[user_id]
        
        # Get relevant income for the user's stage
        if user.age_stage == 'Y':
            income = self.income_young
        elif user.age_stage == 'M':
            income = self.income_middle
        else:  # Old
            income = self.income_old
        
        # Apply taxes
        if user.age_stage == 'Y':
            income -= self.tax_rate_young
        elif user.age_stage == 'M':
            income -= self.tax_rate_middle
        else:  # Old
            income -= self.tax_rate_old
            
        # Validate decision based on constraints
        if user.age_stage == 'Y' and decision_type == 'borrow':
            # Young can only borrow up to the debt limit
            max_borrow = self.borrowing_limit
            # Just ensure amount is positive and not exceeding the limit
            if amount < 0 or amount > max_borrow:
                print(f"Invalid young borrowing: {amount} > {max_borrow}")
                return False
                
        elif user.age_stage == 'M':
            # Middle-aged can save or borrow
            # Calculate disposable income after debt repayment
            disposable_income = income
            if user.assets < 0:  # If they have debt from youth
                disposable_income -= (1 + self.interest_rate) * abs(user.assets)
                
            # For middle-aged users, we just verify their decision is valid:
            # - If saving, ensure amount is positive
            # - If borrowing, ensure it's within reasonable limits
            if (decision_type == 'save' and amount < 0) or \
               (decision_type == 'borrow' and (amount < 0 or amount > self.borrowing_limit)):
                print(f"Invalid middle-aged decision: {decision_type}, {amount}")
                return False
        
        # Record the decision
        success = user.record_decision(decision_type, amount, self.interest_rate, income)
        
        # Mark this user's decision as submitted
        if success and user_id in self.pending_decisions:
            self.pending_decisions.remove(user_id)
            
        return success
    
    def calculate_equilibrium(self):
        """
        Calculate the equilibrium interest rate that clears the loan market
        
        The market clearing condition is:
        sum(B^y_i) + B^g = -sum(B^m_j)
        
        Where:
        - B^y_i: borrowing of young agents
        - B^g: government debt
        - B^m_j: saving/borrowing of middle-aged agents
        
        We use a bisection method to find the interest rate that satisfies this condition
        """
        def market_imbalance(rate):
            """Calculate loan market excess demand at a given interest rate"""
            # Temporarily set interest rate
            old_rate = self.interest_rate
            self.interest_rate = rate
            
            # Safety check: ensure rate is not too close to -1 to avoid division by zero
            if abs(rate + 1.0) < 1e-8:  # If r is very close to -1
                rate = -0.9999  # Use -99.99% instead
            
            # Calculate loan demand (young borrowing + government)
            young_borrowing = sum(
                min(self.borrowing_limit / (1 + rate), user.current_borrowing)
                for user in self.users.values() 
                if user.age_stage == 'Y'
            )
            loan_demand = young_borrowing + self.government_debt
            
            # Calculate loan supply (middle-aged saving)
            loan_supply = sum(
                user.current_saving 
                for user in self.users.values() 
                if user.age_stage == 'M' and user.current_saving > 0
            )
            
            # Reset interest rate
            self.interest_rate = old_rate
            
            # Return the excess demand
            return loan_demand - loan_supply
        
        # Use bisection method to find equilibrium interest rate
        r_min, r_max = -1.0, 2.0  # Interest rate bounds (-100% to 200%)
        tol = 1e-6  # Tolerance
        max_iter = 100  # Maximum iterations
        
        # Check values at bounds to ensure a solution exists within the range
        imbalance_min = market_imbalance(r_min)
        imbalance_max = market_imbalance(r_max)
        
        # If both bounds give the same sign, the solution may be outside range
        # Let's catch this and log a warning
        if (imbalance_min > 0 and imbalance_max > 0) or (imbalance_min < 0 and imbalance_max < 0):
            logging.warning(f"Equilibrium solution may be outside range [{r_min}, {r_max}]. "
                          f"Imbalance at r_min={r_min}: {imbalance_min}, "
                          f"Imbalance at r_max={r_max}: {imbalance_max}")
            
            # We'll still try to find the best available solution within our range
        
        # Bisection loop
        for iter_count in range(max_iter):
            r_mid = (r_min + r_max) / 2
            imbalance = market_imbalance(r_mid)
            
            if abs(imbalance) < tol:
                logging.info(f"Equilibrium found at r={r_mid:.6f} after {iter_count+1} iterations")
                return r_mid
            
            if imbalance > 0:  # Excess demand, increase rate
                r_min = r_mid
            else:  # Excess supply, decrease rate
                r_max = r_mid
        
        # If we reach here, return the midpoint of the final interval
        logging.warning(f"Bisection hit max iterations ({max_iter}). Final interval: [{r_min}, {r_max}]")
        return (r_min + r_max) / 2
    
    def is_test_user(self, user_id):
        """Check if a user is a test user (based on ID prefix)"""
        return user_id.startswith("test_")
    
    def set_optimal_decisions(self, make_optimal_decisions):
        """Set whether test players should make optimal decisions"""
        self.make_optimal_decisions = make_optimal_decisions
    
    def _calculate_equilibrium(self):
        """
        Calculate the equilibrium interest rate by calling the existing method.
        This is a wrapper for compatibility with calls to this method name.
        """
        self.interest_rate = self.calculate_equilibrium()
        return self.interest_rate
    
    def _update_test_players(self, num_test_players):
        """
        Updates the number of test players in the game.
        If the number increases, adds more test players.
        If the number decreases, removes excess test players.
        
        Args:
            num_test_players: The target number of test players
        """
        # Count current test players
        current_test_players = [uid for uid in self.users if self.is_test_user(uid)]
        current_count = len(current_test_players)
        
        # If we have too many, remove some
        if current_count > num_test_players:
            # Sort by ID so removal is deterministic
            to_remove = sorted(current_test_players)[:(current_count - num_test_players)]
            for uid in to_remove:
                self.remove_user(uid)
            print(f"Removed {len(to_remove)} test players")
            
        # If we need more, add them
        elif current_count < num_test_players:
            to_add = num_test_players - current_count
            import random
            from models.user import User
            
            # Use proper import for test player names
            from services.test_player_service import TEST_PLAYER_NAMES
            
            # Add the required number of test players
            for i in range(to_add):
                user_id = f"test_{i}_{random.randint(1000, 9999)}"
                # Pick a random name from the list
                name = random.choice(TEST_PLAYER_NAMES) 
                # Create and add the user
                self.users[user_id] = User(user_id, name)
                self.pending_decisions.add(user_id)
            
            print(f"Added {to_add} test players")
        
        # Update the stored number of test players
        self.num_test_players = num_test_players
    
    def generate_test_player_decisions(self):
        """
        Generate decisions for test users who haven't submitted decisions yet.
        Uses the centralized service implementation.
        """
        # Delegate to the service implementation, passing the game_state (self)
        service_generate_test_player_decisions(self)
    
    def run_round(self):
        """
        Run a round of the game:
        1. Generate test user decisions first
        2. Calculate the equilibrium interest rate if all decisions submitted
        3. Update all users' states
        4. Advance all users to the next age stage
        5. Store the round results and prepare for the next round
        6. Automatically generate decisions for test users for the next round
        """
        # First, generate decisions for any test users who haven't submitted yet
        self.generate_test_player_decisions()
        
        # Only proceed if all decisions are in after test user decisions are generated
        if self.pending_decisions:
            logging.warning(f"Cannot run round: {len(self.pending_decisions)} users have not submitted decisions")
            logging.warning(f"Waiting for: {[self.users[user_id].name for user_id in self.pending_decisions if user_id in self.users]}")
            return False
        
        # Calculate equilibrium interest rate
        self.interest_rate = self.calculate_equilibrium()
        
        # Calculate aggregate statistics using the aggregator method
        aggregates = self.compute_aggregates()
        
        # Store round data with aggregates
        round_data = {
            'round': self.current_round,
            'interest_rate': self.interest_rate,
            'tax_young': self.tax_rate_young,
            'tax_middle': self.tax_rate_middle,
            'tax_old': self.tax_rate_old,
            'government_debt': self.government_debt,
            'borrowing_limit': self.borrowing_limit,
            'aggregates': aggregates,
            'users': {user_id: user.get_state() for user_id, user in self.users.items()}
        }
        self.previous_rounds.append(round_data)
        
        # Advance to next round
        self.current_round += 1
        
        # Advance all users' age stages
        for user in self.users.values():
            user.advance_age()
        
        # Reset pending decisions for the new round
        self.pending_decisions = set(self.users.keys())
        
        # Immediately generate decisions for test users for the next round
        self.generate_test_player_decisions()
        
        return True
    
    def get_user_state(self, user_id):
        """Get the current state for a specific user"""
        if user_id not in self.users:
            return {'error': 'User not found'}
            
        user = self.users[user_id]
        
        # Calculate the max borrowing for Young users
        max_borrowing = self.borrowing_limit / (1 + self.interest_rate) if user.age_stage == 'Y' else 0
        
        return {
            'round': self.current_round,
            'user': user.get_state(),
            'policy': {
                'interest_rate': self.interest_rate,
                'borrowing_limit': self.borrowing_limit,
                'taxes': {
                    'young': self.tax_rate_young,
                    'middle': self.tax_rate_middle,
                    'old': self.tax_rate_old
                },
                'government_debt': self.government_debt
            },
            'waiting_for_decisions': bool(self.pending_decisions)
        }
    
    def compute_aggregates(self):
        """Compute and return a dictionary of commonly needed aggregated values."""
        # Group users by age stage for easier calculations
        young_users = [u for u in self.users.values() if u.age_stage == 'Y']
        middle_users = [u for u in self.users.values() if u.age_stage == 'M']
        old_users = [u for u in self.users.values() if u.age_stage == 'O']
        
        # Calculate key aggregates
        total_young_borrowing = sum(u.current_borrowing for u in young_users)
        total_middle_saving = sum(u.current_saving for u in middle_users if u.current_saving > 0)
        total_middle_borrowing = sum(abs(u.current_saving) for u in middle_users if u.current_saving < 0)
        
        # Calculate loan market balance
        loan_balance = total_middle_saving - (total_young_borrowing + self.government_debt)
        
        return {
            'young_count': len(young_users),
            'middle_count': len(middle_users),
            'old_count': len(old_users),
            'total_young_borrowing': total_young_borrowing,
            'total_middle_saving': total_middle_saving,
            'total_middle_borrowing': total_middle_borrowing,
            'loan_demand': total_young_borrowing + self.government_debt,
            'loan_supply': total_middle_saving,
            'loan_balance': loan_balance
        }
    
    def get_full_state(self):
        """Get the complete game state (for professor view)"""
        # Calculate aggregate statistics using the aggregator method
        aggregates = self.compute_aggregates()
        
        return {
            'round': self.current_round,
            'policy': {
                'interest_rate': self.interest_rate,
                'government_debt': self.government_debt,
                'borrowing_limit': self.borrowing_limit,
                'taxes': {
                    'young': self.tax_rate_young,
                    'middle': self.tax_rate_middle,
                    'old': self.tax_rate_old
                }
            },
            'users': {uid: user.get_state() for uid, user in self.users.items()},
            'aggregates': aggregates,
            'waiting_for': list(self.pending_decisions),
            'history': self.previous_rounds
        }
