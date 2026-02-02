#!/bin/bash

# Script pour exécuter la suite de tests RAG-PEA
# Usage: ./run_tests.sh [options]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         RAG-PEA SYSTEM - SUITE DE TESTS COMPLÈTE             ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "tests" ]; then
    echo -e "${RED}❌ Erreur: Répertoire 'tests' non trouvé${NC}"
    echo -e "${YELLOW}   Exécutez ce script depuis la racine du projet RAG-system${NC}"
    exit 1
fi

# Vérifier que pytest est installé
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest n'est pas installé${NC}"
    echo -e "${YELLOW}   Installez-le avec: pip install pytest requests${NC}"
    exit 1
fi

# Vérifier que l'API est accessible
echo -e "${YELLOW}🔍 Vérification de l'API...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API accessible sur http://localhost:8000${NC}"
else
    echo -e "${RED}❌ API non accessible${NC}"
    echo -e "${YELLOW}   Lancez l'API avec: uvicorn api.main:app --reload${NC}"
    exit 1
fi

# Vérifier Ollama (optionnel)
echo -e "${YELLOW}🔍 Vérification Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama disponible${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama non accessible (certains tests seront skippés)${NC}"
    echo -e "${YELLOW}   Lancez Ollama avec: ollama serve${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Déterminer quels tests exécuter
TEST_SELECTION="tests/"
PYTEST_ARGS="-v"

if [ "$1" == "quick" ]; then
    echo -e "${YELLOW}Mode: Tests rapides (sans tests lents)${NC}"
    PYTEST_ARGS="-v -m 'not slow'"
elif [ "$1" == "rag" ]; then
    echo -e "${YELLOW}Mode: Tests RAG uniquement${NC}"
    TEST_SELECTION="tests/test_rag_workflow.py"
elif [ "$1" == "financial" ]; then
    echo -e "${YELLOW}Mode: Tests analyses financières uniquement${NC}"
    TEST_SELECTION="tests/test_financial_analysis.py"
elif [ "$1" == "portfolio" ]; then
    echo -e "${YELLOW}Mode: Tests portefeuille uniquement${NC}"
    TEST_SELECTION="tests/test_portfolio.py"
elif [ "$1" == "integration" ]; then
    echo -e "${YELLOW}Mode: Tests intégration end-to-end${NC}"
    TEST_SELECTION="tests/test_integration.py"
elif [ "$1" == "coverage" ]; then
    echo -e "${YELLOW}Mode: Tests avec couverture de code${NC}"
    PYTEST_ARGS="-v --cov=api --cov-report=html --cov-report=term"
elif [ "$1" == "help" ] || [ "$1" == "-h" ]; then
    echo "Usage: ./run_tests.sh [mode]"
    echo ""
    echo "Modes disponibles:"
    echo "  (aucun)        - Tous les tests"
    echo "  quick          - Tests rapides uniquement"
    echo "  rag            - Tests RAG uniquement"
    echo "  financial      - Tests analyses financières"
    echo "  portfolio      - Tests gestion portefeuille"
    echo "  integration    - Tests end-to-end"
    echo "  coverage       - Tests avec rapport de couverture"
    echo "  help           - Afficher cette aide"
    echo ""
    exit 0
else
    echo -e "${YELLOW}Mode: Tous les tests${NC}"
fi

echo ""

# Exécuter les tests
echo -e "${BLUE}🚀 Lancement des tests...${NC}"
echo ""

pytest $TEST_SELECTION $PYTEST_ARGS

TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ TOUS LES TESTS ONT RÉUSSI${NC}"
else
    echo -e "${RED}❌ CERTAINS TESTS ONT ÉCHOUÉ${NC}"
    echo -e "${YELLOW}   Consultez les détails ci-dessus${NC}"
fi

if [ "$1" == "coverage" ]; then
    echo ""
    echo -e "${BLUE}📊 Rapport de couverture généré: htmlcov/index.html${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

exit $TEST_EXIT_CODE
