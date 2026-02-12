"""
Handlers de commandes Telegram pour Agent PEA
Contient tous les handlers pour interagir avec l'API du portfolio
"""

import requests
import os
import logging
from functools import wraps
from typing import Optional, Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration logging
logger = logging.getLogger(__name__)

# Configuration API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# ==========================================
# SÉCURITÉ - Whitelist Protection
# ==========================================

def get_authorized_user_ids() -> set:
    """
    Récupère la liste des IDs Telegram autorisés depuis l'environnement.

    Returns:
        set: Ensemble des IDs autorisés (vide si non configuré)
    """
    ids_str = os.getenv("TELEGRAM_AUTHORIZED_USER_IDS", "")
    if not ids_str:
        logger.warning("⚠️ TELEGRAM_AUTHORIZED_USER_IDS not set - bot accessible to all!")
        return set()

    try:
        return {int(uid.strip()) for uid in ids_str.split(",") if uid.strip()}
    except ValueError as e:
        logger.error(f"Invalid TELEGRAM_AUTHORIZED_USER_IDS format: {e}")
        return set()


def authorized_only(func):
    """
    Decorator qui vérifie que l'utilisateur est autorisé à utiliser le bot.

    SÉCURITÉ DÉSACTIVÉE - Usage personnel uniquement
    Autorise tous les utilisateurs sans vérification

    Usage:
        @authorized_only
        async def my_command(update, context):
            # commande protégée
    """
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        # SÉCURITÉ DÉSACTIVÉE - Exécuter directement la commande
        return await func(update, context, *args, **kwargs)

    return wrapper


# ==========================================
# UTILITAIRES
# ==========================================

def format_currency(amount: float) -> str:
    """Formate un montant en euros"""
    return f"{amount:,.2f} €".replace(',', ' ')


def format_percent(percent: float) -> str:
    """Formate un pourcentage avec emoji"""
    emoji = "📈" if percent >= 0 else "📉"
    return f"{emoji} {percent:+.2f}%"


def handle_api_error(response: requests.Response) -> str:
    """Gère les erreurs API et retourne un message approprié"""
    try:
        error_data = response.json()
        return f"❌ Erreur API ({response.status_code}): {error_data.get('detail', 'Erreur inconnue')}"
    except:
        return f"❌ Erreur API ({response.status_code}): {response.text[:200]}"


def get_user_id(update: Update) -> str:
    """Récupère l'ID utilisateur Telegram"""
    return str(update.effective_user.id)


# ==========================================
# TRÉSORERIE PEA
# ==========================================

@authorized_only
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /balance - Affiche la trésorerie PEA"""
    user_id = get_user_id(update)

    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/treasury",
            params={"user_id": user_id}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()

        # Récupérer aussi le portfolio pour les ratios
        portfolio_response = requests.get(
            f"{API_BASE_URL}/portfolio",
            params={"user_id": user_id}
        )
        portfolio = portfolio_response.json()

        pea_total = data.get('pea_total_value', 0)
        cash_available = data.get('cash_available', 0)
        cash_invested = data.get('cash_invested', 0)
        total_deposits = data.get('total_deposits', 0)
        pea_gain_loss = data.get('pea_gain_loss', 0)
        pea_gain_percent = data.get('pea_gain_loss_percent', 0)

        cash_ratio = portfolio.get('cash_ratio', 0)
        investment_ratio = portfolio.get('investment_ratio', 0)

        message = f"""
💰 *TRÉSORERIE PEA*

🏦 *Valeur totale PEA:* {format_currency(pea_total)}
📊 *Performance globale:* {format_percent(pea_gain_percent)}
   └─ Plus-value: {format_currency(pea_gain_loss)}

💵 *Répartition:*
   • Cash disponible: {format_currency(cash_available)} ({cash_ratio:.1f}%)
   • Cash investi: {format_currency(cash_invested)} ({investment_ratio:.1f}%)

📥 *Historique:*
   • Total déposé: {format_currency(total_deposits)}
   • Date ouverture: {data.get('pea_opening_date', 'N/A')}
   • Dernier dépôt: {data.get('last_deposit_date', 'N/A')}
