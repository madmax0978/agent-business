# Integration Tresorerie PEA - Portfolio Manager

## Modifications apportees

### Fichier modifie
`/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/services/portfolio_manager.py`

---

## 1. Imports ajoutes

```python
from typing import Dict, List, Optional
from datetime import datetime
```

---

## 2. Methode `get_portfolio_context_for_ai()` - AMELIOREE

### Avant
- Affichait uniquement les positions du portefeuille
- Performance globale limitee aux positions

### Apres
- **Section TRESORERIE PEA** ajoutee :
  - Valeur totale PEA (cash + positions)
  - Total depose sur le PEA
  - Cash disponible avec ratio
  - Cash investi avec ratio
  - Performance globale PEA (vs depots)
  - Date d'ouverture et dernier depot

- **Section POSITIONS** enrichie :
  - Distinction claire entre valeur positions et cash
  - Performance des positions separee de la performance PEA

- **Section OPPORTUNITES** dynamique :
  - S'affiche automatiquement si cash disponible > 100€
  - Liste les opportunites detectees (diversification, renforcement, etc.)

### Exemple de sortie

```
PORTEFEUILLE PEA DE L'UTILISATEUR:

💰 TRESORERIE PEA:
   • Valeur totale PEA: 5,500.00 €
   • Total depose: 5,000.00 €
   • Cash disponible: 1,200.00 € (21.8%)
   • Cash investi: 4,300.00 € (78.2%)
   • Performance globale PEA: 📈 500.00 € (+10.00%)
   • Date d'ouverture: 2024-01-15
   • Dernier depot: 2024-11-30

📊 POSITIONS EN PORTEFEUILLE:
   • Valeur positions: 4,300.00 €
   • Montant investi: 4,000.00 €
   • Plus/Moins-value positions: 📈 300.00 € (+7.50%)
   • Nombre de positions: 3 entreprises

💡 OPPORTUNITES D'INVESTISSEMENT DETECTEES:
   • Cash disponible pour investir: 1,200.00 €
   • DIVERSIFY: Portefeuille peu diversifie (3 positions)...
```

---

## 3. Nouvelle methode `analyze_cash_opportunities()`

### Description
Analyse automatiquement les opportunites d'investissement basees sur le cash disponible.

### Logique d'analyse

#### Seuil minimum
- Cash disponible doit etre > 100€ pour declencher des opportunites

#### Type 1: DIVERSIFY (Priorite: HIGH)
- **Condition**: < 5 positions dans le portefeuille
- **Action**: Suggere d'ajouter 2-3 nouvelles positions
- **Montant suggere**: 30% du cash ou 1000€ max

#### Type 2: ADD_TO_EXISTING (Priorite: MEDIUM)  
- **Condition**: Position performante (> +5%) ET poids < 20%
- **Action**: Renforcer la position gagnante
- **Montant suggere**: Calculé pour atteindre 15% de poids (max 40% du cash)
- **Details fournis**:
  - Ticker et company_name
  - Quantite suggeree
  - Prix actuel
  - Poids actuel vs cible
  - Performance actuelle

#### Type 3: REBALANCE_CASH (Priorite: MEDIUM)
- **Condition**: Ratio cash > 30% du total PEA
- **Action**: Investir progressivement pour optimiser le rendement
- **Montant suggere**: 50% du cash disponible

### Retour

```python
{
    "has_opportunities": True,
    "cash_available": 1200.00,
    "cash_ratio": 21.8,
    "portfolio_size": 3,
    "total_value": 5500.00,
    "opportunities": [
        {
            "type": "DIVERSIFY",
            "priority": "HIGH",
            "description": "Portefeuille peu diversifie...",
            "suggested_amount": 360.00,
            "reasoning": "Diversification insuffisante..."
        },
        {
            "type": "ADD_TO_EXISTING",
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "priority": "MEDIUM",
            "description": "Renforcer Apple Inc. (performance: +12.5%, poids actuel: 8.2%)",
            "suggested_amount": 450.00,
            "suggested_quantity": 2,
            "current_price": 225.00,
            "current_weight": 8.2,
            "target_weight": 15.0,
            "reasoning": "Position performante avec potentiel..."
        }
    ]
}
```

---

## 4. Nouvelle methode `save_opportunity_to_db()`

### Description
Sauvegarde une opportunite d'investissement en base de donnees.

### Parametres
- `ticker`: Symbole de l'action
- `company_name`: Nom de l'entreprise
- `recommendation_type`: DIVERSIFY, ADD_TO_EXISTING, REBALANCE_CASH
- `suggested_amount`: Montant suggere en euros
- `reasoning`: Explication de la recommandation
- `suggested_quantity`: Nombre d'actions (optionnel)
- `target_price`: Prix cible (optionnel)
- `confidence_score`: Score 0-1 (defaut: 0.7)
- `risk_level`: LOW, MEDIUM, HIGH (defaut: MEDIUM)
- `expires_in_days`: Validite en jours (defaut: 7)

