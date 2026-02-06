"""
Portfolio virtuel pour le backtesting
Gère les transactions, le cash, et calcule les performances
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Trade:
    """Représente une transaction"""
    date: datetime
    type: str  # 'BUY' ou 'SELL'
    ticker: str
    price: float
    quantity: int
    commission: float
    slippage: float
    total: float
    profit: Optional[float] = None
    return_pct: Optional[float] = None


class BacktestPortfolio:
    """
    Portfolio virtuel pour simuler le trading

    Gère:
    - Le cash disponible
    - Les positions (nombre d'actions détenues)
    - L'historique des trades
    - Les frais de transaction et slippage
    """

    def __init__(self, initial_capital: float, commission: float = 0.001, slippage: float = 0.0005):
        """
        Initialise le portfolio

        Args:
            initial_capital: Capital initial en euros
            commission: Commission par trade (défaut: 0.1%)
            slippage: Slippage moyen (défaut: 0.05%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.holdings = 0  # Nombre d'actions détenues
        self.commission = commission
        self.slippage = slippage
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = [initial_capital]
        self.dates: List[datetime] = []

        # Pour calcul de performance
        self.total_buy_cost = 0.0
        self.total_sell_revenue = 0.0

    def buy(self, date: datetime, ticker: str, price: float, quantity: Optional[int] = None) -> bool:
        """
        Achète des actions

        Args:
            date: Date de la transaction
            ticker: Symbole de l'action
            price: Prix d'achat
            quantity: Nombre d'actions (None = acheter le maximum possible)

        Returns:
            True si succès, False si cash insuffisant
        """
        # Appliquer le slippage (augmente le prix d'achat)
        actual_price = price * (1 + self.slippage)

        # Calculer la quantité si non spécifiée
        if quantity is None:
            # Acheter le maximum possible avec le cash disponible
            max_quantity = int(self.cash / (actual_price * (1 + self.commission)))
            quantity = max_quantity

        if quantity <= 0:
            return False

        # Calculer le coût total
        commission_amount = actual_price * quantity * self.commission
        total_cost = actual_price * quantity + commission_amount

        # Vérifier le cash disponible
        if total_cost > self.cash:
            return False

        # Exécuter la transaction
        self.cash -= total_cost
        self.holdings += quantity
        self.total_buy_cost += total_cost

        # Enregistrer le trade
        trade = Trade(
            date=date,
            type='BUY',
            ticker=ticker,
            price=actual_price,
            quantity=quantity,
            commission=commission_amount,
            slippage=actual_price - price,
            total=total_cost,
        )
        self.trades.append(trade)

        return True

    def sell(self, date: datetime, ticker: str, price: float, quantity: Optional[int] = None) -> bool:
        """
        Vend des actions

        Args:
            date: Date de la transaction
            ticker: Symbole de l'action
            price: Prix de vente
            quantity: Nombre d'actions (None = vendre toutes les actions)

        Returns:
            True si succès, False si pas assez d'actions
        """
        # Si quantité non spécifiée, vendre tout
        if quantity is None:
            quantity = self.holdings

        if quantity <= 0 or quantity > self.holdings:
            return False

        # Appliquer le slippage (diminue le prix de vente)
        actual_price = price * (1 - self.slippage)

        # Calculer le revenu
        commission_amount = actual_price * quantity * self.commission
        total_revenue = actual_price * quantity - commission_amount

        # Calculer le profit
        avg_buy_price = self.total_buy_cost / self.holdings if self.holdings > 0 else 0
        cost_basis = avg_buy_price * quantity
        profit = total_revenue - cost_basis
        return_pct = (profit / cost_basis * 100) if cost_basis > 0 else 0

        # Exécuter la transaction
        self.cash += total_revenue
        self.holdings -= quantity
        self.total_sell_revenue += total_revenue

        # Enregistrer le trade
        trade = Trade(
            date=date,
            type='SELL',
            ticker=ticker,
            price=actual_price,
            quantity=quantity,
            commission=commission_amount,
            slippage=price - actual_price,
            total=total_revenue,
            profit=profit,
            return_pct=return_pct,
        )
        self.trades.append(trade)

        return True

    def update_equity(self, date: datetime, current_price: float):
        """
        Met à jour la valeur du portfolio

        Args:
            date: Date courante
            current_price: Prix actuel de l'action
        """
        portfolio_value = self.cash + (self.holdings * current_price)
        self.equity_curve.append(portfolio_value)
        self.dates.append(date)

    def get_current_value(self, current_price: float) -> float:
        """
        Calcule la valeur actuelle du portfolio

        Args:
            current_price: Prix actuel de l'action

        Returns:
            Valeur totale du portfolio
        """
        return self.cash + (self.holdings * current_price)

    def get_holdings(self) -> int:
        """Retourne le nombre d'actions détenues"""
        return self.holdings

    def get_cash(self) -> float:
        """Retourne le cash disponible"""
        return self.cash

    def get_trades(self) -> List[Trade]:
        """Retourne l'historique des trades"""
        return self.trades

    def get_equity_curve(self) -> List[float]:
        """Retourne la courbe d'équité (évolution du capital)"""
        return self.equity_curve

    def get_dates(self) -> List[datetime]:
        """Retourne les dates correspondant à l'equity curve"""
        return self.dates
