#!/bin/bash
# Script de démarrage de l'API RAG

echo "═══════════════════════════════════════════"
echo "    Démarrage de l'API RAG Multi-Documents"
echo "═══════════════════════════════════════════"
echo ""

# Vérifier si Ollama est lancé
echo "Vérification d'Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama n'est pas lancé. Démarrez-le avec: ollama serve"
    echo ""
fi

# Aller dans le dossier api
cd "$(dirname "$0")/api"

# Lancer l'API
echo "Démarrage de l'API sur http://localhost:8000"
echo "Documentation disponible sur http://localhost:8000/docs"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