### Table utilisee
`investment_opportunities`

### Champs enregistres automatiquement
- `cash_available_at_time`: Cash au moment de la creation
- `portfolio_value_at_time`: Valeur PEA au moment de la creation
- `status`: 'PENDING' par defaut
- `created_at`: Timestamp automatique
- `expires_at`: Calcule a partir de expires_in_days

### Exemple d'utilisation

```python
pm = PortfolioManager()

success = pm.save_opportunity_to_db(
    ticker="MSFT",
    company_name="Microsoft Corporation",
    recommendation_type="ADD_TO_EXISTING",
    suggested_amount=500.00,
    reasoning="Position performante avec faible exposition actuelle",
    suggested_quantity=2,
    confidence_score=0.8,
    risk_level="LOW",
    expires_in_days=7
)
```

---

## 5. Nouvelle methode `get_pending_opportunities()`

### Description
Recupere toutes les opportunites en attente (status='PENDING').

### Parametres
- `user_id`: Identifiant utilisateur
- `include_expired`: Inclure opportunites expirees (defaut: False)

### Filtres appliques
- Status = 'PENDING'
- expires_at > CURRENT_TIMESTAMP (si include_expired=False)
- Ordre: plus recentes en premier

### Retour
Liste de dictionnaires avec toutes les colonnes de la table.

### Exemple

```python
opportunities = pm.get_pending_opportunities("default_user")

for opp in opportunities:
    print(f"{opp['ticker']} - {opp['recommendation_type']}")
    print(f"Montant suggere: {opp['suggested_amount']}€")
    print(f"Expire le: {opp['expires_at']}")
```

---

## 6. Nouvelle methode `accept_opportunity()`

### Description
Accepte une opportunite et execute automatiquement la transaction.

### Workflow
1. Recupere l'opportunite par ID
2. Verifie qu'elle existe et est PENDING
3. Verifie qu'elle n'est pas expiree
4. Recupere le prix actuel du marche (si actual_price non fourni)
5. Calcule la quantite (si actual_quantity non fourni)
6. Execute la transaction via `db.add_position()`
7. Deduit automatiquement le cash (gere par portfolio_db)
8. Marque l'opportunite comme 'ACCEPTED'
9. Enregistre actioned_at timestamp

### Parametres
- `opportunity_id`: ID de l'opportunite
- `user_id`: Identifiant utilisateur
- `actual_quantity`: Quantite reelle (optionnel, calcule auto sinon)
- `actual_price`: Prix reel (optionnel, prix marche sinon)

### Retour

```python
# Succes
{
    "success": True,
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "quantity": 5,
    "price": 225.50,
    "total_amount": 1127.50,
    "message": "Transaction executee: 5 actions de Apple Inc. a 225.50€"
}

# Echec
{
    "success": False,
    "error": "Cash insuffisant / Opportunite expirée / Autre erreur"
}
```

### Gestion des erreurs
- Opportunite non trouvee
- Opportunite deja traitee
- Opportunite expiree
- Prix marche indisponible
- Quantite invalide
- Cash insuffisant

### Exemple

```python
result = pm.accept_opportunity(
    opportunity_id=123,
    user_id="default_user"
)

if result['success']:
    print(result['message'])
else:
    print(f"Erreur: {result['error']}")
```

---

## 7. Nouvelle methode `reject_opportunity()`

### Description
Rejette une opportunite d'investissement.

### Workflow
1. Verifie que l'opportunite existe et est PENDING
2. Marque le status comme 'REJECTED'
3. Ajoute la raison du rejet au champ reasoning (si fournie)
4. Enregistre actioned_at timestamp

### Parametres
- `opportunity_id`: ID de l'opportunite
- `user_id`: Identifiant utilisateur
- `reason`: Raison du rejet (optionnel)

### Retour
- `True`: Rejet reussi
- `False`: Opportunite introuvable ou erreur

### Exemple

```python
success = pm.reject_opportunity(
    opportunity_id=123,
    user_id="default_user",
    reason="Prefere attendre une baisse du cours"
)

if success:
    print("Opportunite rejetee")
else:
    print("Erreur lors du rejet")
```

---

## Integration avec portfolio_db

### Methodes utilisees de portfolio_db

1. **`get_treasury_status(user_id)`**
   - Recupere l'etat complet de la tresorerie PEA
   - Retourne: total_deposits, cash_available, cash_invested, etc.

2. **`get_portfolio_summary(user_id)`**
   - Retourne maintenant aussi `pea_treasury` avec toutes les infos PEA
   - Retourne aussi `cash_ratio` et `investment_ratio`

