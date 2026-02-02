# Corrections des Tests - RAG-PEA

**Date:** 2026-02-02
**Statut:** ✅ Corrections appliquées

---

## Problèmes Identifiés & Corrections

### 1. ❌ Test `test_pru_calculation` - Calcul PRU incorrect

**Erreur:**
```
AssertionError: PRU devrait être 716.67, obtenu 707.14
```

**Cause:** Bug SQL dans `api/database/portfolio_db.py` ligne 116
```python
# AVANT (INCORRECT):
current_value = ? * ?,  # SQL invalide
```

**✅ Correction appliquée:**
```python
# APRÈS (CORRECT):
new_avg_price = ((old_price * old_qty) + (price * quantity)) / new_qty
new_current_value = price * new_qty
# Puis dans l'UPDATE:
current_value = ?,  # Valeur calculée en Python
```

---

### 2. ❌ Test `test_sell_position` - Quantité incorrecte après vente

**Erreur:**
```
AssertionError: Quantité doit être 10 après vente de 10
assert 45.0 == 10
```

**Cause:** Bug SQL dans `api/database/portfolio_db.py` ligne 179-181
```python
# AVANT (INCORRECT):
cursor.execute("""
    UPDATE portfolio
    SET quantity = ?,
        current_value = avg_price * ?,  # SQL invalide
    ...
""", (new_qty, new_qty, pos_id))
```

**✅ Correction appliquée:**
```python
# APRÈS (CORRECT):
# Récupérer avg_price et current_price
cursor.execute("""
    SELECT id, quantity, company_name, avg_price, current_price ...
""", (user_id, ticker))

pos_id, current_qty, company_name, avg_price, current_price = position

# Calculer valeur en Python
price_for_value = current_price if current_price else avg_price
new_current_value = price_for_value * new_qty

cursor.execute("""
    UPDATE portfolio
    SET quantity = ?,
        current_value = ?,  # Valeur pré-calculée
    ...
""", (new_qty, new_current_value, pos_id))
```

---

### 3. ❌ Test `test_portfolio_context_for_ai` - Erreur 500

**Erreur:**
```
assert 500 == 200
```

**Cause:** Valeurs `None` non gérées dans `api/services/portfolio_manager.py`
```python
# AVANT (INCORRECT):
• Performance: {pos['gain_loss_percent']:+.2f}%  # Crash si None
```

**✅ Correction appliquée:**
```python
# APRÈS (CORRECT):
# Gérer les valeurs None
avg_price = pos['avg_price'] or 0
current_price = pos['current_price'] or 0
current_value = pos['current_value'] or 0
gain_loss_percent = pos['gain_loss_percent'] or 0

• Performance: {gain_loss_percent:+.2f}%  # Safe
```

---

### 4. ❌ Test `test_portfolio_to_analysis_feedback_loop` - Erreur 500

**Erreur:**
```
assert 500 == 200
```

**Cause:** Même problème que #3 - valeurs None dans `/portfolio/context`

**✅ Correction appliquée:** Identique au point #3

---

## Commandes pour Exécuter les Tests

### Tests complets (tous les tests, y compris les slow)

```bash
# Méthode 1: Via le script
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system
./run_tests.sh

# Méthode 2: Directement avec pytest
pytest tests/ -v

# Méthode 3: Seulement les tests slow/integration
pytest tests/ -v -m "slow or integration"
```

### Tests par catégorie

```bash
# Tests RAG uniquement
./run_tests.sh rag

# Tests Portfolio uniquement
./run_tests.sh portfolio

# Tests Financial Analysis uniquement
./run_tests.sh financial

# Tests d'intégration end-to-end
./run_tests.sh integration

# Tests rapides (sans les slow)
./run_tests.sh quick
```

### Tests avec couverture de code

```bash
# Avec rapport HTML
./run_tests.sh coverage

# OU directement:
pytest tests/ -v --cov=api --cov-report=html --cov-report=term-missing

# Voir le rapport:
open htmlcov/index.html
```

### Tests avec plus de détails

```bash
# Mode verbeux avec output complet
pytest tests/ -v -s

# Arrêter au premier échec
pytest tests/ -v -x

# Exécuter un test spécifique
pytest tests/test_portfolio.py::TestPortfolioManagement::test_pru_calculation -v

# Ré-exécuter seulement les tests qui ont échoué
pytest tests/ --lf -v
```

---

## Vérification de la Couverture des Tests

### Fonctionnalités Actuellement Testées

#### ✅ Gestion de Portfolio (`test_portfolio.py`)
- [x] Ajout de position
- [x] Ajout de positions multiples
- [x] Calcul du PRU (Prix de Revient Unitaire)
- [x] Vente de position (partielle/totale)
- [x] Résumé du portefeuille
- [x] Score de santé du portefeuille
- [x] Recommandations de rééquilibrage
- [x] Détails d'une position
- [x] Contexte pour l'IA
- [x] Gestion d'erreurs

