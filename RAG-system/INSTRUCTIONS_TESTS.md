# Instructions Complètes - Tests & Indexation

**Date:** 2026-02-02

---

## 🚀 Démarrage Rapide

### Étape 1: Lancer l'API

```bash
# Terminal 1
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system
uvicorn api.main:app --reload
```

Attendre le message: ✅ `Application startup complete.`

---

### Étape 2: Indexer des PDF (pour tests RAG)

```bash
# Terminal 2
python3 scripts/quick_index.py
```

**Temps:** 2-5 minutes
**Résultat:** 3 collections créées (Hermès, LVMH, Safran)

---

### Étape 3: Lancer les Tests

```bash
# Dans le Terminal 2
./run_tests.sh
```

---

## 📊 Si des Tests Échouent

### Tests Portfolio qui Échouent

Si tu as encore les erreurs sur `test_pru_calculation` et `test_sell_position`:

#### Debug 1: Vérifier la base de données

```bash
# Supprimer l'ancienne DB pour repartir de zéro
rm data/portfolio.db

# Relancer l'API
uvicorn api.main:app --reload

# Relancer les tests
./run_tests.sh portfolio
```

#### Debug 2: Tester manuellement

```bash
# Test manuel du PRU
curl -X POST "http://localhost:8000/portfolio/add" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "price": 700.0,
    "user_id": "test_manual"
  }'

# Achat 2
curl -X POST "http://localhost:8000/portfolio/add" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 5,
    "price": 750.0,
    "user_id": "test_manual"
  }'

# Vérifier le portefeuille
curl "http://localhost:8000/portfolio?user_id=test_manual" | python3 -m json.tool
```

**Résultat attendu:**
```json
{
  "positions": [
    {
      "ticker": "MC.PA",
      "quantity": 15,
      "avg_price": 716.67,  // (10*700 + 5*750) / 15
      ...
    }
  ]
}
```

#### Debug 3: Logs détaillés

```bash
# Tests avec output verbeux
pytest tests/test_portfolio.py::TestPortfolioManagement::test_pru_calculation -v -s
```

---

## 📝 Output des Tests à Me Fournir

Si les tests échouent encore, envoie-moi:

```bash
./run_tests.sh > test_output.txt 2>&1
```

Puis copie le contenu de `test_output.txt` ici.

Ou juste:
```bash
./run_tests.sh
```

Et copie l'output complet des tests qui échouent.

---

## 🧪 Tests par Catégorie

```bash
# Tous les tests
./run_tests.sh

# Seulement Portfolio
./run_tests.sh portfolio

# Seulement RAG
./run_tests.sh rag

# Seulement Financial Analysis
./run_tests.sh financial

# Seulement Integration
./run_tests.sh integration

# Tests rapides (sans slow)
./run_tests.sh quick

# Avec couverture
./run_tests.sh coverage
```

---

## 🔧 Fichiers Créés pour Toi

### Scripts d'Indexation

1. **`scripts/quick_index.py`**
   - Indexe 3 PDF légers (2-5 min)
   - Pour les tests RAG

2. **`scripts/index_all_pdfs.py`**
   - Indexe TOUS les PDF (2-4h)
   - Pour avoir toutes les collections

### Documentation

1. **`CORRECTIONS_TESTS.md`**
   - Détails des bugs corrigés
   - Explication des corrections

2. **`GUIDE_INDEXATION_TESTS.md`**
   - Guide complet d'indexation
   - Troubleshooting

3. **`INSTRUCTIONS_TESTS.md`** (ce fichier)
   - Instructions rapides
   - Debug si tests échouent

---

## 🐛 Bugs Corrigés

### Bug 1: Calcul PRU

**Avant (INCORRECT):**
```python
current_value = ? * ?,  # SQL invalide
```

**Après (CORRECT):**
```python
new_current_value = price * new_qty
# Puis dans UPDATE:
current_value = ?
```

### Bug 2: Vente Position

**Avant (INCORRECT):**
```python
current_value = avg_price * ?,  # SQL invalide
```

**Après (CORRECT):**
```python
price_for_value = current_price if current_price else avg_price
new_current_value = price_for_value * new_qty
```

### Bug 3: Endpoint /portfolio/context

**Avant (INCORRECT):**
```python
{pos['gain_loss_percent']:+.2f}%  # Crash si None
```

**Après (CORRECT):**
```python
gain_loss_percent = pos['gain_loss_percent'] or 0
{gain_loss_percent:+.2f}%  # Safe
```

---

## ❓ Si Problème Persiste

### Option 1: Tests Manuels

Utilise les commandes curl ci-dessus pour tester manuellement.

### Option 2: M'envoyer l'Output

Lance:
```bash
./run_tests.sh
```

Et copie-moi:
- Les tests qui FAIL
- Le message d'erreur complet
- Le "assert" qui échoue

### Option 3: Vérifier la DB

```bash
# Voir le schéma de la base
sqlite3 data/portfolio.db ".schema portfolio"

# Voir les données
sqlite3 data/portfolio.db "SELECT * FROM portfolio LIMIT 10;"
```

---

## ✅ Checklist Avant de Tester

- [ ] API lancée: `uvicorn api.main:app --reload`
- [ ] API accessible: `curl http://localhost:8000/health`
- [ ] (Optionnel) PDF indexés: `python3 scripts/quick_index.py`
- [ ] Collections créées: `curl http://localhost:8000/collections`
- [ ] Tests lancés: `./run_tests.sh`

---

## 📈 État Actuel

### ✅ Ce qui Fonctionne

- Scripts d'indexation créés
- Documentation complète
- Corrections des bugs SQL appliquées
- Guide d'utilisation complet

### ⚠️ À Vérifier

- Tests portfolio passent-ils maintenant?
- Les collections RAG sont-elles créées?
- Les tests skipped tournent-ils après indexation?

---

## 🎯 Prochaines Actions

1. **Lancer API:** `uvicorn api.main:app --reload`
2. **Indexer:** `python3 scripts/quick_index.py`
3. **Tester:** `./run_tests.sh`
4. **Si échec:** Copier l'output et me l'envoyer

---

**Questions? Problèmes?** Envoie-moi l'output exact des tests! 🚀
