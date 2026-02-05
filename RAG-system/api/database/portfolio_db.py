"""
Base de données pour stocker le portefeuille de l'utilisateur
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path
from decimal import Decimal
import sys
import os

# Import des validateurs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from validators import (
    validate_financial_amount,
    validate_stock_quantity,
    validate_stock_price,
    ValidationError
)


class PortfolioDatabase:
    """Gestion de la base de données du portefeuille"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Par défaut dans le dossier data/
            base_dir = Path(__file__).parent.parent.parent / "data"
            base_dir.mkdir(exist_ok=True)
            db_path = str(base_dir / "portfolio.db")

        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Crée les tables si elles n'existent pas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table du portefeuille actuel
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default_user',
                ticker TEXT NOT NULL,
                company_name TEXT,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                purchase_date DATE,
                current_price REAL,
                current_value REAL,
                gain_loss_percent REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, ticker)
            )
        """)

        # Table des transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default_user',
                ticker TEXT NOT NULL,
                company_name TEXT,
                transaction_type TEXT CHECK(transaction_type IN ('BUY', 'SELL')),
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total_amount REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)

        # Table des analyses historiques
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default_user',
                ticker TEXT NOT NULL,
                analysis_type TEXT,
                recommendation TEXT,
                target_price REAL,
                analysis_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table de trésorerie PEA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pea_treasury (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                total_deposits REAL NOT NULL DEFAULT 0,
                cash_available REAL NOT NULL DEFAULT 0,
                cash_invested REAL NOT NULL DEFAULT 0,
                pea_opening_date DATE,
                last_deposit_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK(total_deposits >= 0),
                CHECK(cash_available >= 0),
                CHECK(cash_invested >= 0)
            )
        """)

        # Table d'historique des dépôts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deposit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                deposit_date DATE NOT NULL,
                deposit_method TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK(amount > 0)
            )
        """)

        # Table des flux de trésorerie
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cash_flow_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                ticker TEXT,
                amount REAL NOT NULL,
                cash_before REAL NOT NULL,
                cash_after REAL NOT NULL,
                transaction_id INTEGER,
                event_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK(amount > 0),
                FOREIGN KEY (transaction_id) REFERENCES transactions(id)
            )
        """)

        # Table des opportunités d'investissement
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investment_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                company_name TEXT,
                recommendation_type TEXT,
                suggested_amount REAL,
                suggested_quantity INTEGER,
                target_price REAL,
                reasoning TEXT,
                confidence_score REAL,
                risk_level TEXT,
                cash_available_at_time REAL,
                portfolio_value_at_time REAL,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                actioned_at TIMESTAMP,
                CHECK(suggested_amount > 0),
                CHECK(confidence_score BETWEEN 0 AND 1)
            )
        """)

        conn.commit()
        conn.close()

    def add_position(
        self,
        ticker: str,
        company_name: str,
        quantity: float,
        price: float,
        purchase_date: Optional[str] = None,
        user_id: str = "default_user"
    ) -> bool:
        """
        Ajoute une position au portefeuille

        NOUVEAU: Déduit automatiquement le montant du cash disponible avec validation Decimal stricte
        """
        try:
            # VALIDATION DECIMAL STRICTE
            dec_quantity = validate_stock_quantity(quantity, field_name="Quantité")
            dec_price = validate_stock_price(price, field_name="Prix d'achat")
            dec_total_amount = dec_quantity * dec_price

            # Convertir en float pour SQLite (mais calculs déjà validés)
            quantity = float(dec_quantity)
            price = float(dec_price)
            total_amount = float(dec_total_amount)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if purchase_date is None:
                purchase_date = datetime.now().strftime("%Y-%m-%d")

            # Vérifier si la position existe déjà
            cursor.execute("""
                SELECT quantity, avg_price FROM portfolio WHERE user_id = ? AND ticker = ?
            """, (user_id, ticker))

            existing = cursor.fetchone()

            if existing:
                old_qty, old_price = existing
                new_qty = old_qty + quantity
                # Calcul PRU pur
                new_avg_price = ((old_price * old_qty) + (price * quantity)) / new_qty
                # Calculer la nouvelle valeur (on garde current_price si disponible, sinon on met le nouveau prix)
                new_current_value = price * new_qty  # Valeur basée sur le prix actuel

                cursor.execute("""
                    UPDATE portfolio
                    SET quantity = ?,
                        avg_price = ?,
                        current_price = ?,
                        current_value = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND ticker = ?
                """, (new_qty, new_avg_price, price, new_current_value, user_id, ticker))
            else:
                # Nouvelle position
                cursor.execute("""
                    INSERT INTO portfolio
                    (user_id, ticker, company_name, quantity, avg_price, purchase_date, current_price, current_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, ticker, company_name, quantity, price, purchase_date, price, quantity * price))

            # Enregistrer la transaction
            cursor.execute("""
                INSERT INTO transactions
                (user_id, ticker, company_name, transaction_type, quantity, price, total_amount)
                VALUES (?, ?, ?, 'BUY', ?, ?, ?)
            """, (user_id, ticker, company_name, quantity, price, total_amount))

            transaction_id = cursor.lastrowid

            # NOUVEAU: Déduire le cash et enregistrer le cash flow
            self._update_cash_on_buy(cursor, user_id, total_amount, transaction_id, ticker)

            # Recalculer cash_invested
            cursor.execute("""
                SELECT SUM(current_value) as invested FROM portfolio WHERE user_id = ?
            """, (user_id,))

            invested = cursor.fetchone()[0] or 0.0

            cursor.execute("""
                UPDATE pea_treasury
                SET cash_invested = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (invested, user_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erreur add_position: {e}")
            if 'conn' in locals():
                conn.close()
            return False

    def sell_position(
        self,
        ticker: str,
        quantity: float,
        price: float,
        user_id: str = "default_user"
    ) -> bool:
        """
        Vend (partiellement ou totalement) une position

        NOUVEAU: Ajoute automatiquement le montant au cash disponible avec validation Decimal stricte
        """
        try:
            # VALIDATION DECIMAL STRICTE
            dec_quantity = validate_stock_quantity(quantity, field_name="Quantité à vendre")
            dec_price = validate_stock_price(price, field_name="Prix de vente")
            dec_total_amount = dec_quantity * dec_price

            # Convertir en float pour SQLite (mais calculs déjà validés)
            quantity = float(dec_quantity)
            price = float(dec_price)
            total_amount = float(dec_total_amount)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Récupérer la position actuelle
            cursor.execute("""
                SELECT id, quantity, company_name, avg_price, current_price FROM portfolio WHERE user_id = ? AND ticker = ?
            """, (user_id, ticker))

            position = cursor.fetchone()

            if not position:
                print(f"Position {ticker} non trouvée pour user {user_id}")
                conn.close()
                return False

            pos_id, current_qty, company_name, avg_price, current_price = position

            if quantity > current_qty:
                print(f"Quantité à vendre ({quantity}) supérieure à la quantité détenue ({current_qty})")
                conn.close()
                return False

            # Mise à jour de la position
            new_qty = current_qty - quantity

            if new_qty > 0:
                # Vente partielle - calculer nouvelle valeur
                # Utiliser current_price si disponible, sinon avg_price
                price_for_value = current_price if current_price else avg_price
                new_current_value = price_for_value * new_qty

                cursor.execute("""
                    UPDATE portfolio
                    SET quantity = ?,
                        current_value = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_qty, new_current_value, pos_id))
            else:
                # Vente totale - supprimer la position
                cursor.execute("DELETE FROM portfolio WHERE id = ?", (pos_id,))

            # Enregistrer la transaction
            cursor.execute("""
                INSERT INTO transactions
                (user_id, ticker, company_name, transaction_type, quantity, price, total_amount)
                VALUES (?, ?, ?, 'SELL', ?, ?, ?)
            """, (user_id, ticker, company_name, quantity, price, total_amount))

            transaction_id = cursor.lastrowid

            # NOUVEAU: Ajouter le cash récupéré et enregistrer le cash flow
            self._update_cash_on_sell(cursor, user_id, total_amount, transaction_id, ticker)

            # Recalculer cash_invested
            cursor.execute("""
                SELECT SUM(current_value) as invested FROM portfolio WHERE user_id = ?
            """, (user_id,))

            invested = cursor.fetchone()[0] or 0.0

            cursor.execute("""
                UPDATE pea_treasury
                SET cash_invested = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (invested, user_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erreur sell_position: {e}")
            if 'conn' in locals():
                conn.close()
            return False

    def get_portfolio(self, user_id: str = "default_user") -> List[Dict]:
        """Récupère le portefeuille complet"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM portfolio WHERE user_id = ? ORDER BY current_value DESC
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_current_prices(self, user_id: str = "default_user"):
        """Met à jour les prix actuels avec Yahoo Finance"""
        try:
            from api.services.yahoo_finance_service import YahooFinanceService

            portfolio = self.get_portfolio(user_id)
            yf_service = YahooFinanceService()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for position in portfolio:
                ticker = position['ticker']
                info = yf_service.get_stock_info(ticker)

                if info:
                    current_price = info.get('currentPrice', 0)
                    
                    if current_price > 0:
                        current_value = current_price * position['quantity']
                        gain_loss = ((current_price - position['avg_price']) / position['avg_price']) * 100

                        cursor.execute("""
                            UPDATE portfolio
                            SET current_price = ?,
                                current_value = ?,
                                gain_loss_percent = ?,
                                last_updated = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (current_price, current_value, gain_loss, position['id']))

            conn.commit()
            conn.close()
        except ImportError:
            print("Yahoo Finance service non disponible - prix non mis à jour")
        except Exception as e:
            print(f"Erreur update_current_prices: {e}")

    def get_portfolio_summary(self, user_id: str = "default_user") -> Dict:
        """
        Résumé du portefeuille

        NOUVEAU: Inclut les informations de trésorerie PEA
        """
        portfolio = self.get_portfolio(user_id)
        treasury = self.get_treasury_status(user_id)

        total_value = sum(p['current_value'] or 0 for p in portfolio)
        total_invested = sum(p['avg_price'] * p['quantity'] for p in portfolio)
        total_gain_loss = total_value - total_invested
        total_gain_loss_percent = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0

        # Calculer la valeur totale du PEA
        pea_total_value = treasury['cash_available'] + total_value

        # Performance globale du PEA
        pea_gain_loss = pea_total_value - treasury['total_deposits']
        pea_gain_loss_percent = (
            (pea_gain_loss / treasury['total_deposits'] * 100)
            if treasury['total_deposits'] > 0 else 0
        )

        # Calculer la répartition sectorielle (si disponible)
        sectors = {}
        for p in portfolio:
            # On pourrait enrichir avec Yahoo Finance ici
            sector = "Non classé"
            if sector not in sectors:
                sectors[sector] = 0
            sectors[sector] += p['current_value'] or 0

        return {
            # Informations portfolio existantes
            "total_positions": len(portfolio),
            "total_value": total_value,
            "total_invested": total_invested,
            "total_gain_loss": total_gain_loss,
            "total_gain_loss_percent": total_gain_loss_percent,
            "sectors": sectors,
            "positions": portfolio,

            # NOUVELLES informations PEA
            "pea_treasury": {
                "total_deposits": treasury['total_deposits'],
                "cash_available": treasury['cash_available'],
                "cash_invested": treasury['cash_invested'],
                "pea_total_value": pea_total_value,
                "pea_gain_loss": pea_gain_loss,
                "pea_gain_loss_percent": pea_gain_loss_percent,
                "pea_opening_date": treasury.get('pea_opening_date'),
                "last_deposit_date": treasury.get('last_deposit_date'),
            },

            # Ratios utiles
            "cash_ratio": (treasury['cash_available'] / pea_total_value * 100) if pea_total_value > 0 else 0,
            "investment_ratio": (total_value / pea_total_value * 100) if pea_total_value > 0 else 0,
        }

    def save_analysis(
        self,
        ticker: str,
        analysis_type: str,
        recommendation: str,
        analysis_text: str,
        target_price: Optional[float] = None,
        user_id: str = "default_user"
    ) -> bool:
        """Sauvegarde une analyse pour historique"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO analysis_history
                (user_id, ticker, analysis_type, recommendation, target_price, analysis_text)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, ticker, analysis_type, recommendation, target_price, analysis_text))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erreur save_analysis: {e}")
            return False

    def get_analysis_history(
        self,
        ticker: Optional[str] = None,
        user_id: str = "default_user",
        limit: int = 10
    ) -> List[Dict]:
        """Récupère l'historique des analyses"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if ticker:
            cursor.execute("""
                SELECT * FROM analysis_history
                WHERE user_id = ? AND ticker = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, ticker, limit))
        else:
            cursor.execute("""
                SELECT * FROM analysis_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_transactions(
        self,
        ticker: Optional[str] = None,
        user_id: str = "default_user",
        limit: int = 50
    ) -> List[Dict]:
        """Récupère l'historique des transactions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if ticker:
            cursor.execute("""
                SELECT * FROM transactions
                WHERE user_id = ? AND ticker = ?
                ORDER BY date DESC
                LIMIT ?
            """, (user_id, ticker, limit))
        else:
            cursor.execute("""
                SELECT * FROM transactions
                WHERE user_id = ?
                ORDER BY date DESC
                LIMIT ?
            """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ==========================================
    # NOUVELLES MÉTHODES - TRÉSORERIE PEA
    # ==========================================

    def deposit_cash(
        self,
        amount: float,
        user_id: str = "default_user",
        deposit_method: str = "ONE_TIME",
        notes: Optional[str] = None
    ) -> bool:
        """
        Dépose de l'argent sur le PEA avec validation Decimal stricte et UPDATE atomique

        Args:
            amount: Montant à déposer (euros)
            user_id: Identifiant utilisateur
            deposit_method: Type de dépôt ('INITIAL', 'RECURRING', 'ONE_TIME')
            notes: Notes optionnelles

        Returns:
            True si succès, False sinon

        Raises:
            ValidationError: Si le montant est invalide
        """
        try:
            # VALIDATION DECIMAL STRICTE
            dec_amount = validate_financial_amount(
                amount,
                min_value=0.01,
                max_value=150_000.0,  # Plafond PEA
                field_name="Montant du dépôt"
            )
            amount = float(dec_amount)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Vérifier si l'utilisateur existe dans pea_treasury
            cursor.execute("""
                SELECT cash_available, total_deposits FROM pea_treasury WHERE user_id = ?
            """, (user_id,))

            result = cursor.fetchone()

            if result:
                # ATOMIC UPDATE (pas de race condition)
                cash_before = result[0]

                cursor.execute("""
                    UPDATE pea_treasury
                    SET cash_available = cash_available + ?,
                        total_deposits = total_deposits + ?,
                        last_deposit_date = DATE('now'),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (amount, amount, user_id))

                # Vérifier que l'UPDATE a réussi
                if cursor.rowcount == 0:
                    raise ValueError("Échec de la mise à jour atomique du dépôt")
            else:
                # Création initiale (pas de race condition car INSERT unique par user_id)
                cursor.execute("""
                    INSERT INTO pea_treasury
                    (user_id, cash_available, total_deposits, pea_opening_date, last_deposit_date)
                    VALUES (?, ?, ?, DATE('now'), DATE('now'))
                """, (user_id, amount, amount))

                cash_before = 0.0

            # Enregistrer dans deposit_history
            cursor.execute("""
                INSERT INTO deposit_history (user_id, amount, deposit_date, deposit_method, notes)
                VALUES (?, ?, DATE('now'), ?, ?)
            """, (user_id, amount, deposit_method, notes))

            # Enregistrer le cash flow event
            cursor.execute("""
                INSERT INTO cash_flow_events (user_id, event_type, amount, cash_before, cash_after)
                VALUES (?, 'DEPOSIT', ?, ?, ?)
            """, (user_id, amount, cash_before, cash_before + amount))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Erreur deposit_cash: {e}")
            return False

    def get_treasury_status(self, user_id: str = "default_user") -> Dict:
        """
        Récupère l'état complet de la trésorerie PEA

        Returns:
            Dict avec toutes les informations de trésorerie
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Récupérer l'état de trésorerie
        cursor.execute("""
            SELECT * FROM pea_treasury WHERE user_id = ?
        """, (user_id,))

        treasury = cursor.fetchone()

        if not treasury:
            # Initialiser si n'existe pas
            conn.close()
            return {
                "exists": False,
                "total_deposits": 0,
                "cash_available": 0,
                "cash_invested": 0,
                "pea_opening_date": None,
                "last_deposit_date": None
            }

        # Recalculer cash_invested depuis le portfolio actuel (source of truth)
        cursor.execute("""
            SELECT SUM(current_value) as invested
            FROM portfolio WHERE user_id = ?
        """, (user_id,))

        invested_result = cursor.fetchone()
        actual_cash_invested = invested_result['invested'] or 0.0

        # Mettre à jour si nécessaire
        if abs(actual_cash_invested - treasury['cash_invested']) > 0.01:
            cursor.execute("""
                UPDATE pea_treasury
                SET cash_invested = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (actual_cash_invested, user_id))
            conn.commit()

        result = dict(treasury)
        result['exists'] = True
        result['cash_invested'] = actual_cash_invested

        conn.close()
        return result

    def get_deposit_history(
        self,
        user_id: str = "default_user",
        limit: int = 50
    ) -> List[Dict]:
        """
        Récupère l'historique des dépôts

        Returns:
            Liste des dépôts effectués
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM deposit_history
            WHERE user_id = ?
            ORDER BY deposit_date DESC
            LIMIT ?
        """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_cash_flow_events(
        self,
        user_id: str = "default_user",
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Récupère l'historique des flux de trésorerie

        Args:
            event_type: Filter par type ('DEPOSIT', 'BUY', 'SELL') ou None pour tous

        Returns:
            Liste des événements de cash flow
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if event_type:
            cursor.execute("""
                SELECT * FROM cash_flow_events
                WHERE user_id = ? AND event_type = ?
                ORDER BY event_date DESC
                LIMIT ?
            """, (user_id, event_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM cash_flow_events
                WHERE user_id = ?
                ORDER BY event_date DESC
                LIMIT ?
            """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _update_cash_on_buy(
        self,
        cursor,
        user_id: str,
        amount: float,
        transaction_id: int,
        ticker: str
    ):
        """
        Met à jour le cash disponible lors d'un achat avec ATOMIC UPDATE (thread-safe)

        Cette méthode est appelée par add_position

        IMPORTANT: Utilise un UPDATE atomique pour éviter les race conditions
        entre les 3 containers (api, bot, scheduler) qui accèdent à SQLite.

        Raises:
            ValueError: Si trésorerie inexistante ou solde insuffisant
        """
        # Récupérer le cash actuel AVANT l'update (pour cash_flow_events)
        cursor.execute("""
            SELECT cash_available FROM pea_treasury WHERE user_id = ?
        """, (user_id,))

        result = cursor.fetchone()

        if not result:
            raise ValueError(
                f"Aucune trésorerie PEA trouvée pour {user_id}. "
                f"Effectuez un dépôt d'abord avec /portfolio/deposit"
            )

        cash_before = result[0]

        # ATOMIC UPDATE avec vérification du solde dans la clause WHERE
        # Si available_cash < amount, la WHERE clause échouera et rowcount = 0
        cursor.execute("""
            UPDATE pea_treasury
            SET cash_available = cash_available - ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
              AND cash_available >= ?
        """, (amount, user_id, amount))

        # Vérifier que l'UPDATE a réussi (rowcount = 1)
        if cursor.rowcount == 0:
            # Re-vérifier le cash disponible pour un message d'erreur précis
            cursor.execute("""
                SELECT cash_available FROM pea_treasury WHERE user_id = ?
            """, (user_id,))
            current_cash = cursor.fetchone()
            if current_cash:
                raise ValueError(
                    f"Cash insuffisant. Disponible: {current_cash[0]:.2f}€, Requis: {amount:.2f}€"
                )
            else:
                raise ValueError(f"Trésorerie introuvable pour {user_id}")

        # Calculer le nouveau solde pour cash_flow_events
        new_cash = cash_before - amount

        # Enregistrer le cash flow event
        cursor.execute("""
            INSERT INTO cash_flow_events
            (user_id, event_type, ticker, amount, cash_before, cash_after, transaction_id)
            VALUES (?, 'BUY', ?, ?, ?, ?, ?)
        """, (user_id, ticker, amount, cash_before, new_cash, transaction_id))

    def _update_cash_on_sell(
        self,
        cursor,
        user_id: str,
        amount: float,
        transaction_id: int,
        ticker: str
    ):
        """
        Met à jour le cash disponible lors d'une vente avec ATOMIC UPDATE (thread-safe)

        Cette méthode est appelée par sell_position

        IMPORTANT: Utilise un UPDATE atomique pour éviter les race conditions
        entre les 3 containers (api, bot, scheduler) qui accèdent à SQLite.

        Raises:
            ValueError: Si trésorerie inexistante
        """
        # Récupérer le cash actuel AVANT l'update (pour cash_flow_events)
        cursor.execute("""
            SELECT cash_available FROM pea_treasury WHERE user_id = ?
        """, (user_id,))

        result = cursor.fetchone()

        if not result:
            raise ValueError(f"Aucune trésorerie PEA trouvée pour {user_id}")

        cash_before = result[0]

        # ATOMIC UPDATE pour ajouter le cash récupéré
        cursor.execute("""
            UPDATE pea_treasury
            SET cash_available = cash_available + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (amount, user_id))

        # Vérifier que l'UPDATE a réussi
        if cursor.rowcount == 0:
            raise ValueError(f"Échec de la mise à jour atomique pour {user_id}")

        # Calculer le nouveau solde pour cash_flow_events
        new_cash = cash_before + amount

        # Enregistrer le cash flow event
        cursor.execute("""
            INSERT INTO cash_flow_events
            (user_id, event_type, ticker, amount, cash_before, cash_after, transaction_id)
            VALUES (?, 'SELL', ?, ?, ?, ?, ?)
        """, (user_id, ticker, amount, cash_before, new_cash, transaction_id))
