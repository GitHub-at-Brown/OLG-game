import numpy as np
from models.user import User

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
        self.tax_young = 0.0
        self.tax_middle = 0.0
        self.tax_old = 0.0
        self.government_debt = 0.0
        self.borrowing_limit = 100.0
        
        # Equilibrium variables
        self.interest_rate = 0.03  # Initial interest rate (3%)
        self.pending_decisions = set()  # Track users who haven't submitted decisions
        
        # Income parameters (could be made configurable)
        self.income_young = 0.0
        self.income_middle = 60.0
        self.income_old = 0.0
    
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
    
    def set_policy(self, tax_young=None, tax_middle=None, tax_old=None, 
                  government_debt=None, borrowing_limit=None):
        """Update policy parameters"""
        if tax_young is not None:
            self.tax_young = tax_young
        if tax_middle is not None:
            self.tax_middle = tax_middle
        if tax_old is not None:
            self.tax_old = tax_old
        if government_debt is not None:
            self.government_debt = government_debt
        if borrowing_limit is not None:
            self.borrowing_limit = borrowing_limit
    
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
            income -= self.tax_young
        elif user.age_stage == 'M':
            income -= self.tax_middle
        else:  # Old
            income -= self.tax_old
            
        # Validate decision based on constraints
        if user.age_stage == 'Y' and decision_type == 'borrow':
            # Young can only borrow up to the borrowing limit
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
        r_min, r_max = -0.5, 2.0  # Interest rate bounds (-50% to 200%)
        tol = 1e-6  # Tolerance
        max_iter = 100  # Maximum iterations
        
        for _ in range(max_iter):
            r_mid = (r_min + r_max) / 2
            imbalance = market_imbalance(r_mid)
            
            if abs(imbalance) < tol:
                return r_mid
            
            if imbalance > 0:  # Excess demand, increase rate
                r_min = r_mid
            else:  # Excess supply, decrease rate
                r_max = r_mid
        
        # If we reach here, return the midpoint of the final interval
        return (r_min + r_max) / 2
    
    def run_round(self):
        """
        Run a round of the game:
        1. Calculate the equilibrium interest rate
        2. Update all users' states
        3. Advance all users to the next age stage
        4. Store the round results and prepare for the next round
        """
        # Only proceed if all decisions are in or we're forcing the round to advance
        if self.pending_decisions:
            return False
        
        # Calculate equilibrium interest rate
        self.interest_rate = self.calculate_equilibrium()
        
        # Store current round data
        round_data = {
            'round': self.current_round,
            'interest_rate': self.interest_rate,
            'government_debt': self.government_debt,
            'borrowing_limit': self.borrowing_limit,
            'taxes': {
                'young': self.tax_young,
                'middle': self.tax_middle,
                'old': self.tax_old
            },
            'users': {uid: user.get_state() for uid, user in self.users.items()}
        }
        self.previous_rounds.append(round_data)
        
        # Advance to next round
        self.current_round += 1
        
        # Advance all users to next age stage
        for user in self.users.values():
            user.advance_age()
        
        # Reset pending decisions for next round
        self.pending_decisions = set(self.users.keys())
        
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
                    'young': self.tax_young,
                    'middle': self.tax_middle,
                    'old': self.tax_old
                },
                'government_debt': self.government_debt
            },
            'waiting_for_decisions': bool(self.pending_decisions)
        }
    
    def get_full_state(self):
        """Get the complete game state (for professor view)"""
        # Calculate aggregate statistics
        young_users = [u for u in self.users.values() if u.age_stage == 'Y']
        middle_users = [u for u in self.users.values() if u.age_stage == 'M']
        old_users = [u for u in self.users.values() if u.age_stage == 'O']
        
        total_young_borrowing = sum(u.current_borrowing for u in young_users)
        total_middle_saving = sum(u.current_saving for u in middle_users if u.current_saving > 0)
        total_middle_borrowing = sum(abs(u.current_saving) for u in middle_users if u.current_saving < 0)
        
        return {
            'round': self.current_round,
            'policy': {
                'interest_rate': self.interest_rate,
                'government_debt': self.government_debt,
                'borrowing_limit': self.borrowing_limit,
                'taxes': {
                    'young': self.tax_young,
                    'middle': self.tax_middle,
                    'old': self.tax_old
                }
            },
            'users': {uid: user.get_state() for uid, user in self.users.items()},
            'aggregates': {
                'young_count': len(young_users),
                'middle_count': len(middle_users),
                'old_count': len(old_users),
                'total_young_borrowing': total_young_borrowing,
                'total_middle_saving': total_middle_saving,
                'total_middle_borrowing': total_middle_borrowing,
                'loan_demand': total_young_borrowing + self.government_debt,
                'loan_supply': total_middle_saving
            },
            'waiting_for': list(self.pending_decisions),
            'history': self.previous_rounds
        }
