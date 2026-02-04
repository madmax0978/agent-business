# Guide d'Utilisation - Système de Trésorerie PEA

## Vue d'ensemble

Le système de trésorerie PEA permet de gérer votre Plan d'Épargne en Actions avec:
- **Trésorerie:** Suivre l'argent déposé, disponible et investi
- **Opportunités IA:** Suggestions automatiques d'investissement basées sur votre cash disponible
- **Historique complet:** Tous les dépôts et mouvements de cash sont tracés

## Fonctionnalités principales

### 1. Gestion de la Trésorerie

#### Déposer de l'argent sur le PEA
```bash
curl -X POST "http://localhost:8000/portfolio/deposit?amount=5000&notes=Depot_initial"
```

**Réponse:**
```json
{
    "message": "Dépôt de 5000.00€ effectué avec succès",
    "new_cash_available": 5000.0,
    "total_deposits": 5000.0
}
```

**Points importants:**
- L'argent déposé **ne peut jamais être retiré** (règle PEA)
- Le montant `total_deposits` est monotone croissant
- Le plafond PEA est de 150 000€

#### Consulter l'état de la trésorerie
```bash
curl "http://localhost:8000/portfolio/treasury"
```

**Réponse:**
```json
{
    "exists": true,
    "total_deposits": 5000.0,
    "cash_available": 3200.0,
    "cash_invested": 1800.0,
    "pea_opening_date": "2026-02-04",
    "last_deposit_date": "2026-02-04"
}
```

**Informations:**
- `total_deposits`: Total déposé depuis l'ouverture
- `cash_available`: Argent disponible pour investir
- `cash_invested`: Valeur actuelle des positions

#### Historique des dépôts
```bash
curl "http://localhost:8000/portfolio/treasury/deposits?limit=10"
```

#### Flux de trésorerie complets
```bash
# Tous les mouvements
curl "http://localhost:8000/portfolio/treasury/cashflow"

# Seulement les achats
curl "http://localhost:8000/portfolio/treasury/cashflow?event_type=BUY"

# Seulement les ventes
curl "http://localhost:8000/portfolio/treasury/cashflow?event_type=SELL"
```

### 2. Achats et Ventes d'Actions

#### Acheter une action
```bash
curl -X POST "http://localhost:8000/portfolio/add" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "LVMH.PA",
    "company_name": "LVMH",
    "quantity": 5,
    "price": 750.0
  }'
```

**Comportement:**
1. ✅ Vérifie que vous avez assez de cash disponible (5 × 750 = 3750€)
2. ✅ Déduit automatiquement 3750€ du cash disponible
3. ✅ Ajoute la position à votre portfolio
4. ✅ Enregistre la transaction et le mouvement de cash

**Erreurs possibles:**
```json
{
    "detail": "Cash insuffisant. Disponible: 1000.00€, Requis: 3750.00€"
}
```

#### Vendre une action
```bash
curl -X POST "http://localhost:8000/portfolio/sell" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "LVMH.PA",
    "quantity": 2,
    "price": 800.0
  }'
```

**Comportement:**
1. ✅ Vend 2 actions à 800€ = 1600€
2. ✅ Ajoute automatiquement 1600€ au cash disponible
3. ✅ Met à jour la position (quantité: 5 → 3)
4. ✅ Enregistre la transaction et le mouvement de cash

**Important:** L'argent de la vente reste sur le PEA (ne peut pas être retiré).

### 3. Opportunités d'Investissement IA

#### Analyser les opportunités
```bash
curl -X POST "http://localhost:8000/portfolio/opportunities/analyze"
```

**Réponse:**
```json
{
    "has_opportunities": true,
    "cash_available": 3200.0,
    "cash_ratio": 64.0,
    "portfolio_size": 2,
    "total_value": 5000.0,
    "opportunities": [
        {
            "type": "DIVERSIFY",
            "priority": "HIGH",
            "reasoning": "Vous avez 2 position(s). Recommandation: diversifier avec 5-8 positions différentes.",
            "suggested_amount": 960.0,
            "action": "Rechercher de nouvelles opportunités dans des secteurs différents"
        },
        {
            "type": "REBALANCE_CASH",
            "priority": "MEDIUM",
            "reasoning": "Vous avez 64.0% de cash non investi. Recommandation: investir progressivement pour optimiser le rendement.",
            "suggested_amount": 1600.0,
            "action": "Investir 50% du cash disponible dans des opportunités diversifiées"
        }
    ]
}
```

**Types d'opportunités détectées:**

1. **DIVERSIFY** (Priorité: HIGH)
   - Condition: < 5 positions dans le portfolio
   - Suggestion: Ajouter 2-3 nouvelles positions
   - Montant: 30% du cash ou 1000€ max

