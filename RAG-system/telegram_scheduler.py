#!/usr/bin/env python3
"""
Scheduler pour rapports automatiques Telegram
- Rapport quotidien si cash disponible > 0 (opportunités)
- Rapport hebdomadaire si cash = 0 (santé portfolio)
"""

import os
import asyncio
import logging
from datetime import datetime, time
from dotenv import load_dotenv
import requests
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


async def send_telegram_message(text: str):
    """Envoie un message sur Telegram"""
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode='Markdown'
        )
        logger.info("✅ Message envoyé sur Telegram")
    except Exception as e:
        logger.error(f"❌ Erreur envoi Telegram: {e}")


async def daily_opportunities_report():
    """
    Rapport quotidien des opportunités (si cash > 0)
    Exécuté tous les jours à 9h00
    """
    logger.info("🔄 Génération rapport quotidien opportunités...")

    try:
        # 1. Vérifier la trésorerie
        response = requests.get(f"{API_BASE_URL}/portfolio/treasury")
        treasury = response.json()

        cash_available = treasury.get('cash_available', 0)

        # Si pas de cash, on skip
        if cash_available < 100:
            logger.info(f"⏭️ Pas assez de cash ({cash_available:.2f}€), skip rapport quotidien")
            return

        # 2. Analyser les opportunités
        response = requests.post(f"{API_BASE_URL}/portfolio/opportunities/analyze")
        opportunities = response.json()

        # 3. Récupérer le portfolio
        response = requests.get(f"{API_BASE_URL}/portfolio")
        portfolio = response.json()

        # 4. Construire le message
        message = f"""
🌅 *RAPPORT QUOTIDIEN - {datetime.now().strftime('%d/%m/%Y')}*

💰 *TRÉSORERIE PEA*
• Cash disponible: *{cash_available:,.2f} €*
• Cash investi: {treasury.get('cash_invested', 0):,.2f} €
• Ratio cash: {opportunities.get('cash_ratio', 0):.1f}%

📊 *PORTFOLIO*
• Positions: {portfolio.get('total_positions', 0)}
• Valeur totale: {portfolio.get('total_value', 0):,.2f} €
• Performance: {portfolio['total_gain_loss_percent']:+.2f}%
"""

        # 5. Ajouter les opportunités
        if opportunities.get('has_opportunities'):
            message += "\n💎 *OPPORTUNITÉS DÉTECTÉES*\n"

            for i, opp in enumerate(opportunities['opportunities'][:3], 1):  # Max 3
                priority_emoji = "🔴" if opp['priority'] == 'HIGH' else "🟡"
                message += f"\n{priority_emoji} *{opp['type']}* (Priorité: {opp['priority']})\n"
                message += f"   {opp['reasoning'][:100]}...\n"
                if 'ticker' in opp:
                    message += f"   • Ticker: {opp['ticker']}\n"
                message += f"   • Montant suggéré: {opp['suggested_amount']:.2f}€\n"

            message += "\n💡 Tapez /opportunities pour voir tous les détails"
        else:
            message += "\n✅ Aucune opportunité urgente détectée"

        message += "\n\n_Rapport automatique quotidien_"

        # 6. Envoyer le message
        await send_telegram_message(message)

    except Exception as e:
        logger.error(f"❌ Erreur rapport quotidien: {e}")
        await send_telegram_message(f"❌ Erreur lors du rapport quotidien: {str(e)}")


