"""
Base de données pour stocker le portefeuille de l'utilisateur
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path


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
        """Ajoute une position au portefeuille"""
        try:
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
                # Mise à jour avec moyenne pondérée
                old_qty, old_price = existing
                new_qty = old_qty + quantity
                new_avg_price = ((old_price * old_qty) + (price * quantity)) / new_qty

                cursor.execute("""
                    UPDATE portfolio
                    SET quantity = ?,
                        avg_price = ?,
                        current_value = ? * ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND ticker = ?
                """, (new_qty, new_avg_price, new_avg_price, new_qty, user_id, ticker))
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
            """, (user_id, ticker, company_name, quantity, price, quantity * price))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erreur add_position: {e}")
            return False

    def sell_position(
        self,
        ticker: str,
        quantity: float,
        price: float,
        user_id: str = "default_user"
    ) -> bool:
        """Vend (partiellement ou totalement) une position"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Récupérer la position actuelle
            cursor.execute("""
                SELECT id, quantity, company_name FROM portfolio WHERE user_id = ? AND ticker = ?
            """, (user_id, ticker))

            position = cursor.fetchone()

            if not position:
                print(f"Position {ticker} non trouvée pour user {user_id}")
                return False

            pos_id, current_qty, company_name = position

            if quantity > current_qty:
                print(f"Quantité à vendre ({quantity}) supérieure à la quantité détenue ({current_qty})")
                return False

            # Mise à jour de la position
            new_qty = current_qty - quantity

            if new_qty > 0:
                # Vente partielle
                cursor.execute("""
                    UPDATE portfolio
                    SET quantity = ?,
                        current_value = avg_price * ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_qty, new_qty, pos_id))
            else:
                # Vente totale - supprimer la position
                cursor.execute("DELETE FROM portfolio WHERE id = ?", (pos_id,))

            # Enregistrer la transaction
            cursor.execute("""
                INSERT INTO transactions
                (user_id, ticker, company_name, transaction_type, quantity, price, total_amount)
                VALUES (?, ?, ?, 'SELL', ?, ?, ?)
            """, (user_id, ticker, company_name, quantity, price, quantity * price))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erreur sell_position: {e}")
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
                    current_price = info.get('current_price', 0)
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
        """Résumé du portefeuille"""
        portfolio = self.get_portfolio(user_id)

        total_value = sum(p['current_value'] or 0 for p in portfolio)
        total_invested = sum(p['avg_price'] * p['quantity'] for p in portfolio)
        total_gain_loss = total_value - total_invested
        total_gain_loss_percent = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0

        # Calculer la répartition sectorielle (si disponible)
        sectors = {}
        for p in portfolio:
            # On pourrait enrichir avec Yahoo Finance ici
            sector = "Non classé"
            if sector not in sectors:
                sectors[sector] = 0
            sectors[sector] += p['current_value'] or 0

        return {
            "total_positions": len(portfolio),
            "total_value": total_value,
            "total_invested": total_invested,
            "total_gain_loss": total_gain_loss,
            "total_gain_loss_percent": total_gain_loss_percent,
            "sectors": sectors,
            "positions": portfolio
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
