#!/usr/bin/env python3
"""
Bot Telegram Principal - Agent PEA
Bot complet pour gérer votre portfolio via Telegram
"""

import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Charger variables d'environnement
load_dotenv()

# Configuration logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Importer le decorator de sécurité
from telegram_handlers import authorized_only

# États de conversation pour onboarding
(ASKING_INITIAL_CASH, ASKING_HAS_POSITIONS,
 ASKING_POSITION_TICKER, ASKING_POSITION_QUANTITY,
 ASKING_POSITION_PRICE, ASKING_MORE_POSITIONS) = range(6)

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_USERNAME = os.getenv("API_USERNAME", "admin")
API_PASSWORD = os.getenv("API_PASSWORD")

# Cache du token JWT
_auth_token = None


# ==========================================
# AUTHENTICATION
# ==========================================

def get_auth_headers():
    """Récupère les headers d'authentification avec token JWT"""
    global _auth_token
    import requests

    # Si pas de credentials configurés, retourner headers vides
    if not API_USERNAME or not API_PASSWORD:
        logger.warning("⚠️ API_USERNAME ou API_PASSWORD non configuré")
        return {}

    # Si token en cache, l'utiliser
    if _auth_token:
        return {"Authorization": f"Bearer {_auth_token}"}

    # Sinon, obtenir un nouveau token
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": API_USERNAME, "password": API_PASSWORD}
        )

        if response.status_code == 200:
            _auth_token = response.json()["access_token"]
            logger.info("✅ Token JWT obtenu")
            return {"Authorization": f"Bearer {_auth_token}"}
        else:
            logger.error(f"❌ Erreur auth: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        logger.error(f"❌ Erreur obtention token: {e}")
        return {}


# ==========================================
# ONBOARDING - Première utilisation
# ==========================================

@authorized_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start - Lance l'onboarding"""
    user = update.effective_user

    # Vérifier si l'utilisateur a déjà un portfolio
    user_id = str(user.id)

    welcome_text = f"""
👋 Bienvenue *{user.first_name}* sur *Agent PEA* !

Je suis votre assistant intelligent pour gérer votre Plan d'Épargne en Actions (PEA).

🎯 *Ce que je peux faire pour vous:*
• 💰 Gérer votre trésorerie PEA
• 📊 Suivre vos positions en temps réel
• 💎 Détecter des opportunités d'investissement
• 📈 Analyser vos actions avec l'IA
• 🤖 Rapports automatiques quotidiens/hebdomadaires

🚀 *Commençons par configurer votre PEA !*

Quel est le montant que vous souhaitez déposer sur votre PEA ?
(Exemple: 5000 pour 5000€)

_Tapez /cancel pour annuler à tout moment_
"""

    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown'
    )

    return ASKING_INITIAL_CASH


async def receive_initial_cash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reçoit le montant initial de cash"""
    try:
        amount = float(update.message.text.replace(',', '.'))

        if amount <= 0:
            await update.message.reply_text(
                "❌ Le montant doit être positif. Réessayez:"
            )
            return ASKING_INITIAL_CASH

        # Stocker dans le contexte
        context.user_data['initial_cash'] = amount

        # Demander si positions existantes
        keyboard = [
            [InlineKeyboardButton("✅ Oui, j'ai des positions", callback_data='has_positions_yes')],
            [InlineKeyboardButton("❌ Non, je commence de zéro", callback_data='has_positions_no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Parfait ! Dépôt de *{amount:,.2f} €* enregistré.\n\n"
            f"📊 Avez-vous déjà des positions à ajouter à votre portefeuille ?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        return ASKING_HAS_POSITIONS

    except ValueError:
        await update.message.reply_text(
            "❌ Montant invalide. Entrez un nombre (ex: 5000):"
        )
        return ASKING_INITIAL_CASH


async def handle_has_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la réponse sur les positions existantes"""
    query = update.callback_query
    await query.answer()

    if query.data == 'has_positions_no':
        # Pas de positions, finaliser l'onboarding
        return await finalize_onboarding(update, context)

    else:  # has_positions_yes
        context.user_data['positions'] = []

        await query.edit_message_text(
            "📊 *Ajout de positions*\n\n"
            "Entrez le ticker de votre première action:\n"
            "(Exemples: MC.PA, OR.PA, AI.PA)\n\n"
            "_Tapez /skip pour passer_",
            parse_mode='Markdown'
        )

        return ASKING_POSITION_TICKER


async def receive_position_ticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reçoit le ticker d'une position"""
    if update.message.text == '/skip':
        return await finalize_onboarding(update, context)

    ticker = update.message.text.upper().strip()
    context.user_data['current_position'] = {'ticker': ticker}

    await update.message.reply_text(
        f"✅ Ticker: *{ticker}*\n\n"
        f"Combien d'actions possédez-vous ?",
        parse_mode='Markdown'
    )

    return ASKING_POSITION_QUANTITY


