from typing import Dict, List, Tuple
import pandas as pd
import yfinance as yf

class FinanceCalculator:
    @staticmethod
    def calculate_cost_basis(transactions: pd.DataFrame) -> float:
        """Calculate the cost basis for a given set of transactions"""
        pass

    @staticmethod
    def calculate_gain_loss(cost_basis: float, current_price: float, units: float) -> Tuple[float, float]:
        """Calculate total and percentage gain/loss"""
        pass

    @staticmethod
    def get_current_prices(tickers: List[str]) -> Dict[str, float]:
        """Fetch current prices from Yahoo Finance"""
        pass

    @staticmethod
    def calculate_portfolio_weights(holdings: Dict[str, float], total_value: float) -> Dict[str, float]:
        """Calculate current portfolio weights"""
        pass 