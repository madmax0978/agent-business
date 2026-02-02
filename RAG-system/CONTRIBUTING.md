# Guide de Contribution - RAG-PEA

Merci de votre intérêt pour contribuer au projet RAG-PEA ! Ce guide vous aidera à démarrer.

---

## Table des Matières

- [Code of Conduct](#code-of-conduct)
- [Comment Contribuer](#comment-contribuer)
- [Setup Environnement Développement](#setup-environnement-développement)
- [Standards de Code](#standards-de-code)
- [Workflow Git](#workflow-git)
- [Tests](#tests)
- [Documentation](#documentation)
- [Code Review](#code-review)

---

## Code of Conduct

- Soyez respectueux et professionnel
- Accueillez les nouveaux contributeurs
- Concentrez-vous sur le code, pas sur la personne
- Acceptez les critiques constructives

---

## Comment Contribuer

### Types de contributions acceptées

- **Bug fixes** - Correction de bugs
- **Features** - Nouvelles fonctionnalités
- **Documentation** - Amélioration docs
- **Tests** - Ajout/amélioration tests
- **Performance** - Optimisations
- **Refactoring** - Nettoyage code

### Workflow contribution

1. **Fork** le repository
2. **Clone** votre fork
3. **Créer** une branche feature
4. **Développer** avec tests
5. **Commit** avec messages clairs
6. **Push** vers votre fork
7. **Ouvrir** une Pull Request

---

## Setup Environnement Développement

### Prérequis

```bash
# Python 3.9+
python --version

# Git
git --version

# Ollama (optionnel)
ollama --version
```

### Installation

```bash
# 1. Fork et clone
git clone https://github.com/VOTRE_USERNAME/RAG-system.git
cd RAG-system

# 2. Créer virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows

# 3. Installer dépendances dev
pip install -r requirements.txt
pip install pytest pytest-cov black isort mypy flake8

# 4. Configurer .env
cp .env.example .env
# Éditer .env avec vos clés API

# 5. Vérifier installation
python -c "from api.config import settings; print('OK')"

# 6. Lancer tests
pytest tests/ -v

# 7. Démarrer API
uvicorn api.main:app --reload
```

### Configuration IDE

**VS Code (recommandé):**

`.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

**PyCharm:**
- Configurer Black comme formatter
- Activer pytest comme test runner
- Configurer flake8 pour linting

---

## Standards de Code

### Style Guide - PEP 8

```python
# ✅ Bon style
def calculate_portfolio_health_score(
    positions: List[Dict],
    total_value: float,
    user_id: str = "default_user"
) -> Dict[str, Any]:
    """
    Calcule le score de santé du portefeuille (0-100).

    Args:
        positions: Liste des positions du portefeuille
        total_value: Valeur totale du portefeuille en EUR
        user_id: Identifiant utilisateur

    Returns:
        Dict avec score, grade, issues et recommendations
    """
    score = 100

    # Vérifier diversification
    num_positions = len(positions)
    if num_positions < 3:
        score -= 30

    return {
        "score": score,
        "grade": _calculate_grade(score),
        "num_positions": num_positions
    }


# ❌ Mauvais style
def calc_score(pos,val):  # Noms courts, pas de types
    s=100  # Variable 1 lettre
    if len(pos)<3:s-=30  # Pas d'espaces
    return {"score":s}  # Pas de docstring
```

### Type Hints

**Obligatoires** pour toutes fonctions publiques:

```python
from typing import List, Dict, Optional, Union

def get_stock_info(ticker: str) -> Optional[Dict[str, Any]]:
    """Type hints pour paramètres ET return"""
    ...

def process_data(
    data: List[Dict],
    filter_func: Optional[Callable[[Dict], bool]] = None,
    max_results: int = 100
) -> Union[List[Dict], None]:
    """Types complexes supportés"""
    ...
```

### Docstrings - Google Style

**Format requis:**

```python
def function_name(param1: type1, param2: type2) -> return_type:
    """Brief description en une ligne.

    Longer description explaining the function's purpose,
    behavior, and any important details.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.

    Returns:
        Description of return value.

    Raises:
        ErrorType: When this error occurs.

    Example:
        >>> function_name("value1", 42)
        expected_output
    """
```

**Pour classes:**

```python
class PortfolioManager:
    """Gestionnaire de portefeuille avec analyse IA.

    Cette classe fournit des méthodes pour:
    - Calculer le score de santé du portefeuille
    - Détecter besoins de rééquilibrage
    - Générer contexte pour LLM

    Attributes:
        db: Instance PortfolioDatabase
        yf: Instance YahooFinanceService

    Example:
        >>> manager = PortfolioManager()
        >>> health = manager.get_portfolio_health_score("user123")
        >>> print(health['score'])
        85
    """

    def __init__(self):
        """Initialise le PortfolioManager avec DB et YF service."""
        self.db = PortfolioDatabase()
        self.yf = YahooFinanceService()
```

### Imports

**Ordre (utilisez isort):**

```python
# 1. Standard library
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 2. Third-party
import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 3. Local
from api.config import settings
from api.exceptions import PortfolioError
from api.services.yahoo_finance_service import YahooFinanceService
```

**Formatage automatique:**

```bash
# isort pour organiser imports
isort api/services/portfolio_manager.py

# black pour formatter code
black api/services/portfolio_manager.py

# OU les deux
isort . && black .
```

### Naming Conventions

```python
# Modules: lowercase_with_underscores
# portfolio_manager.py, yahoo_finance_service.py

# Classes: CapitalizedWords
class PortfolioManager:
class YahooFinanceService:

# Functions/methods: lowercase_with_underscores
def calculate_health_score():
def get_stock_info():

# Constants: UPPERCASE_WITH_UNDERSCORES
MAX_POSITIONS = 20
DEFAULT_CACHE_TTL = 300

# Private: _leading_underscore
def _internal_helper():
    _private_var = 42
```

### Error Handling

**Utilisez exceptions personnalisées:**

```python
from api.exceptions import (
    PortfolioError,
    PositionNotFoundError,
    InsufficientQuantityError,
    raise_for_status
)

def sell_position(ticker: str, quantity: float):
    """Vend une position avec gestion d'erreurs."""

    position = get_position(ticker)

    # ✅ Bon: exception spécifique
    raise_for_status(
        position is not None,
        PositionNotFoundError(ticker, user_id)
    )

    # ✅ Bon: validation claire
    if position['quantity'] < quantity:
        raise InsufficientQuantityError(
            ticker,
            available=position['quantity'],
            requested=quantity
        )

    # ❌ Mauvais: exception générique
    if not position:
        raise Exception("Position not found")
```

### Logging

**Utilisez le logger structuré:**

```python
from api.logging_config import get_logger, log_exception, log_performance

logger = get_logger(__name__)

def process_data(data: List[Dict]) -> List[Dict]:
    """Process data avec logging approprié."""

    logger.info(f"Processing {len(data)} items")

    try:
        start_time = time.time()

        # Processing logic
        result = expensive_operation(data)

        # Log success avec métriques
        duration_ms = (time.time() - start_time) * 1000
        log_performance(
            logger,
            "process_data",
            duration_ms,
            success=True,
            items_processed=len(result)
        )

        return result

    except Exception as e:
        # Log exception avec contexte
        log_exception(
            logger,
            e,
            "Failed to process data",
            data_size=len(data)
        )
        raise
```

---

## Workflow Git

### Branches

**Structure:**

```
main                    # Production (protégée)
├── develop            # Development (intégration)
    ├── feature/add-crypto-support
    ├── feature/improve-rag-search
    ├── bugfix/fix-portfolio-calculation
    └── hotfix/critical-security-issue
```

**Convention nommage:**

```bash
feature/courte-description   # Nouvelle feature
bugfix/courte-description    # Correction bug
hotfix/courte-description    # Fix critique production
refactor/courte-description  # Refactoring
docs/courte-description      # Documentation
```

### Commits

**Format (Conventional Commits):**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: Nouvelle feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting, missing semi colons, etc
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Exemples:**

```bash
# Feature
git commit -m "feat(portfolio): add crypto portfolio support

- Add crypto_portfolio_manager.py
- Support Bitcoin, Ethereum, top 20 coins
- Integrate CoinGecko API for pricing
- Add tests for crypto calculations"

# Bug fix
git commit -m "fix(rag): correct chunk overlap calculation

Fixed bug where chunk overlap was not applied correctly,
causing loss of context between chunks.

Closes #123"

# Documentation
git commit -m "docs(api): add API reference documentation

Complete API documentation with:
- All 23 endpoints documented
- Request/response examples
- Error codes explained"
```

### Pull Requests

**Template PR:**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings

## Testing
Describe how to test changes

## Screenshots (if applicable)
```

**Bonnes pratiques PR:**

1. **Keep PR small** - Max 400 lignes changées
2. **One concern per PR** - Une feature/fix par PR
3. **Clear title** - Titre descriptif
4. **Description complète** - Expliquer POURQUOI, pas juste QUOI
5. **Link issues** - Référencer issues concernées
6. **Request reviewers** - Demander review à 1-2 personnes
7. **Respond to feedback** - Répondre aux commentaires rapidement

---

## Tests

### Requis pour PR

**Minimum:**
- [ ] Tests unitaires pour nouvelle feature
- [ ] Tests d'intégration si modifie API
- [ ] Tous tests existants passent
- [ ] Coverage >= 80% sur code modifié

### Écrire tests

**Structure test:**

```python
def test_feature_name():
    """
    Test description claire

    Given: Initial context
    When: Action performed
    Then: Expected result
    """
    # Arrange
    input_data = prepare_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
    assert result.some_field == expected_value
```

**Utiliser fixtures:**

```python
import pytest

@pytest.fixture
def sample_portfolio():
    """Fixture réutilisable"""
    return {
        "positions": [
            {"ticker": "MC.PA", "quantity": 10, "price": 700}
        ]
    }

def test_with_fixture(sample_portfolio):
    """Test utilisant fixture"""
    result = calculate_value(sample_portfolio)
    assert result > 0
```

**Mock services externes:**

```python
from unittest.mock import patch, Mock

def test_with_mock():
    """Test avec Yahoo Finance mocké"""

    mock_response = {"current_price": 750.30}

    with patch('api.services.yahoo_finance_service.YahooFinanceService.get_stock_info') as mock:
        mock.return_value = mock_response

        result = get_position_value("MC.PA")

        assert result == 750.30
        mock.assert_called_once_with("MC.PA")
```

### Lancer tests avant PR

```bash
# Tous tests
./run_tests.sh

# Tests rapides
./run_tests.sh quick

# Avec coverage
./run_tests.sh coverage

# Vérifier coverage >= 80%
pytest tests/ --cov=api --cov-fail-under=80
```

---

## Documentation

### Quand documenter

**Obligatoire:**
- Toutes fonctions/méthodes publiques
- Toutes classes
- Modules (docstring module)
- Nouvelles features (README, ARCHITECTURE.md)
- Breaking changes (CHANGELOG.md)

**Optionnel mais recommandé:**
- Fonctions privées complexes
- Algorithmes non triviaux
- Workarounds temporaires

### Où documenter

```
Code → Docstrings (Google style)
API → Endpoint descriptions (FastAPI)
Architecture → ARCHITECTURE.md
Usage → README.md
Troubleshooting → TROUBLESHOOTING.md
Changes → CHANGELOG.md
```

### Mise à jour docs

**Checklist:**

- [ ] Docstrings à jour
- [ ] README.md mis à jour si nouvelle feature
- [ ] ARCHITECTURE.md mis à jour si changement archi
- [ ] API_REFERENCE.md mis à jour si nouveau endpoint
- [ ] CHANGELOG.md entry ajoutée

---

## Code Review

### Pour reviewers

**Que vérifier:**

1. **Correctness** - Code fait ce qu'il dit?
2. **Tests** - Tests passent? Coverage OK?
3. **Design** - Architecture cohérente?
4. **Readability** - Code lisible et maintenable?
5. **Performance** - Pas de bottlenecks évidents?
6. **Security** - Pas de failles de sécurité?
7. **Documentation** - Docs à jour?

**Comment reviewer:**

```markdown
# ✅ Bon feedback
"Cette fonction pourrait bénéficier d'un try/except pour gérer
les cas où Yahoo Finance est indisponible. Suggérer de retourner
des données cachées en fallback."

# ❌ Mauvais feedback
"Ce code est nul."
```

**Process review:**

1. Lire description PR
2. Vérifier tests passent
3. Review code fichier par fichier
4. Tester localement si possible
5. Laisser commentaires constructifs
6. Approuver ou demander changements

### Pour auteurs PR

**Répondre aux commentaires:**

```markdown
# Bon: Expliquer ou corriger
"Bonne suggestion! J'ai ajouté le try/except dans commit abc123."

# OU
"J'ai pensé à ça mais décidé de ne pas le faire car [raison].
Qu'en pensez-vous?"

# Mauvais: Ignorer ou être défensif
"Non, mon code est bon."
```

**Après review:**

1. Répondre à TOUS les commentaires
2. Faire changements demandés OU expliquer pourquoi pas
3. Push nouveaux commits
4. Re-request review si changements majeurs
5. Merger quand approuvé

---

## Checklist PR Finale

Avant de soumettre PR:

**Code:**
- [ ] Code suit style guide (black, isort, flake8)
- [ ] Type hints complets
- [ ] Docstrings Google style
- [ ] Pas de code commenté/dead code
- [ ] Pas de print() debug (utiliser logger)
- [ ] Pas de secrets hardcodés

**Tests:**
- [ ] Tests unitaires écrits
- [ ] Tests d'intégration si API modifiée
- [ ] Tous tests passent (`./run_tests.sh`)
- [ ] Coverage >= 80% sur nouveau code

**Documentation:**
- [ ] Docstrings à jour
- [ ] README.md mis à jour si feature visible
- [ ] CHANGELOG.md entry
- [ ] ARCHITECTURE.md si changement archi

**Git:**
- [ ] Branch à jour avec main/develop
- [ ] Commits clean (squash si nécessaire)
- [ ] Messages commits clairs
- [ ] PR title descriptif
- [ ] PR description complète

---

## Questions?

**Besoin d'aide?**
- Ouvrir une issue avec tag `question`
- Rejoindre discussions GitHub
- Consulter docs existantes

**Suggestions?**
- Issues avec tag `enhancement`
- Discussions pour idées

Merci de contribuer à RAG-PEA! 🚀

---

**Document version:** 1.0.0
**Dernière mise à jour:** Février 2026