async def receive_position_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reçoit la quantité d'actions"""
    try:
        quantity = float(update.message.text.replace(',', '.'))

        if quantity <= 0:
            await update.message.reply_text("❌ La quantité doit être positive. Réessayez:")
            return ASKING_POSITION_QUANTITY

        context.user_data['current_position']['quantity'] = quantity

        await update.message.reply_text(
            f"✅ Quantité: *{quantity}*\n\n"
            f"À quel prix avez-vous acheté ces actions ? (PRU en €)",
            parse_mode='Markdown'
        )

        return ASKING_POSITION_PRICE

    except ValueError:
        await update.message.reply_text("❌ Quantité invalide. Entrez un nombre:")
        return ASKING_POSITION_QUANTITY


async def receive_position_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reçoit le prix d'achat"""
    try:
        price = float(update.message.text.replace(',', '.'))

        if price <= 0:
            await update.message.reply_text("❌ Le prix doit être positif. Réessayez:")
            return ASKING_POSITION_PRICE

        # Compléter la position
        position = context.user_data['current_position']
        position['price'] = price
        position['company_name'] = position['ticker'].split('.')[0]  # Simplifié

        # Ajouter à la liste
        context.user_data['positions'].append(position)

        # Demander si d'autres positions
        keyboard = [
            [InlineKeyboardButton("✅ Oui, ajouter une autre", callback_data='add_another_yes')],
            [InlineKeyboardButton("❌ Non, c'est tout", callback_data='add_another_no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        ticker = position['ticker']
        qty = position['quantity']
        total = qty * price

        await update.message.reply_text(
            f"✅ Position ajoutée !\n\n"
            f"📊 *{ticker}*: {qty} actions à {price:.2f}€ = {total:,.2f}€\n\n"
            f"Voulez-vous ajouter une autre position ?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        return ASKING_MORE_POSITIONS

    except ValueError:
        await update.message.reply_text("❌ Prix invalide. Entrez un nombre:")
        return ASKING_POSITION_PRICE


async def handle_more_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère l'ajout d'autres positions"""
    query = update.callback_query
    await query.answer()

    if query.data == 'add_another_no':
        return await finalize_onboarding(update, context)

    else:  # add_another_yes
        await query.edit_message_text(
            "📊 *Nouvelle position*\n\n"
            "Entrez le ticker:",
            parse_mode='Markdown'
        )
        return ASKING_POSITION_TICKER


async def finalize_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finalise l'onboarding et configure le portfolio"""
    import requests

    # Récupérer les données
    initial_cash = context.user_data.get('initial_cash', 0)
    positions = context.user_data.get('positions', [])

    # Message de traitement
    if update.callback_query:
        await update.callback_query.edit_message_text("⏳ Configuration en cours...")
    else:
        await update.message.reply_text("⏳ Configuration en cours...")

    try:
        # Obtenir les headers d'authentification
        auth_headers = get_auth_headers()

        # 1. Déposer le cash
        response = requests.post(
            f"{API_BASE_URL}/portfolio/deposit",
            params={"amount": initial_cash, "notes": "Dépôt initial onboarding"},
            headers=auth_headers
        )

        if response.status_code != 200:
            raise Exception(f"Erreur dépôt: {response.text}")

        # 2. Ajouter les positions
        total_invested = 0
        for pos in positions:
            response = requests.post(
                f"{API_BASE_URL}/portfolio/add",
                json={
                    "ticker": pos['ticker'],
                    "company_name": pos['company_name'],
                    "quantity": pos['quantity'],
                    "price": pos['price']
                },
                headers=auth_headers
            )

            if response.status_code == 200:
                total_invested += pos['quantity'] * pos['price']

        # 3. Récupérer le résumé
        response = requests.get(f"{API_BASE_URL}/portfolio", headers=auth_headers)
        summary = response.json()

        # Message de succès
        success_text = f"""
✅ *Configuration terminée !*

💰 *Votre PEA:*
• Total déposé: {initial_cash:,.2f} €
• Cash disponible: {summary['pea_treasury']['cash_available']:,.2f} €
• Cash investi: {summary['pea_treasury']['cash_invested']:,.2f} €

📊 *Positions: {len(positions)}*
"""

        for pos in positions:
            success_text += f"\n• {pos['ticker']}: {pos['quantity']} actions"

        success_text += """

🎯 *Prochaines étapes:*
• /help - Voir toutes les commandes
• /portfolio - Voir votre portfolio complet
• /opportunities - Détecter opportunités
• /settings - Configurer les alertes

🤖 Votre assistant est prêt !
"""

        if update.callback_query:
            await update.callback_query.message.reply_text(
                success_text,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                success_text,
                parse_mode='Markdown'
            )

        # Nettoyer le contexte
        context.user_data.clear()

        return ConversationHandler.END

    except Exception as e:
        error_text = f"❌ Erreur lors de la configuration: {str(e)}\n\nContactez le support."

        if update.callback_query:
            await update.callback_query.message.reply_text(error_text)
        else:
            await update.message.reply_text(error_text)

        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule l'onboarding"""
    await update.message.reply_text(
        "❌ Configuration annulée.\n\n"
        "Tapez /start pour recommencer."
    )
    context.user_data.clear()
    return ConversationHandler.END


# ==========================================
# COMMANDES PRINCIPALES
# ==========================================

@authorized_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /help - Affiche l'aide"""
    help_text = """
📚 *GUIDE COMPLET - Agent PEA*

🎯 *COMMANDES PRINCIPALES*

💰 *Trésorerie PEA:*
• /balance - Voir votre trésorerie
• /deposit <montant> - Déposer de l'argent
• /history - Historique des dépôts

📊 *Portfolio:*
• /portfolio - Vue complète du portfolio
• /positions - Liste des positions
• /health - Santé du portfolio (score)

💎 *Opportunités:*
• /opportunities - Détecter opportunités
• /pending - Opportunités en attente
• /accept <id> - Accepter une opportunité
• /reject <id> - Rejeter une opportunité

📈 *Transactions:*
• /buy <ticker> <qty> <price> - Acheter
• /sell <ticker> <qty> <price> - Vendre

🔍 *Analyses:*
• /analyze <ticker> - Analyse complète IA
• /news <company> - Actualités
• /technical <ticker> - Analyse technique

⚙️ *Paramètres:*
• /settings - Configurer alertes
• /reports - Activer rapports auto

❓ *Aide:*
• /usecases - Voir tous les cas d'usage
• /examples - Exemples de commandes
• /api - Documentation API complète

_Tapez /usecases pour des exemples détaillés_
"""

    await update.message.reply_text(help_text, parse_mode='Markdown')


@authorized_only
async def usecases_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /usecases - Explique tous les cas d'usage"""
    usecases_text = """
🎯 *CAS D'USAGE - Agent PEA*

*1️⃣ DÉMARRAGE*
• Configurez votre PEA avec /start
• Déposez votre capital initial
• Ajoutez vos positions existantes

*2️⃣ SUIVI QUOTIDIEN*
• Consultez /portfolio chaque matin
• Vérifiez /opportunities pour investir cash
• Recevez alertes automatiques

*3️⃣ ACHETER UNE ACTION*
Méthode 1: Via opportunité
  → /opportunities
  → /accept 123

Méthode 2: Manuellement
  → /buy MC.PA 5 750.0
  (Acheter 5 LVMH à 750€)

*4️⃣ VENDRE UNE ACTION*
  → /sell MC.PA 2 800.0
  (Vendre 2 LVMH à 800€)
  💡 L'argent revient dans le cash disponible

*5️⃣ ANALYSER AVANT D'ACHETER*
  → /analyze MC.PA
  → IA donne: recommandation, prix cible, risques

*6️⃣ GÉRER LE CASH*
Problème: Trop de cash non investi
  → /opportunities
  → Bot suggère où investir

*7️⃣ RAPPORTS AUTOMATIQUES*
• Si cash > 0: Rapport quotidien opportunités
• Si cash = 0: Rapport hebdomadaire santé

_Tapez /examples pour voir des exemples concrets_
"""

    await update.message.reply_text(usecases_text, parse_mode='Markdown')


# ==========================================
# MAIN
# ==========================================

def main():
    """Lance le bot"""

    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN non configuré dans .env")
        return

    # Créer l'application
    application = Application.builder().token(BOT_TOKEN).build()

    # Handler d'onboarding (ConversationHandler)
    onboarding_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASKING_INITIAL_CASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_initial_cash)],
            ASKING_HAS_POSITIONS: [CallbackQueryHandler(handle_has_positions)],
            ASKING_POSITION_TICKER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_position_ticker)],
            ASKING_POSITION_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_position_quantity)],
            ASKING_POSITION_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_position_price)],
            ASKING_MORE_POSITIONS: [CallbackQueryHandler(handle_more_positions)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Ajouter les handlers
    application.add_handler(onboarding_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('usecases', usecases_command))

    # Importer et ajouter tous les handlers de commandes depuis telegram_handlers.py
    from telegram_handlers import COMMAND_HANDLERS, CALLBACK_HANDLER

    for command_name, handler_func in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command_name, handler_func))
        logger.info(f"✅ Handler enregistré: /{command_name}")

    # Ajouter le handler pour les boutons inline
    application.add_handler(CallbackQueryHandler(CALLBACK_HANDLER))

    # Démarrer le bot
    logger.info("🤖 Bot Telegram démarré !")
    logger.info(f"📡 Connecté à l'API: {API_BASE_URL}")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