3. **`add_position()`**
   - Deduit automatiquement le cash disponible
   - Enregistre le cash flow event
   - Met a jour cash_invested

4. **`sell_position()`**
   - Ajoute automatiquement le cash au disponible
   - Enregistre le cash flow event
   - Met a jour cash_invested

---

## Cas d'usage complets

### Cas 1: Utilisateur depose 1000€

```python
# Via l'API ou direct DB
db = PortfolioDatabase()
db.deposit_cash(amount=1000, user_id="default_user")

# Le context AI affichera automatiquement les opportunites
pm = PortfolioManager()
context = pm.get_portfolio_context_for_ai("default_user")
# → Affiche section OPPORTUNITES avec suggestions
```

### Cas 2: Detection et creation d'opportunites

```python
pm = PortfolioManager()

# Analyser les opportunites
opps = pm.analyze_cash_opportunities("default_user")

if opps['has_opportunities']:
    for opp in opps['opportunities']:
        if opp['type'] == 'ADD_TO_EXISTING':
            # Sauvegarder en DB pour action ulterieure
            pm.save_opportunity_to_db(
                ticker=opp['ticker'],
                company_name=opp['company_name'],
                recommendation_type=opp['type'],
                suggested_amount=opp['suggested_amount'],
                reasoning=opp['reasoning'],
                suggested_quantity=opp.get('suggested_quantity'),
                expires_in_days=7
            )
```

### Cas 3: Workflow complet d'acceptation

```python
# 1. Lister les opportunites
opportunities = pm.get_pending_opportunities("default_user")

# 2. Utilisateur choisit une opportunite
opp_id = opportunities[0]['id']

# 3. Accepter et executer
result = pm.accept_opportunity(opp_id, "default_user")

if result['success']:
    # Transaction executee
    # Cash deduit automatiquement
    # Position ajoutee/renforcee
    print(f"Achat reussi: {result['quantity']} x {result['ticker']}")
else:
    print(f"Echec: {result['error']}")
```

---

## Points d'attention

### Edge cases geres

1. **Cash insuffisant**
   - Detection avant execution
   - Message d'erreur clair

2. **Opportunite expiree**
   - Verification automatique de expires_at
   - Rejet si expiree

3. **Prix marche indisponible**
   - Gestion d'erreur si Yahoo Finance echoue
   - Possibilite de fournir actual_price manuellement

4. **Division par zero**
   - Protection sur tous les calculs de ratios
   - Valeurs par defaut securisees

5. **Positions None**
   - Gestion des valeurs None dans tous les calculs
   - Utilisation de `.get()` avec defaults

### Performances

- Pas de calculs lourds
- 1 requete DB par methode en moyenne
- Mise en cache possible cote appelant

### Securite

- Verification user_id sur toutes les operations
- Validation des montants (CHECK constraints en DB)
- Validation des status avant modification

---

## Tests recommandes

### Test 1: Context enrichi
```python
pm = PortfolioManager()
context = pm.get_portfolio_context_for_ai("default_user")
assert "TRESORERIE PEA" in context
assert "Cash disponible" in context
```

### Test 2: Detection opportunites
```python
opps = pm.analyze_cash_opportunities("default_user")
assert 'has_opportunities' in opps
assert 'opportunities' in opps
```

### Test 3: Cycle complet
```python
# Creer opportunite
success = pm.save_opportunity_to_db(...)
assert success == True

# Lister
opps = pm.get_pending_opportunities("default_user")
assert len(opps) > 0

# Accepter
result = pm.accept_opportunity(opps[0]['id'])
assert result['success'] == True
```

---

## Compatibilite

### Fonctionnalites existantes
- ✅ Aucune fonctionnalite existante cassee
- ✅ `get_portfolio_context_for_ai()` enrichi mais compatible
- ✅ Toutes les autres methodes inchangees

### Base de donnees
- ✅ Utilise les nouvelles tables de portfolio_db
- ✅ Pas de migration necessaire (tables deja creees)

---

## Prochaines etapes possibles

1. **Integration API endpoints**
   - POST /portfolio/opportunities/analyze
   - GET /portfolio/opportunities/pending
   - POST /portfolio/opportunities/{id}/accept
   - POST /portfolio/opportunities/{id}/reject

2. **Ameliorations IA**
   - Analyser les news pour detecter opportunites
   - Scoring plus sophistique (technical analysis)
   - Alertes automatiques si nouvelle opportunite

3. **Alertes utilisateur**
   - Email/notification si nouvelle opportunite
   - Rappel avant expiration

4. **Dashboard**
   - Vue graphique des opportunites
   - Historique des opportunites acceptees/rejetees
   - Performance des opportunites suivies

---

**Date de modification**: 2024-02-04
**Fichier modifie**: `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/services/portfolio_manager.py`
**Status**: ✅ Pret pour integration
