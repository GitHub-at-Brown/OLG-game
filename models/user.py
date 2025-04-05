class User:
    """
    Represents a player (student) in the OLG game. Each user has a lifecycle stage,
    assets, and decision history.
    
    Lifecycle stages:
    - 'Y': Young
    - 'M': Middle-aged
    - 'O': Old
    """
    
    def __init__(self, user_id, name=None, avatar=None):
        self.user_id = user_id
        self.name = name or f"Player {user_id}"
        self.avatar = avatar or "default_avatar"
        self.age_stage = 'Y'  # Default to Young
        self.assets = 0.0  # Net assets
        
        # Decision history
        self.decisions = []
        
        # Current round data
        self.current_consumption = 0.0
        self.current_borrowing = 0.0
        self.current_saving = 0.0
        self.current_utility = 0.0
        
        # Previous round data for display
        self.previous_consumption = 0.0
        self.previous_decision = 0.0
        self.previous_utility = 0.0
    
    def advance_age(self):
        """Move the user to the next lifecycle stage"""
        if self.age_stage == 'Y':
            self.age_stage = 'M'
        elif self.age_stage == 'M':
            self.age_stage = 'O'
        else:  # User is Old, reborn as Young
            self.age_stage = 'Y'
            self.assets = 0.0  # Reset assets on rebirth
    
    def record_decision(self, decision_type, amount, interest_rate, income=0.0):
        """
        Record a user's decision for the current round
        
        Args:
            decision_type: 'borrow' (Young) or 'save' (Middle-aged)
            amount: The amount to borrow or save
            interest_rate: Current interest rate (r)
            income: Current income for the stage (Y^y, Y^m, or Y^o)
        
        Returns:
            True if the decision is valid, False otherwise
        """
        # Save previous round data
        self.previous_consumption = self.current_consumption
        self.previous_decision = self.current_borrowing if self.age_stage == 'Y' else self.current_saving
        self.previous_utility = self.current_utility
        
        # Process current decision based on life stage
        if self.age_stage == 'Y':
            # Young can only borrow
            if decision_type != 'borrow' or amount < 0:
                return False
                
            self.current_borrowing = amount
            # Young consumption = borrowing (+ income if any)
            self.current_consumption = amount + income
            self.assets = -amount  # Negative value represents debt
            
        elif self.age_stage == 'M':
            # Middle-aged can save or borrow more
            if decision_type not in ['save', 'borrow']:
                return False
                
            # Convert to saving (positive = saving, negative = borrowing)
            amount = amount if decision_type == 'save' else -amount
            
            # Check if they have enough resources after repaying young debt
            disposable_income = income - (1 + interest_rate) * (self.assets if self.assets < 0 else 0)
            
            # Ensure consumption is non-negative
            if disposable_income + amount < 0:
                return False
                
            self.current_saving = amount
            self.current_consumption = disposable_income + amount
            self.assets = amount  # Update assets with new saving/borrowing
            
        elif self.age_stage == 'O':
            # Old automatically consume everything
            # No decision needed, but we'll record it
            self.current_consumption = income + (1 + interest_rate) * (self.assets if self.assets > 0 else 0)
            self.assets = 0  # Reset assets
        
        # Calculate utility (using log utility function)
        import math
        self.current_utility = math.log(max(self.current_consumption, 0.1))  # Avoid log(0)
        
        # Record the decision for history
        self.decisions.append({
            'age_stage': self.age_stage,
            'decision_type': decision_type,
            'amount': amount,
            'consumption': self.current_consumption,
            'utility': self.current_utility
        })
        
        return True
    
    def get_state(self):
        """Return the current state of the user for API responses"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'avatar': self.avatar,
            'age_stage': self.age_stage,
            'assets': self.assets,
            'current_consumption': self.current_consumption,
            'current_borrowing': self.current_borrowing if self.age_stage == 'Y' else 0,
            'current_saving': self.current_saving if self.age_stage == 'M' else 0,
            'current_utility': self.current_utility,
            'previous_consumption': self.previous_consumption,
            'previous_decision': self.previous_decision,
            'previous_utility': self.previous_utility
        }