"""

        # Ajouter des suggestions si beaucoup de cash
        if cash_ratio > 30 and cash_available > 100:
            message += f"\n💡 *Suggestion:* Vous avez {cash_ratio:.0f}% en cash. Tapez /opportunities pour investir."

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /deposit <amount> - Dépose de l'argent sur le PEA"""
    user_id = get_user_id(update)

    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /deposit <montant>\n\n"
            "Exemples:\n"
            "• /deposit 1000\n"
            "• /deposit 5000"
        )
        return

    try:
        amount = float(context.args[0].replace(',', '.'))

        if amount <= 0:
            await update.message.reply_text("❌ Le montant doit être positif.")
            return

        # Note optionnelle
        notes = " ".join(context.args[1:]) if len(context.args) > 1 else None

        response = requests.post(
            f"{API_BASE_URL}/portfolio/deposit",
            params={
                "amount": amount,
                "user_id": user_id,
                "notes": notes
            }
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()

        message = f"""
✅ *Dépôt enregistré !*

💵 Montant déposé: {format_currency(amount)}
💰 Nouveau cash disponible: {format_currency(data['new_cash_available'])}
📊 Total déposé sur le PEA: {format_currency(data['total_deposits'])}
"""

        if notes:
            message += f"\n📝 Note: {notes}"

        message += "\n\n💡 Tapez /opportunities pour investir ce cash."

        await update.message.reply_text(message, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text("❌ Montant invalide. Utilisez un nombre (ex: 1000)")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /history - Historique des dépôts"""
    user_id = get_user_id(update)

    limit = 10
    if context.args and len(context.args) > 0:
        try:
            limit = int(context.args[0])
        except:
            pass

    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/treasury/deposits",
            params={"user_id": user_id, "limit": limit}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()
        deposits = data.get('deposits', [])

        if not deposits:
            await update.message.reply_text("📭 Aucun dépôt enregistré.")
            return

        message = f"📜 *HISTORIQUE DES DÉPÔTS* (derniers {limit})\n\n"

        total = 0
        for deposit in deposits:
            amount = deposit['amount']
            date = deposit['deposit_date']
            notes = deposit.get('notes', '')
            total += amount

            message += f"💵 {format_currency(amount)}\n"
            message += f"   └─ {date[:10]}"
            if notes:
                message += f" • {notes}"
            message += "\n\n"

        message += f"📊 *Total:* {format_currency(total)}"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def cashflow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /cashflow - Flux de trésorerie (dépôts, achats, ventes)"""
    user_id = get_user_id(update)

    # Paramètres optionnels
    event_type = None
    limit = 20

    if context.args and len(context.args) > 0:
        arg = context.args[0].upper()
        if arg in ['DEPOSIT', 'BUY', 'SELL']:
            event_type = arg
        else:
            try:
                limit = int(arg)
            except:
                pass

    try:
        params = {"user_id": user_id, "limit": limit}
        if event_type:
            params["event_type"] = event_type

        response = requests.get(
            f"{API_BASE_URL}/portfolio/treasury/cashflow",
            params=params
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()
        events = data.get('events', [])

        if not events:
            await update.message.reply_text("📭 Aucun événement trouvé.")
            return

        filter_text = f" ({event_type})" if event_type else ""
        message = f"💸 *FLUX DE TRÉSORERIE{filter_text}*\n\n"

        for event in events[:limit]:
            type_icon = {
                'DEPOSIT': '📥',
                'BUY': '🛒',
                'SELL': '💰'
            }.get(event['event_type'], '❓')

            message += f"{type_icon} *{event['event_type']}*\n"
            message += f"   Montant: {format_currency(abs(event['amount']))}\n"
            message += f"   Cash après: {format_currency(event['cash_after'])}\n"

            if event.get('details'):
                message += f"   {event['details']}\n"

            message += f"   📅 {event['event_date'][:16]}\n\n"

        message += f"\n💡 Filtrer: /cashflow DEPOSIT|BUY|SELL"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


# ==========================================
# PORTFOLIO
# ==========================================

@authorized_only
async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /portfolio - Vue complète du portfolio"""
    user_id = get_user_id(update)

    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio",
            params={"user_id": user_id}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()
        positions = data.get('positions', [])
        treasury = data.get('pea_treasury', {})

        if not positions:
            await update.message.reply_text(
                "📭 Votre portefeuille est vide.\n\n"
                "💡 Utilisez /buy pour acheter des actions ou /opportunities pour des suggestions."
            )
            return

        total_value = data['total_value']
        total_gain = data['total_gain_loss']
        total_gain_percent = data['total_gain_loss_percent']
        pea_total = treasury.get('pea_total_value', 0)
        cash_available = treasury.get('cash_available', 0)

        message = f"""
📊 *PORTFOLIO PEA*

💼 *Valeur totale:* {format_currency(pea_total)}
   └─ Positions: {format_currency(total_value)}
   └─ Cash: {format_currency(cash_available)}

📈 *Performance:* {format_percent(total_gain_percent)}
   └─ Plus-value: {format_currency(total_gain)}

🏢 *Positions ({len(positions)}):*
"""

        # Trier par valeur décroissante
        positions_sorted = sorted(positions, key=lambda x: x.get('current_value', 0) or 0, reverse=True)

        for pos in positions_sorted:
            ticker = pos['ticker']
            company = pos['company_name']
            qty = pos['quantity']
            avg_price = pos['avg_price'] or 0
            current_price = pos['current_price'] or 0
            current_value = pos['current_value'] or 0
            gain_percent = pos['gain_loss_percent'] or 0
            weight = (current_value / total_value * 100) if total_value > 0 else 0

            perf_icon = "🟢" if gain_percent >= 0 else "🔴"

            message += f"\n{perf_icon} *{ticker}* - {company}\n"
            message += f"   {qty} actions • PRU: {avg_price:.2f}€ → {current_price:.2f}€\n"
            message += f"   Valeur: {format_currency(current_value)} ({weight:.1f}%)\n"
            message += f"   Perf: {format_percent(gain_percent)}\n"

        # Ajouter boutons d'action
        keyboard = [
            [InlineKeyboardButton("💰 Trésorerie", callback_data='show_treasury')],
            [InlineKeyboardButton("💡 Opportunités", callback_data='show_opportunities')],
            [InlineKeyboardButton("🏥 Santé", callback_data='show_health')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /positions - Liste simplifiée des positions"""
    user_id = get_user_id(update)

    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio",
            params={"user_id": user_id}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()
        positions = data.get('positions', [])

        if not positions:
            await update.message.reply_text("📭 Aucune position.")
            return

        message = "📋 *POSITIONS*\n\n"

        for pos in sorted(positions, key=lambda x: x.get('current_value', 0) or 0, reverse=True):
            gain_percent = pos.get('gain_loss_percent', 0) or 0
            icon = "🟢" if gain_percent >= 0 else "🔴"

            message += f"{icon} *{pos['ticker']}*: {pos['quantity']} actions "
            message += f"({format_percent(gain_percent)})\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /health - Analyse la santé du portfolio"""
    user_id = get_user_id(update)

    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/health",
            params={"user_id": user_id}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()

        score = data['score']
        grade = data['grade']
        issues = data.get('issues', [])
        recommendations = data.get('recommendations', [])

        # Emoji selon le score
        if score >= 80:
            score_emoji = "🏆"
        elif score >= 60:
            score_emoji = "✅"
        elif score >= 40:
            score_emoji = "⚠️"
        else:
            score_emoji = "🚨"

        message = f"""
{score_emoji} *SANTÉ DU PORTFOLIO*

📊 *Score:* {score}/100
🎯 *Grade:* {grade}

💼 *Statistiques:*
   • Positions: {data['total_positions']}
   • Valeur: {format_currency(data['total_value'])}
   • Performance: {format_percent(data['performance'])}

"""

        if issues and issues[0] != "Aucun problème majeur détecté":
            message += "⚠️ *Points d'attention:*\n"
            for issue in issues:
                message += f"   • {issue}\n"
            message += "\n"
        else:
            message += "✅ *Aucun problème majeur détecté*\n\n"

        if recommendations:
            message += "💡 *Recommandations:*\n"
            for rec in recommendations:
                message += f"   {rec}\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def rebalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /rebalance - Vérifie si rééquilibrage nécessaire"""
    user_id = get_user_id(update)

    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/rebalance",
            params={"user_id": user_id}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()

        needs_rebalance = data['needs_rebalance']
        recommendations = data.get('recommendations', [])

        if not needs_rebalance:
            message = """
✅ *RÉÉQUILIBRAGE NON NÉCESSAIRE*

Votre portefeuille est bien équilibré.
Continuez le suivi régulier !
"""
        else:
            message = f"""
⚖️ *RÉÉQUILIBRAGE RECOMMANDÉ*

📊 *Portfolio:*
   • {data['portfolio_size']} positions
   • Valeur: {format_currency(data['total_value'])}

🎯 *Actions recommandées:*

"""

            for rec in recommendations:
                urgency_icon = {
                    'HIGH': '🚨',
                    'MEDIUM': '⚠️',
                    'LOW': '💡'
                }.get(rec.get('urgency', 'LOW'), '💡')

                action = rec['action']

                if action == 'DIVERSIFY':
                    message += f"{urgency_icon} *{action}*\n"
                    message += f"   {rec['reason']}\n\n"
                else:
                    ticker = rec.get('ticker', '')
                    company = rec.get('company', '')
                    current_weight = rec.get('current_weight', 0)
                    target_weight = rec.get('target_weight', 0)

                    message += f"{urgency_icon} *{action}* {ticker} - {company}\n"
                    message += f"   Poids: {current_weight:.1f}% → {target_weight:.1f}%\n"
                    message += f"   {rec['reason']}\n\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


# ==========================================
# OPPORTUNITÉS
# ==========================================

@authorized_only
async def opportunities_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /opportunities - Analyse les opportunités d'investissement"""
    user_id = get_user_id(update)

    await update.message.reply_text("🔍 Analyse en cours...")

    try:
        response = requests.post(
            f"{API_BASE_URL}/portfolio/opportunities/analyze",
            params={"user_id": user_id}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()

        if not data['has_opportunities']:
            message = f"""
💰 *OPPORTUNITÉS D'INVESTISSEMENT*

{data.get('reason', 'Aucune opportunité détectée pour le moment.')}

Cash disponible: {format_currency(data['cash_available'])}
"""
            await update.message.reply_text(message, parse_mode='Markdown')
            return

        opportunities = data['opportunities']

        message = f"""
💡 *OPPORTUNITÉS DÉTECTÉES*

💰 Cash disponible: {format_currency(data['cash_available'])}
📊 Portfolio: {data['portfolio_size']} positions
💼 Valeur totale: {format_currency(data['total_value'])}

🎯 *Recommandations:*

"""

        for i, opp in enumerate(opportunities, 1):
            priority_icon = {
                'HIGH': '🚨',
                'MEDIUM': '⚠️',
                'LOW': '💡'
            }.get(opp['priority'], '💡')

            message += f"{priority_icon} *Opportunité {i}* - {opp['type']}\n"
            message += f"   {opp['description']}\n"
            message += f"   💵 Montant suggéré: {format_currency(opp['suggested_amount'])}\n"

            if opp.get('ticker'):
                message += f"   📊 Ticker: {opp['ticker']}\n"
                if opp.get('suggested_quantity'):
                    message += f"   🔢 Quantité: {opp['suggested_quantity']} actions\n"

            message += f"\n   💭 {opp['reasoning']}\n\n"

        message += "\n💡 Utilisez /pending pour voir toutes vos opportunités sauvegardées."

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /pending - Opportunités en attente de décision"""
    user_id = get_user_id(update)

    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/opportunities/pending",
            params={"user_id": user_id, "include_expired": False}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()
        opportunities = data.get('opportunities', [])

        if not opportunities:
            await update.message.reply_text(
                "📭 Aucune opportunité en attente.\n\n"
                "💡 Utilisez /opportunities pour en détecter."
            )
            return

        message = f"📋 *OPPORTUNITÉS EN ATTENTE* ({len(opportunities)})\n\n"

        for opp in opportunities:
            opp_id = opp['id']
            ticker = opp['ticker']
            company = opp['company_name']
            amount = opp['suggested_amount']
            qty = opp.get('suggested_quantity', 0)
            confidence = opp.get('confidence_score', 0) * 100
            risk = opp.get('risk_level', 'MEDIUM')

            risk_icon = {
                'LOW': '🟢',
                'MEDIUM': '🟡',
                'HIGH': '🔴'
            }.get(risk, '🟡')

            message += f"{risk_icon} *#{opp_id}* - {ticker} ({company})\n"
            message += f"   💵 {format_currency(amount)}"
            if qty:
                message += f" • {qty} actions\n"
            else:
                message += "\n"
            message += f"   🎯 Confiance: {confidence:.0f}%\n"
            message += f"   📅 Expire: {opp.get('expires_at', 'N/A')[:10]}\n"
            message += f"   /accept {opp_id} | /reject {opp_id}\n\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def accept_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /accept <id> - Accepte une opportunité"""
    user_id = get_user_id(update)

    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /accept <id>\n\n"
            "Exemple: /accept 123\n\n"
            "💡 Utilisez /pending pour voir les opportunités."
        )
        return

    try:
        opp_id = int(context.args[0])

        await update.message.reply_text("⏳ Exécution en cours...")

        response = requests.post(
            f"{API_BASE_URL}/portfolio/opportunities/{opp_id}/accept",
            params={"user_id": user_id}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()

        if not data['success']:
            await update.message.reply_text(f"❌ {data.get('error', 'Erreur inconnue')}")
            return

        message = f"""
✅ *OPPORTUNITÉ ACCEPTÉE !*

🛒 Transaction exécutée:
   • {data['company_name']} ({data['ticker']})
   • {data['quantity']} actions à {data['price']:.2f}€
   • Montant total: {format_currency(data['total_amount'])}

💡 Utilisez /portfolio pour voir votre nouvelle position.
"""

        await update.message.reply_text(message, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text("❌ ID invalide. Utilisez un nombre (ex: /accept 123)")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /reject <id> [raison] - Rejette une opportunité"""
    user_id = get_user_id(update)

    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /reject <id> [raison]\n\n"
            "Exemples:\n"
            "• /reject 123\n"
            "• /reject 123 Trop risqué"
        )
        return

    try:
        opp_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else None

        params = {"user_id": user_id}
        if reason:
            params["reason"] = reason

        response = requests.post(
            f"{API_BASE_URL}/portfolio/opportunities/{opp_id}/reject",
            params=params
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()

        if data['success']:
            message = "✅ Opportunité rejetée."
            if reason:
                message += f"\n📝 Raison: {reason}"
        else:
            message = "❌ Opportunité introuvable."

        await update.message.reply_text(message)

    except ValueError:
        await update.message.reply_text("❌ ID invalide. Utilisez un nombre (ex: /reject 123)")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


# ==========================================
# TRANSACTIONS
# ==========================================

@authorized_only
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /buy <ticker> <qty> <price> - Achète des actions"""
    user_id = get_user_id(update)

    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "❌ Usage: /buy <ticker> <quantité> <prix>\n\n"
            "Exemples:\n"
            "• /buy MC.PA 5 750.50\n"
            "• /buy OR.PA 10 420"
        )
        return

    try:
        ticker = context.args[0].upper()
        quantity = float(context.args[1])
        price = float(context.args[2].replace(',', '.'))

        if quantity <= 0 or price <= 0:
            await update.message.reply_text("❌ La quantité et le prix doivent être positifs.")
            return

        # Estimer le nom de l'entreprise depuis le ticker
        company_name = ticker.split('.')[0]

        await update.message.reply_text("🛒 Achat en cours...")

        response = requests.post(
            f"{API_BASE_URL}/portfolio/add",
            json={
                "ticker": ticker,
                "company_name": company_name,
                "quantity": int(quantity),
                "price": price,
                "user_id": user_id
            }
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        total = quantity * price

        message = f"""
✅ *ACHAT ENREGISTRÉ*

🛒 Transaction:
   • {ticker} ({company_name})
   • {int(quantity)} actions à {price:.2f}€
   • Montant total: {format_currency(total)}

💡 Utilisez /portfolio pour voir votre position mise à jour.
"""

        await update.message.reply_text(message, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text("❌ Paramètres invalides. Format: /buy TICKER QTY PRICE")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /sell <ticker> <qty> <price> - Vend des actions"""
    user_id = get_user_id(update)

    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "❌ Usage: /sell <ticker> <quantité> <prix>\n\n"
            "Exemples:\n"
            "• /sell MC.PA 2 800\n"
            "• /sell OR.PA 5 450.75"
        )
        return

    try:
        ticker = context.args[0].upper()
        quantity = float(context.args[1])
        price = float(context.args[2].replace(',', '.'))

        if quantity <= 0 or price <= 0:
            await update.message.reply_text("❌ La quantité et le prix doivent être positifs.")
            return

        await update.message.reply_text("💰 Vente en cours...")

        response = requests.post(
            f"{API_BASE_URL}/portfolio/sell",
            json={
                "ticker": ticker,
                "quantity": int(quantity),
                "price": price,
                "user_id": user_id
            }
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        total = quantity * price

        message = f"""
✅ *VENTE ENREGISTRÉE*

💰 Transaction:
   • {ticker}
   • {int(quantity)} actions à {price:.2f}€
   • Montant encaissé: {format_currency(total)}

💵 Le cash est maintenant disponible sur votre PEA.
💡 Utilisez /balance pour voir votre trésorerie.
"""

        await update.message.reply_text(message, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text("❌ Paramètres invalides. Format: /sell TICKER QTY PRICE")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


# ==========================================
# ANALYSES
# ==========================================

@authorized_only
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /analyze <ticker> - Analyse complète avec l'IA"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /analyze <ticker> <company_name>\n\n"
            "Exemples:\n"
            "• /analyze MC.PA LVMH\n"
            "• /analyze OR.PA L'Oreal"
        )
        return

    ticker = context.args[0].upper()
    company_name = " ".join(context.args[1:]) if len(context.args) > 1 else ticker.split('.')[0]

    await update.message.reply_text("🤖 Analyse IA en cours... (cela peut prendre 30-60 secondes)")

    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/complete/{ticker}",
            params={"company_name": company_name},
            timeout=120
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()
        market = data.get('market_data', {})
        sentiment = data.get('news_sentiment', {})
        technical = data.get('technical_analysis', {})

        # Partie 1: Market Data
        current_price = market.get('currentPrice', 0)
        market_cap = market.get('marketCap', 0) / 1_000_000_000  # En milliards
        pe_ratio = market.get('trailingPE', 0)
        dividend = market.get('dividendYield', 0) * 100 if market.get('dividendYield') else 0

        message = f"""
📊 *ANALYSE COMPLÈTE* - {ticker}
🏢 {company_name}

💰 *Données de marché:*
   • Prix actuel: {current_price:.2f}€
   • Cap. boursière: {market_cap:.1f}B€
   • PER: {pe_ratio:.1f}
   • Dividende: {dividend:.2f}%

"""

        # Partie 2: Sentiment
        if sentiment:
            sentiment_score = sentiment.get('overall_sentiment', {}).get('score', 0)
            sentiment_label = sentiment.get('overall_sentiment', {}).get('label', 'NEUTRE')
            news_count = sentiment.get('total_articles', 0)

            sentiment_icon = {
                'POSITIF': '📈',
                'NÉGATIF': '📉',
                'NEUTRE': '➡️'
            }.get(sentiment_label, '➡️')

            message += f"""
📰 *Sentiment des news ({news_count} articles):*
   {sentiment_icon} *{sentiment_label}* (score: {sentiment_score:.2f})

"""

        # Partie 3: Analyse technique
        if technical:
            trend = technical.get('trend', 'UNKNOWN')
            signals = technical.get('signals', {})

            trend_icon = {
                'BULLISH': '🐂',
                'BEARISH': '🐻',
                'SIDEWAYS': '➡️'
            }.get(trend, '➡️')

            message += f"""
📈 *Analyse technique:*
   {trend_icon} Tendance: *{trend}*

🎯 *Signaux:*
"""

            if signals:
                for signal_name, signal_value in signals.items():
                    if signal_value in ['BUY', 'SELL', 'BULLISH', 'BEARISH']:
                        icon = '🟢' if signal_value in ['BUY', 'BULLISH'] else '🔴'
                        message += f"   {icon} {signal_name}: {signal_value}\n"

        # Envoyer le message (peut être long, donc on le coupe si nécessaire)
        if len(message) > 4000:
            # Telegram limite à 4096 caractères
            await update.message.reply_text(message[:4000] + "...", parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')

    except requests.Timeout:
        await update.message.reply_text("⏱️ Timeout: L'analyse prend trop de temps. Réessayez plus tard.")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /news <company> - Actualités récentes"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /news <company_name>\n\n"
            "Exemples:\n"
            "• /news LVMH\n"
            "• /news L'Oreal"
        )
        return

    company_name = " ".join(context.args)
    days_back = 7

    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/news/{company_name}",
            params={"days_back": days_back}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()
        articles = data.get('articles', [])

        if not articles:
            await update.message.reply_text(f"📭 Aucune actualité trouvée pour {company_name}.")
            return

        message = f"📰 *ACTUALITÉS* - {company_name}\n"
        message += f"({len(articles)} articles, derniers {days_back} jours)\n\n"

        for i, article in enumerate(articles[:5], 1):  # Limiter à 5 articles
            title = article.get('title', 'Sans titre')
            source = article.get('source', 'Source inconnue')
            date = article.get('published_date', '')[:10]
            url = article.get('url', '')

            message += f"{i}. *{title}*\n"
            message += f"   📅 {date} • {source}\n"
            if url:
                message += f"   🔗 {url}\n"
            message += "\n"

        if len(articles) > 5:
            message += f"... et {len(articles) - 5} autres articles."

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def technical_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /technical <ticker> - Analyse technique"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /technical <ticker>\n\n"
            "Exemples:\n"
            "• /technical MC.PA\n"
            "• /technical OR.PA"
        )
        return

    ticker = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "6mo"

    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/technical/{ticker}",
            params={"period": period}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()

        trend = data.get('trend', 'UNKNOWN')
        signals = data.get('signals', {})
        levels = data.get('levels', {})

        trend_icon = {
            'BULLISH': '🐂',
            'BEARISH': '🐻',
            'SIDEWAYS': '➡️'
        }.get(trend, '➡️')

        message = f"""
📈 *ANALYSE TECHNIQUE* - {ticker}
Période: {period}

{trend_icon} *Tendance:* {trend}

🎯 *Signaux:*
"""

        if signals:
            for name, value in signals.items():
                if isinstance(value, str) and value in ['BUY', 'SELL', 'BULLISH', 'BEARISH', 'NEUTRAL']:
                    icon = '🟢' if value in ['BUY', 'BULLISH'] else '🔴' if value in ['SELL', 'BEARISH'] else '⚪'
                    message += f"   {icon} {name}: {value}\n"
        else:
            message += "   Aucun signal détecté\n"

        message += "\n📊 *Niveaux:*\n"

        if levels:
            support = levels.get('support', [])
            resistance = levels.get('resistance', [])

            if support:
                message += f"   🟢 Support: {', '.join([f'{s:.2f}€' for s in support[:3]])}\n"
            if resistance:
                message += f"   🔴 Résistance: {', '.join([f'{r:.2f}€' for r in resistance[:3]])}\n"
        else:
            message += "   Aucun niveau identifié\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


# ==========================================
# MARKET DATA
# ==========================================

@authorized_only
async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /stock <ticker> - Informations de marché"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /stock <ticker>\n\n"
            "Exemples:\n"
            "• /stock MC.PA\n"
            "• /stock OR.PA"
        )
        return

    ticker = context.args[0].upper()

    try:
        response = requests.get(f"{API_BASE_URL}/market/stock/{ticker}")

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()

        name = data.get('longName', ticker)
        price = data.get('currentPrice', 0)
        change = data.get('regularMarketChangePercent', 0)
        volume = data.get('volume', 0)
        market_cap = data.get('marketCap', 0) / 1_000_000_000
        pe = data.get('trailingPE', 0)
        dividend = data.get('dividendYield', 0) * 100 if data.get('dividendYield') else 0

        change_icon = "📈" if change >= 0 else "📉"

        message = f"""
📊 *{name}* ({ticker})

💰 *Prix:* {price:.2f}€ {change_icon} ({change:+.2f}%)
📊 *Volume:* {volume:,}
💼 *Cap. boursière:* {market_cap:.1f}B€

📈 *Ratios:*
   • PER: {pe:.2f}
   • Dividende: {dividend:.2f}%

💡 Utilisez /analyze {ticker} pour une analyse complète IA.
"""

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


@authorized_only
async def history_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /history <ticker> - Historique des cours"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /history <ticker> [period]\n\n"
            "Périodes: 1mo, 3mo, 6mo, 1y, 2y, 5y\n\n"
            "Exemples:\n"
            "• /history MC.PA\n"
            "• /history OR.PA 1y"
        )
        return

    ticker = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "1y"

    try:
        response = requests.get(
            f"{API_BASE_URL}/market/history/{ticker}",
            params={"period": period, "interval": "1d"}
        )

        if response.status_code != 200:
            await update.message.reply_text(handle_api_error(response))
            return

        data = response.json()
        history_data = data.get('data', [])

        if not history_data:
            await update.message.reply_text(f"📭 Aucune donnée historique pour {ticker}.")
            return

        # Calculer quelques statistiques
        prices = [d['Close'] for d in history_data if 'Close' in d]

        if not prices:
            await update.message.reply_text("❌ Données incomplètes.")
            return

        current = prices[-1]
        oldest = prices[0]
        highest = max(prices)
        lowest = min(prices)
        avg = sum(prices) / len(prices)
        change = ((current - oldest) / oldest * 100) if oldest > 0 else 0

        change_icon = "📈" if change >= 0 else "📉"

        message = f"""
📊 *HISTORIQUE* - {ticker}
Période: {period} ({len(history_data)} jours)

💰 *Prix actuel:* {current:.2f}€
📈 *Performance:* {change_icon} {change:+.2f}%

📊 *Statistiques:*
   • Plus haut: {highest:.2f}€
   • Plus bas: {lowest:.2f}€
   • Moyenne: {avg:.2f}€

💡 Utilisez /technical {ticker} pour l'analyse technique.
"""

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")


# ==========================================
# CALLBACK QUERY HANDLERS (boutons inline)
# ==========================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les clics sur les boutons inline"""
    query = update.callback_query
    await query.answer()

    user_id = get_user_id(update)

    if query.data == 'show_treasury':
        # Rediriger vers /balance
        await balance_command(update, context)

    elif query.data == 'show_opportunities':
        # Rediriger vers /opportunities
        await opportunities_command(update, context)

    elif query.data == 'show_health':
        # Rediriger vers /health
        await health_command(update, context)


# ==========================================
# EXPORTS
# ==========================================

# Liste de tous les handlers à enregistrer dans le bot principal
COMMAND_HANDLERS = {
    # Trésorerie
    'balance': balance_command,
    'deposit': deposit_command,
    'history': history_command,
    'cashflow': cashflow_command,

    # Portfolio
    'portfolio': portfolio_command,
    'positions': positions_command,
    'health': health_command,
    'rebalance': rebalance_command,

    # Opportunités
    'opportunities': opportunities_command,
    'pending': pending_command,
    'accept': accept_command,
    'reject': reject_command,

    # Transactions
    'buy': buy_command,
    'sell': sell_command,

    # Analyses
    'analyze': analyze_command,
    'news': news_command,
    'technical': technical_command,

    # Market
    'stock': stock_command,
    'historystock': history_stock_command,
}

# Handler pour les callbacks (boutons inline)
CALLBACK_HANDLER = button_callback