#### ✅ Intégration End-to-End (`test_integration.py`)
- [x] Workflow complet (données → RAG → agents → portfolio)
- [x] Intégration RAG → Agents CrewAI
- [x] Boucle de feedback Portfolio ↔ Analyse
- [x] Intégration multi-sources (Yahoo, RAG, News, Technical)
- [x] Mise à jour prix en temps réel
- [x] Récupération après erreurs
- [x] Performance sous charge
- [x] Cohérence des données

#### ✅ Workflow RAG (`test_rag_workflow.py`)
- [x] Indexation de documents
- [x] Recherche sémantique
- [x] Génération de réponses
- [x] Gestion des collections
- [x] Upload de fichiers

#### ✅ Analyses Financières (`test_financial_analysis.py`)
- [x] Données de marché Yahoo Finance
- [x] Analyse technique (RSI, MACD, Bollinger)
- [x] Analyse de sentiment (news)
- [x] Analyse complète multi-sources
- [x] Agents CrewAI

### Fonctionnalités NON Testées (À Ajouter)

#### ⚠️ Tests Manquants

1. **Backtesting Engine**
   - [ ] Exécution de stratégies de trading
   - [ ] Calcul des métriques (Sharpe, drawdown, win rate)
   - [ ] Walk-forward optimization

2. **Telegram Bot**
   - [ ] Commandes du bot
   - [ ] Système d'alertes
   - [ ] Rapport quotidien/hebdomadaire
   - [ ] Q&A avec RAG

3. **Machine Learning** (quand implémenté)
   - [ ] Prédictions de prix (LSTM)
   - [ ] Classification de tendance (XGBoost)
   - [ ] Évaluation de la précision

4. **Sécurité** (si implémenté)
   - [ ] Authentification
   - [ ] Validation des inputs
   - [ ] Rate limiting

5. **Base de Données**
   - [ ] Migrations
   - [ ] Transactions atomiques
   - [ ] Rollback en cas d'erreur

6. **Cache & Performance**
   - [ ] Cache Yahoo Finance
   - [ ] Circuit breaker
   - [ ] Rate limiting

---

## Prochaines Étapes

### 1. Exécuter les tests corrigés

```bash
./run_tests.sh
```

**Attendu:**
- ✅ `test_pru_calculation` devrait passer
- ✅ `test_sell_position` devrait passer
- ✅ `test_portfolio_context_for_ai` devrait passer
- ✅ `test_portfolio_to_analysis_feedback_loop` devrait passer

### 2. Si des tests échouent encore

```bash
# Mode verbeux pour voir les détails
pytest tests/ -v -s --tb=long

# Tester un seul fichier
pytest tests/test_portfolio.py -v -s
```

### 3. Vérifier la couverture de code

```bash
pytest tests/ -v --cov=api --cov-report=term-missing

# Voir quelles lignes ne sont pas couvertes
```

### 4. Ajouter tests manquants

Priorités:
1. **Tests du Backtesting Engine** (important pour la roadmap)
2. **Tests du Telegram Bot** (important pour la roadmap)
3. **Tests de sécurité** (si authentification ajoutée)
4. **Tests ML** (quand les modèles seront implémentés)

---

## Notes Importantes

### Tests Skipped

Les tests marqués `@pytest.mark.slow` ou `@pytest.mark.integration` sont skippés par défaut avec `./run_tests.sh quick`.

Pour les exécuter:
```bash
./run_tests.sh  # Exécute TOUS les tests
```

### Dépendances Requises

Avant de lancer les tests, assurez-vous que:
1. L'API est en cours d'exécution: `uvicorn api.main:app --reload`
2. Ollama est lancé (optionnel): `ollama serve`
3. Les dépendances sont installées: `pip install -r requirements.txt`

### Debugging

Si un test échoue:

```bash
# Voir la stacktrace complète
pytest tests/test_portfolio.py::TestPortfolioManagement::test_pru_calculation -v --tb=long

# Ajouter des prints
pytest tests/ -v -s

# Arrêter au premier échec
pytest tests/ -x
```

---

## Résumé

✅ **Corrections appliquées:** 4/4
- Calcul PRU corrigé
- Vente de position corrigée
- Endpoint `/portfolio/context` corrigé
- Gestion des valeurs None ajoutée

📊 **Couverture de code:** À vérifier avec `./run_tests.sh coverage`

🎯 **Prochaine étape:** Exécuter `./run_tests.sh` et vérifier que tous les tests passent

---

**Fichiers modifiés:**
- `api/database/portfolio_db.py` (lignes 105-121, 156-188)
- `api/services/portfolio_manager.py` (lignes 39-55)
