# 📚 Ordre de Lecture - Documentation RAG-PEA System

Pour bien comprendre le projet, lire les documents dans cet ordre :

---

## 1️⃣ README.md (10 min) - COMMENCER ICI
**Vue d'ensemble du projet**

- Fonctionnalités principales (RAG, ML, Backtesting, Portfolio, Telegram Bot)
- Démarrage rapide (installation, premier test)
- Architecture du projet
- Exemples de code pour chaque module

👉 **À lire en premier** pour comprendre ce que fait le système et comment le lancer.

---

## 2️⃣ GUIDE_UTILISATION.md (30 min) - APPROFONDIR
**Guide pratique détaillé**

- RAG v2: Comment indexer et interroger des documents
- Portfolio Management: Gestion positions, cash, opportunités
- Analyse de Marché: Technical, News, Sentiment
- **Machine Learning**: Entraîner modèles, prédire prix
- **Backtesting**: Tester stratégies, comparer, optimiser
- **Intelligence**: Analyse complète ML + Backtesting + Technical
- Exemples pratiques avec cURL et Python

👉 **À lire après README** pour apprendre à utiliser toutes les fonctionnalités.

---

## 3️⃣ API_ENDPOINTS.md (60 min) - RÉFÉRENCE COMPLÈTE
**Documentation technique de l'API**

- **48 endpoints** documentés en détail
- Pour chaque endpoint:
  - Description technique
  - Outils utilisés (TensorFlow, yfinance, CrewAI, etc.)
  - Paramètres et schémas request/response
  - Exemples cURL et Python
  - Codes d'erreur
- Glossaire technique complet

👉 **Référence à consulter** quand vous développez ou intégrez l'API.

---

## 4️⃣ DEPLOYMENT.md (20 min) - DÉPLOIEMENT
**Guide de déploiement sur VPS**

- Configuration Docker et docker-compose
- Variables d'environnement
- Déploiement sur VPS Ubuntu
- Configuration Nginx reverse proxy
- Monitoring et logs
- Troubleshooting

👉 **À lire avant de déployer** en production sur votre VPS.

---

## 📊 Temps de lecture total: ~2h

**Parcours recommandé selon votre besoin:**

### Je veux tester rapidement (30 min)
1. README.md → Section "Démarrage Rapide"
2. GUIDE_UTILISATION.md → Section de votre choix (RAG, ML, Backtesting)

### Je veux développer avec l'API (1h30)
1. README.md → Architecture
2. GUIDE_UTILISATION.md → Tous les modules
3. API_ENDPOINTS.md → Endpoints dont vous avez besoin

### Je veux déployer en production (2h)
1. README.md → Vue d'ensemble
2. DEPLOYMENT.md → Configuration complète
3. API_ENDPOINTS.md → Référence pour tests post-déploiement

---

## 🔧 Après la lecture

**Pour aller plus loin:**
- Voir le code dans `api/` pour comprendre l'implémentation
- Consulter les tests dans `tests/` pour exemples d'usage
- Lire les docstrings dans le code pour détails techniques

**Support:**
- Issues GitHub: https://github.com/madmax0978/agent-business/issues
- Documentation interactive: http://localhost:8000/docs (après lancement API)
