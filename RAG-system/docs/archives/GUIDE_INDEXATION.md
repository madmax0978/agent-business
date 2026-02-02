# 📚 Guide d'Indexation de Documents - 79 Rapports

## ⏱️ Estimation pour vos 79 documents

Vos documents totalisent environ **750 MB**. Voici l'estimation :

- **Temps total estimé** : 6-8 heures
- **Moyenne par document** : 5-10 minutes
- **Gros documents (500 pages)** : 15-20 minutes chacun

## 🚀 Méthode Recommandée : Indexation Batch Progressive

### Étape 1 : Lancer l'API (Terminal 1)

```bash
cd api
python -m uvicorn main:app --reload
```

Laissez ce terminal ouvert pendant toute l'indexation.

### Étape 2 : Lancer l'indexation batch (Terminal 2)

```bash
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system

# Indexer tous les documents
python batch_index_documents.py data/context/
```

**Le script va :**
1. ✅ Afficher un résumé des 79 documents
2. ✅ Calculer le temps estimé
3. ✅ Demander confirmation avant de démarrer
4. ✅ Traiter chaque document un par un
5. ✅ Sauvegarder la progression après chaque document
6. ✅ Continuer même si un document échoue
7. ✅ Générer un rapport complet à la fin

### Étape 3 : Suivre la progression

La progression est affichée en temps réel :

```
================================================================================
📄 Document 15/79 (19.0%)
================================================================================
📄 Indexation: Capgemini_-_2024-03-29_-_Document_d_Enregistrement_Universel_2023.pdf
   Taille: 13.2 MB
   Timeout: 396s (~6min)
   Collection: capgemini_2024_03_29_document_d_enregistrement_universel_2023

✅ Succès! Chunks: 1245 (Tables: 687, Texte: 558)

📊 Progression: 15/79 documents
   ✅ Succès: 15
   ❌ Échecs: 0
   📈 Taux de réussite: 100.0%
   ⏱️  Temps écoulé: 384.2s
   🔄 Restants: 64 documents
```

## 🛑 Interruption et Reprise

### Si vous devez arrêter (Ctrl+C)

```bash
# Interrompez avec Ctrl+C
^C
⚠️  Interruption par l'utilisateur (Ctrl+C)
💾 Progression sauvegardée!
🔄 Relancez la même commande pour reprendre l'indexation
```

### Pour reprendre

```bash
# Relancez simplement la même commande
python batch_index_documents.py data/context/

# Les documents déjà traités seront automatiquement ignorés
```

## 📊 Fichiers de Suivi

### `indexing_progress.json`

```json
{
  "processed": [
    {
      "file": "lvmh_rapport_2024.pdf",
      "collection": "lvmh_rapport_2024",
      "chunks": 402,
      "timestamp": "2026-01-19T18:30:00",
      "processing_time": 245.3
    }
  ],
  "failed": []
}
```

### `indexing_log.txt`

```
[2026-01-19 18:30:00] [INFO] 🚀 INDEXATION BATCH DE DOCUMENTS
[2026-01-19 18:30:05] [INFO] 📄 Document 1/79 (1.3%)
[2026-01-19 18:30:10] [SUCCESS] ✅ Succès! Chunks: 402
```

## 🎯 Stratégies d'Indexation

### Option 1 : Tout indexer d'un coup (Recommandé)

```bash
# Lancez et laissez tourner toute la nuit
python batch_index_documents.py data/context/

# Avantage : Automatique, tout est fait le lendemain
# Temps : 6-8 heures
```

### Option 2 : Par petits lots

```bash
# Jour 1 : Les 20 premiers documents
python batch_index_documents.py data/context/ --max 20

# Jour 2 : Les 20 suivants (seront automatiquement détectés)
python batch_index_documents.py data/context/ --max 40

# Jour 3 : Les 20 suivants
python batch_index_documents.py data/context/ --max 60

# Jour 4 : Le reste
python batch_index_documents.py data/context/
```

### Option 3 : Test puis full

```bash
# 1. Tester avec 3 documents
python batch_index_documents.py data/context/ --max 3

# 2. Vérifier que tout fonctionne
python add_document.py list

# 3. Lancer le reste
python batch_index_documents.py data/context/
```

## 💡 Conseils pour l'Indexation Longue Durée

### 1. Lancer en arrière-plan

```bash
# Utiliser nohup pour que ça continue même si vous fermez le terminal
nohup python batch_index_documents.py data/context/ > indexing_output.log 2>&1 &

# Suivre la progression
tail -f indexing_log.txt
```

### 2. Utiliser screen ou tmux

```bash
# Créer une session screen
screen -S indexation

# Lancer l'indexation
python batch_index_documents.py data/context/

# Détacher avec Ctrl+A puis D
# Rattacher plus tard avec: screen -r indexation
```

### 3. Optimiser les performances

```bash
# Augmenter la mémoire Python si nécessaire
PYTHONUNBUFFERED=1 python batch_index_documents.py data/context/
```

## 🔍 Vérification Post-Indexation

### Lister tous les documents indexés

```bash
python add_document.py list
```

### Tester une collection

```bash
# Via l'API
curl "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quel est le chiffre d'\''affaires?",
    "collection_name": "lvmh_rapport_2024",
    "n_results": 3
  }'
```

## ⚠️ Gestion des Problèmes

### Problème : Un document échoue systématiquement

```bash
# Le script continue automatiquement avec les autres
# Consultez le log pour voir l'erreur
cat indexing_log.txt | grep ERROR
```

### Problème : L'API crashe

```bash
# Relancez l'API
cd api
python -m uvicorn main:app --reload

# Reprenez l'indexation (la progression est sauvegardée)
cd ..
python batch_index_documents.py data/context/
```

### Problème : Manque de mémoire

```bash
# Redémarrez l'API entre deux lots
# Option 1 : Par lots de 20
python batch_index_documents.py data/context/ --max 20

# Redémarrez l'API
# Ctrl+C dans le terminal de l'API
# cd api && python -m uvicorn main:app --reload

# Continuez
python batch_index_documents.py data/context/ --max 40
```

## 📈 Résultat Attendu

À la fin, vous aurez :

```
✅ 79 collections indexées dans ChromaDB
✅ Environ 30,000 - 50,000 chunks au total
✅ Recherche sémantique disponible sur tous les documents
✅ Prêt pour les analyses CrewAI
```

## 🎉 Après l'Indexation

### 1. Tester l'analyse complète

```bash
cd api/agents
python portfolio_builder_crew.py 10000 balanced
```

Le système utilisera automatiquement tous vos documents !

### 2. Requêtes RAG personnalisées

```python
from agents.tools import create_rag_tool

rag_tool = create_rag_tool()
result = rag_tool._run(
    question="Compare les performances de LVMH et Hermès",
    collection_name="lvmh_rapport_2024"
)
print(result)
```

## ⏰ Planning Recommandé

### Scénario : Indexation de nuit

```bash
# 18h00 : Démarrer l'API
cd api && python -m uvicorn main:app --reload

# 18h05 : Lancer l'indexation batch
cd .. && nohup python batch_index_documents.py data/context/ > indexing.log 2>&1 &

# Le lendemain matin (8h00) : Tout est prêt ! ✅
```

---

**Bon courage pour l'indexation ! 📚✨**
