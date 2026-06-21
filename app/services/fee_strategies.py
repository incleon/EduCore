"""
Fee Calculation Strategies (Strategy Pattern)
=============================================
Allows interchangeable fee calculation logic without altering the service.
Adheres to the Open-Closed Principle (OCP).
"""
from abc import ABC, abstractmethod
from datetime import date
from app.models.fee import Fee, FeeStatus

class FeeCalculationStrategy(ABC):
    """Abstract Strategy interface."""
    @abstractmethod
    def calculate(self, fee: Fee, additional_payment: float) -> dict:
        """Returns the dictionary of updates for the fee record."""
        pass

class StandardFeeStrategy(FeeCalculationStrategy):
    """Standard payment without penalties or discounts."""
    def calculate(self, fee: Fee, additional_payment: float) -> dict:
        new_paid = fee.paid_amount + additional_payment
        status = FeeStatus.PAID if new_paid >= fee.amount else FeeStatus.PARTIAL
        return {"paid_amount": new_paid, "status": status}

class LatePenaltyStrategy(FeeCalculationStrategy):
    """Adds a dynamic penalty if the fee is past due."""
    def __init__(self, penalty_per_day: float = 10.0):
        self.penalty_per_day = penalty_per_day

    def calculate(self, fee: Fee, additional_payment: float) -> dict:
        total_due = fee.amount
        
        # Calculate late penalty
        if fee.due_date and date.today() > fee.due_date:
            days_late = (date.today() - fee.due_date).days
            if days_late > 0:
                total_due += (days_late * self.penalty_per_day)
                
        new_paid = fee.paid_amount + additional_payment
        status = FeeStatus.PAID if new_paid >= total_due else FeeStatus.PARTIAL
        return {
            "paid_amount": new_paid, 
            "status": status,
            "remarks": f"Total due adjusted for late penalty: {total_due}" if total_due > fee.amount else fee.remarks
        }

class ScholarshipStrategy(FeeCalculationStrategy):
    """Applies a percentage discount."""
    def __init__(self, discount_percentage: float = 20.0):
        self.discount_percentage = discount_percentage

    def calculate(self, fee: Fee, additional_payment: float) -> dict:
        discounted_amount = fee.amount * (1 - self.discount_percentage / 100)
        new_paid = fee.paid_amount + additional_payment
        status = FeeStatus.PAID if new_paid >= discounted_amount else FeeStatus.PARTIAL
        return {
            "paid_amount": new_paid, 
            "status": status,
            "remarks": f"Scholarship applied. New due: {discounted_amount}"
        }