async def weekly_portfolio_report():
    """
    Rapport hebdomadaire complet (santé + recommandations)
    Exécuté tous les lundis à 9h00
    """
    logger.info("🔄 Génération rapport hebdomadaire...")

    try:
        # 1. Récupérer le portfolio
        response = requests.get(f"{API_BASE_URL}/portfolio")
        portfolio = response.json()

        # 2. Santé du portfolio
        response = requests.get(f"{API_BASE_URL}/portfolio/health")
        health = response.json()

        # 3. Rééquilibrage
        response = requests.get(f"{API_BASE_URL}/portfolio/rebalance")
        rebalance = response.json()

        # 4. Trésorerie
        treasury = portfolio.get('pea_treasury', {})

        # 5. Construire le message
        message = f"""
📅 *RAPPORT HEBDOMADAIRE - {datetime.now().strftime('%d/%m/%Y')}*

💰 *PEA - VUE D'ENSEMBLE*
• Valeur totale: *{treasury.get('pea_total_value', 0):,.2f} €*
• Total déposé: {treasury.get('total_deposits', 0):,.2f} €
• Performance PEA: {treasury.get('pea_gain_loss_percent', 0):+.2f}%

📊 *PORTFOLIO*
• Positions: {portfolio.get('total_positions', 0)}
• Valeur investie: {portfolio.get('total_value', 0):,.2f} €
• Cash disponible: {treasury.get('cash_available', 0):,.2f} €
• Performance: {portfolio['total_gain_loss_percent']:+.2f}%

🏥 *SANTÉ DU PORTFOLIO*
• Score: *{health['score']}/100* ({health['grade']})
"""

        # Problèmes détectés
        if health.get('issues'):
            message += "\n⚠️ *Points d'attention:*\n"
            for issue in health['issues'][:3]:
                message += f"• {issue}\n"

        # Recommandations
        if health.get('recommendations'):
            message += "\n💡 *Recommandations:*\n"
            for rec in health['recommendations'][:3]:
                message += f"• {rec}\n"

        # Rééquilibrage
        if rebalance.get('needs_rebalance'):
            message += f"\n⚖️ *RÉÉQUILIBRAGE NÉCESSAIRE*\n"
            message += f"Nombre d'ajustements: {len(rebalance.get('recommendations', []))}\n"
            message += "Tapez /rebalance pour voir les détails"

        # Top 3 positions
        if portfolio.get('positions'):
            positions = sorted(
                portfolio['positions'],
                key=lambda x: x.get('gain_loss_percent', 0),
                reverse=True
            )[:3]

            message += "\n🏆 *TOP 3 POSITIONS*\n"
            for pos in positions:
                emoji = "🟢" if pos.get('gain_loss_percent', 0) >= 0 else "🔴"
                message += f"{emoji} {pos['company_name']}: {pos['gain_loss_percent']:+.2f}%\n"

        message += "\n\n_Rapport automatique hebdomadaire_"

        # 6. Envoyer le message
        await send_telegram_message(message)

    except Exception as e:
        logger.error(f"❌ Erreur rapport hebdomadaire: {e}")
        await send_telegram_message(f"❌ Erreur lors du rapport hebdomadaire: {str(e)}")


async def market_open_notification():
    """
    Notification d'ouverture du marché (optionnel)
    Exécuté du lundi au vendredi à 9h00
    """
    message = """
🔔 *MARCHÉ OUVERT*

Les marchés européens viennent d'ouvrir !

💡 Actions disponibles:
• /portfolio - Voir votre portfolio
• /opportunities - Détecter opportunités
• /health - Vérifier la santé

Bonne journée de trading ! 📈
"""
    await send_telegram_message(message)


async def check_api_health():
    """Vérifie que l'API est accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API accessible")
            return True
        else:
            logger.error(f"❌ API problème: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ API inaccessible: {e}")
        return False


def main():
    """Lance le scheduler"""

    if not BOT_TOKEN or not CHAT_ID:
        logger.error("❌ TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID non configuré")
        return

    # Vérifier l'API au démarrage
    logger.info("🔍 Vérification de l'API...")
    if not asyncio.run(check_api_health()):
        logger.error("❌ API non accessible. Assurez-vous qu'elle tourne sur " + API_BASE_URL)
        return

    # Créer le scheduler
    scheduler = AsyncIOScheduler()

    # Rapport quotidien opportunités (tous les jours à 9h00)
    scheduler.add_job(
        daily_opportunities_report,
        CronTrigger(hour=9, minute=0),
        id='daily_opportunities',
        name='Rapport quotidien opportunités',
        replace_existing=True
    )
    logger.info("✅ Job programmé: Rapport quotidien à 9h00")

    # Rapport hebdomadaire (tous les lundis à 9h00)
    scheduler.add_job(
        weekly_portfolio_report,
        CronTrigger(day_of_week='mon', hour=9, minute=0),
        id='weekly_report',
        name='Rapport hebdomadaire portfolio',
        replace_existing=True
    )
    logger.info("✅ Job programmé: Rapport hebdomadaire (lundi 9h00)")

    # Notification ouverture marché (optionnel - commenté par défaut)
    # scheduler.add_job(
    #     market_open_notification,
    #     CronTrigger(day_of_week='mon-fri', hour=9, minute=0),
    #     id='market_open',
    #     name='Notification ouverture marché'
    # )

    # Vérification API toutes les heures
    scheduler.add_job(
        check_api_health,
        CronTrigger(minute=0),  # Toutes les heures à minute 0
        id='api_health_check',
        name='Vérification API'
    )
    logger.info("✅ Job programmé: Vérification API (toutes les heures)")

    # Démarrer le scheduler
    scheduler.start()
    logger.info("🤖 Scheduler démarré !")
    logger.info("📅 Rapports programmés:")
    logger.info("   • Quotidien (opportunités): Tous les jours à 9h00")
    logger.info("   • Hebdomadaire (santé): Lundi à 9h00")

    # Garder le programme en vie
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("⏹️ Arrêt du scheduler")
        scheduler.shutdown()


if __name__ == '__main__':
    main()