2. **ADD_TO_EXISTING** (Priorité: MEDIUM)
   - Condition: Position performante (+5%) ET poids < 20%
   - Suggestion: Renforcer la position gagnante
   - Inclut: ticker, company_name, quantité suggérée

3. **REBALANCE_CASH** (Priorité: MEDIUM)
   - Condition: Ratio de cash > 30%
   - Suggestion: Investir 50% du cash progressivement

#### Voir les opportunités en attente
```bash
curl "http://localhost:8000/portfolio/opportunities/pending"
```

#### Créer une opportunité manuellement
```bash
curl -X POST "http://localhost:8000/portfolio/opportunities/create" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "recommendation_type": "ADD_TO_EXISTING",
    "suggested_amount": 1500.0,
    "reasoning": "Position performante à renforcer",
    "confidence_score": 0.85,
    "risk_level": "LOW",
    "expires_in_days": 7
  }'
```

#### Accepter une opportunité
```bash
# Accepter avec les paramètres suggérés
curl -X POST "http://localhost:8000/portfolio/opportunities/123/accept"

# Accepter avec des paramètres personnalisés
curl -X POST "http://localhost:8000/portfolio/opportunities/123/accept?actual_quantity=3&actual_price=750.5"
```

**Comportement:**
1. ✅ Récupère les infos de l'opportunité
2. ✅ Obtient le prix du marché (si non fourni)
3. ✅ Exécute automatiquement l'achat via `add_position()`
4. ✅ Le cash est déduit automatiquement
5. ✅ Marque l'opportunité comme 'ACCEPTED'

#### Rejeter une opportunité
```bash
curl -X POST "http://localhost:8000/portfolio/opportunities/123/reject" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Préfère attendre une baisse du prix"
  }'
```

### 4. Résumé du Portfolio

#### Voir le portfolio complet
```bash
curl "http://localhost:8000/portfolio"
```

**Réponse enrichie:**
```json
{
    "total_positions": 3,
    "total_value": 4500.0,
    "total_invested": 4200.0,
    "total_gain_loss": 300.0,
    "total_gain_loss_percent": 7.14,

    "pea_treasury": {
        "total_deposits": 10000.0,
        "cash_available": 5200.0,
        "cash_invested": 4500.0,
        "pea_total_value": 9700.0,
        "pea_gain_loss": -300.0,
        "pea_gain_loss_percent": -3.0,
        "pea_opening_date": "2026-02-04",
        "last_deposit_date": "2026-02-04"
    },

    "cash_ratio": 53.6,
    "investment_ratio": 46.4,

    "positions": [...]
}
```

**Nouveaux champs:**
- `pea_treasury`: Toutes les infos de trésorerie PEA
- `pea_total_value`: Valeur totale (cash + positions)
- `pea_gain_loss`: Performance globale du PEA
- `cash_ratio`: % de cash non investi
- `investment_ratio`: % investi en actions

## Scénarios d'utilisation

### Scénario 1: Premier dépôt et premier achat

```bash
# 1. Déposer 10 000€
curl -X POST "http://localhost:8000/portfolio/deposit?amount=10000&notes=Ouverture_PEA"

# 2. Vérifier la trésorerie
curl "http://localhost:8000/portfolio/treasury"
# → cash_available: 10000€

# 3. Acheter 10 actions LVMH à 750€
curl -X POST "http://localhost:8000/portfolio/add" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "MC.PA", "company_name": "LVMH", "quantity": 10, "price": 750.0}'

# 4. Vérifier que le cash a été déduit
curl "http://localhost:8000/portfolio/treasury"
# → cash_available: 2500€ (10000 - 7500)
# → cash_invested: 7500€
```

### Scénario 2: Vente et réinvestissement

```bash
# 1. Vendre 5 actions LVMH à 800€
curl -X POST "http://localhost:8000/portfolio/sell" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "MC.PA", "quantity": 5, "price": 800.0}'

# 2. Vérifier le cash récupéré
curl "http://localhost:8000/portfolio/treasury"
# → cash_available: 6500€ (2500 + 4000)

# 3. Analyser les opportunités
curl -X POST "http://localhost:8000/portfolio/opportunities/analyze"
# → Suggestions basées sur 6500€ disponible

# 4. Acheter une nouvelle position
curl -X POST "http://localhost:8000/portfolio/add" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "OR.PA", "company_name": "L Oreal", "quantity": 20, "price": 400.0}'
```

### Scénario 3: Utilisation des opportunités IA

