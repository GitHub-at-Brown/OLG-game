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
    
    def record_decision(self, decision_type, amount, interest_rate=0.0, income=0.0):
        """
        Record a user's decision for the current round
        
        Args:
            decision_type: 'borrow' (Young), 'save' (Middle-aged), or 'consume' (Old)
            amount: The amount to borrow or save
            interest_rate: Current interest rate (r)
            income: Current income for the stage (Y^y, Y^m, or Y^o)
        
        Returns:
            True if the decision is valid, False otherwise
        """
        try:
            # Convert amount to float if needed
            amount = float(amount)
            
            # Save previous round data for display purposes
            self.previous_consumption = self.current_consumption
            self.previous_decision = self.current_borrowing if self.age_stage == 'Y' else self.current_saving
            self.previous_utility = self.current_utility
            
            # Process decision based on life stage
            if self.age_stage == 'Y':
                # Young can only borrow
                if decision_type != 'borrow':
                    print(f"Invalid decision type for Young: {decision_type}")
                    return False
                
                # Borrowing amount must be non-negative
                if amount < 0:
                    print(f"Invalid borrowing amount: {amount}")
                    return False
                    
                self.current_borrowing = amount
                self.current_consumption = amount + income
                self.assets = -amount  # Negative assets represent debt
                
            elif self.age_stage == 'M':
                # Calculate disposable income after debt repayment
                debt_repayment = 0
                if self.assets < 0:  # If they have debt from youth
                    debt_repayment = (1 + interest_rate) * abs(self.assets)
                
                disposable_income = income - debt_repayment
                
                # Special case for Middle-aged with negative disposable income
                if disposable_income <= 0:
                    # They're completely broke, so no saving or additional borrowing
                    # Just consume whatever income they have and keep the debt
                    print(f"Middle-aged player has negative disposable income: {disposable_income}. Setting zero saving.")
                    self.current_saving = 0
                    self.current_consumption = income  # They consume just their income
                    # Keep the existing debt from youth
                    
                    # Record the decision
                    import math
                    self.current_utility = math.log(max(self.current_consumption, 0.1))
                    self.decisions.append({
                        'age_stage': self.age_stage,
                        'decision_type': 'save',
                        'amount': 0,
                        'consumption': self.current_consumption,
                        'utility': self.current_utility
                    })
                    return True
                
                # Normal case with positive disposable income
                if decision_type == 'save':
                    # Cannot save more than disposable income
                    if amount < 0:
                        print(f"Cannot save negative amount: {amount}")
                        return False
                    if amount > disposable_income:
                        print(f"Cannot save {amount} with only {disposable_income} disposable income")
                        return False
                        
                    self.current_saving = amount
                    self.current_consumption = disposable_income - amount
                    self.assets = amount  # Positive assets represent savings
                    
                elif decision_type == 'borrow':
                    # Borrowing amount must be non-negative
                    if amount < 0:
                        print(f"Cannot borrow negative amount: {amount}")
                        return False
                        
                    self.current_saving = -amount  # Negative saving = borrowing
                    self.current_consumption = disposable_income + amount
                    self.assets = -amount  # Negative assets represent debt
                    
                else:
                    print(f"Invalid decision type for Middle-aged: {decision_type}")
                    return False
                
            elif self.age_stage == 'O':
                # Old automatically consume everything
                if decision_type != 'consume' and decision_type != '':
                    print(f"Invalid decision type for Old: {decision_type}")
                    return False
                    
                # Calculate consumption based on pension and assets
                self.current_consumption = income
                if self.assets > 0:  # Add any savings from middle age
                    self.current_consumption += (1 + interest_rate) * self.assets
                    
                self.assets = 0  # Reset assets
                
            else:
                # Unknown age stage
                print(f"Unknown age stage: {self.age_stage}")
                return False
                
            # Ensure consumption is not negative
            if self.current_consumption < 0:
                print(f"Negative consumption: {self.current_consumption}")
                return False
                
            # Calculate utility with log utility function
            import math
            self.current_utility = math.log(max(self.current_consumption, 0.1))  # Avoid log(0)
            
            # Record decision in history
            self.decisions.append({
                'age_stage': self.age_stage,
                'decision_type': decision_type,
                'amount': amount,
                'consumption': self.current_consumption,
                'utility': self.current_utility
            })
            
            return True
            
        except Exception as e:
            print(f"Error processing {self.age_stage} decision for {self.user_id}: {str(e)}")
            return False
    
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
