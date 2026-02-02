"""
Bot Telegram pour envoyer des alertes
"""

import os
from typing import Optional
import requests


class TelegramBot:
    """Bot pour envoyer des notifications Telegram"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            print("⚠️ TELEGRAM_BOT_TOKEN non configuré - Alertes Telegram désactivées")
        if not self.chat_id:
            print("⚠️ TELEGRAM_CHAT_ID non configuré - Alertes Telegram désactivées")

    def is_configured(self) -> bool:
        """Vérifie si le bot est configuré"""
        return bool(self.bot_token and self.chat_id)

    def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Envoie un message sur Telegram

        Args:
            message: Texte du message (supporte Markdown)
            parse_mode: "Markdown" ou "HTML"

        Returns:
            True si envoyé avec succès
        """
        if not self.is_configured():
            print(f"⚠️ Bot Telegram non configuré. Message: {message[:100]}...")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            response = requests.post(url, data=data, timeout=10)

            if response.status_code == 200:
                print(f"✅ Message Telegram envoyé")
                return True
            else:
                print(f"❌ Erreur Telegram: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Erreur lors de l'envoi Telegram: {e}")
            return False

    def send_alert(
        self,
        ticker: str,
        company_name: str,
        alert_type: str,
        current_price: float,
        change_percent: float,
        message: Optional[str] = None
    ) -> bool:
        """
        Envoie une alerte formatée

        Args:
            ticker: Ticker de l'action
            company_name: Nom de l'entreprise
            alert_type: "PRICE_DROP", "PRICE_RISE", "BUY_OPPORTUNITY", etc.
            current_price: Prix actuel
            change_percent: Variation en %
            message: Message additionnel optionnel
        """
        # Emojis selon le type d'alerte
        emoji_map = {
            "PRICE_DROP": "🚨",
            "PRICE_RISE": "🚀",
            "BUY_OPPORTUNITY": "💎",
            "SELL_RECOMMENDATION": "⚠️",
            "NEWS": "📰",
            "TECHNICAL_SIGNAL": "📊"
        }

        emoji = emoji_map.get(alert_type, "🔔")

        # Construction du message
        alert_message = f"{emoji} *ALERTE - {company_name}* ({ticker})\n\n"

        if alert_type == "PRICE_DROP":
            alert_message += f"📉 *Baisse importante: {change_percent:+.2f}%*\n"
            alert_message += f"Prix actuel: {current_price:.2f} €\n\n"
            alert_message += "📊 Analyse: Vérifiez si opportunité d'achat ou stop-loss\n"

        elif alert_type == "PRICE_RISE":
            alert_message += f"📈 *Hausse importante: {change_percent:+.2f}%*\n"
            alert_message += f"Prix actuel: {current_price:.2f} €\n\n"
            alert_message += "💡 Conseil: Envisagez de prendre des bénéfices\n"

        elif alert_type == "BUY_OPPORTUNITY":
            alert_message += f"💎 *Opportunité d'achat détectée*\n"
            alert_message += f"Prix actuel: {current_price:.2f} €\n"
            alert_message += f"Variation: {change_percent:+.2f}%\n\n"
            alert_message += "✅ Analyse technique favorable\n"

        elif alert_type == "SELL_RECOMMENDATION":
            alert_message += f"⚠️ *Recommandation de vente*\n"
            alert_message += f"Prix actuel: {current_price:.2f} €\n"
            alert_message += f"Variation: {change_percent:+.2f}%\n\n"

        else:
            alert_message += f"Prix: {current_price:.2f} € ({change_percent:+.2f}%)\n\n"

        # Message additionnel
        if message:
            alert_message += f"\n{message}\n"

        return self.send_message(alert_message)

    def send_portfolio_summary(
        self,
        total_value: float,
        total_gain_loss: float,
        total_gain_loss_percent: float,
        num_positions: int
    ) -> bool:
        """Envoie un résumé du portefeuille"""
        emoji = "📈" if total_gain_loss >= 0 else "📉"

        message = f"{emoji} *RÉSUMÉ PORTEFEUILLE*\n\n"
        message += f"💰 Valeur totale: {total_value:,.2f} €\n"
        message += f"📊 Performance: {total_gain_loss:+,.2f} € ({total_gain_loss_percent:+.2f}%)\n"
        message += f"📍 Positions: {num_positions}\n"

        return self.send_message(message)

    def send_analysis_result(
        self,
        company_name: str,
        recommendation: str,
        target_price: Optional[float] = None,
        analysis_summary: Optional[str] = None
    ) -> bool:
        """Envoie le résultat d'une analyse"""
        emoji_map = {
            "ACHETER": "🟢",
            "ACHETER FORT": "💚",
            "RENFORCER": "🔵",
            "CONSERVER": "⚪",
            "ALLÉGER": "🟠",
            "VENDRE": "🔴"
        }

        emoji = emoji_map.get(recommendation, "🔔")

        message = f"{emoji} *ANALYSE - {company_name}*\n\n"
        message += f"📊 Recommandation: *{recommendation}*\n"

        if target_price:
            message += f"🎯 Prix cible: {target_price:.2f} €\n"

        if analysis_summary:
            message += f"\n{analysis_summary}\n"

        return self.send_message(message)