```bash
# 1. Analyser les opportunités
RESPONSE=$(curl -s -X POST "http://localhost:8000/portfolio/opportunities/analyze")
echo $RESPONSE | python3 -m json.tool

# 2. Si has_opportunities = true, l'IA suggère des actions

# 3. Créer une opportunité personnalisée
curl -X POST "http://localhost:8000/portfolio/opportunities/create" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AI.PA",
    "company_name": "Air Liquide",
    "recommendation_type": "NEW_POSITION",
    "suggested_amount": 2000.0,
    "reasoning": "Secteur défensif intéressant",
    "confidence_score": 0.75,
    "risk_level": "LOW"
  }'

# 4. Lister les opportunités en attente
curl "http://localhost:8000/portfolio/opportunities/pending"

# 5. Accepter l'opportunité 123
curl -X POST "http://localhost:8000/portfolio/opportunities/123/accept"
# → Achat automatique exécuté, cash déduit
```

## Intégration avec l'IA

Le système s'intègre parfaitement avec l'IA via `get_portfolio_context_for_ai()`:

```python
from services.portfolio_manager import PortfolioManager

pm = PortfolioManager()
context = pm.get_portfolio_context_for_ai()

# Context inclut maintenant:
# - État de la trésorerie PEA
# - Cash disponible et ratio
# - Opportunités automatiques si cash > 100€
# - Performance globale du PEA

# L'IA peut utiliser ce contexte pour:
# - Suggérer des achats
# - Recommander un rééquilibrage
# - Analyser la diversification
# - Détecter des opportunités
```

## Points d'attention

### Règles PEA importantes
1. **Pas de retrait:** L'argent déposé ne peut jamais être retiré du PEA
2. **Plafond:** Maximum 150 000€ de versements
3. **Cash stagant:** L'argent non investi ne rapporte rien, d'où les suggestions IA

### Sécurité et intégrité
1. **Vérification du cash:** Impossible d'acheter sans cash suffisant
2. **Audit trail:** Tous les mouvements sont tracés dans `cash_flow_events`
3. **Calculs automatiques:** `cash_invested` recalculé depuis les positions

### Erreurs courantes

**Erreur: "Aucune trésorerie PEA trouvée"**
```json
{"detail": "Aucune trésorerie PEA trouvée pour default_user. Effectuez un dépôt d'abord avec /portfolio/deposit"}
```
→ Solution: Déposer de l'argent d'abord

**Erreur: "Cash insuffisant"**
```json
{"detail": "Cash insuffisant. Disponible: 1000.00€, Requis: 5000.00€"}
```
→ Solution: Déposer plus d'argent ou réduire la quantité

**Erreur: "Position non trouvée"**
```json
{"detail": "Position AAPL.PA non trouvée pour user default_user"}
```
→ Solution: Vérifier le ticker ou ajouter la position d'abord

## Résumé des Endpoints

### Trésorerie
- `POST /portfolio/deposit` - Déposer de l'argent
- `GET /portfolio/treasury` - État de la trésorerie
- `GET /portfolio/treasury/deposits` - Historique des dépôts
- `GET /portfolio/treasury/cashflow` - Flux de trésorerie

### Opportunités
- `POST /portfolio/opportunities/analyze` - Analyser et générer
- `GET /portfolio/opportunities/pending` - Lister en attente
- `POST /portfolio/opportunities/create` - Créer manuellement
- `POST /portfolio/opportunities/{id}/accept` - Accepter et exécuter
- `POST /portfolio/opportunities/{id}/reject` - Rejeter
- `GET /portfolio/opportunities/{id}` - Détails

### Portfolio (existants, modifiés)
- `POST /portfolio/add` - Acheter (déduit le cash automatiquement)
- `POST /portfolio/sell` - Vendre (ajoute le cash automatiquement)
- `GET /portfolio` - Résumé (inclut maintenant pea_treasury)

## Support et Debugging

### Vérifier l'intégrité des données
```bash
# Vérifier la cohérence: total_deposits >= cash_available + cash_invested
curl "http://localhost:8000/portfolio/treasury"

# Voir tous les flux de cash
curl "http://localhost:8000/portfolio/treasury/cashflow?limit=100"

# Vérifier les positions
curl "http://localhost:8000/portfolio"
```

### Réinitialiser (development seulement)
```bash
# Supprimer la base de données
rm data/portfolio.db

# Relancer l'API - les tables seront recréées
```

## Conclusion

Le système de trésorerie PEA offre une gestion complète et automatisée:
- ✅ Suivi précis du cash disponible et investi
- ✅ Déduction/ajout automatique lors des transactions
- ✅ Suggestions IA basées sur le cash disponible
- ✅ Audit trail complet de tous les mouvements
- ✅ Intégration transparente avec le portfolio existant

Pour toute question, consultez la documentation complète dans `INTEGRATION_PEA_PORTFOLIO_MANAGER.md`.
