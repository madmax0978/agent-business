"""
Outil CrewAI pour l'intégration du système RAG
"""

from crewai_tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import requests


class RAGQueryInput(BaseModel):
    """Input schema pour l'outil RAG"""

    question: str = Field(..., description="Question à poser au système RAG")
    collection_name: str = Field(..., description="Nom de la collection à interroger")
    n_results: int = Field(5, description="Nombre de chunks à récupérer", ge=1, le=20)


class RAGTool(BaseTool):
    """
    Outil CrewAI pour interroger le système RAG
    Permet aux agents CrewAI d'accéder aux documents indexés
    """

    name: str = "RAG Document Query"
    description: str = (
        "Interroge le système RAG pour obtenir des informations depuis des documents indexés. "
        "Utilisez cet outil pour rechercher des informations dans des rapports, documents financiers, "
        "ou tout autre document indexé dans le système. "
        "L'outil retourne les passages les plus pertinents et génère une réponse synthétique."
    )
    args_schema: Type[BaseModel] = RAGQueryInput
    api_url: str = "http://localhost:8000"

    def _run(
        self, question: str, collection_name: str, n_results: int = 5
    ) -> str:
        """
        Exécute une requête RAG

        Args:
            question: Question à poser
            collection_name: Nom de la collection à interroger
            n_results: Nombre de résultats à récupérer

        Returns:
            Réponse générée par le système RAG
        """
        try:
            # Appeler l'API RAG
            response = requests.post(
                f"{self.api_url}/query",
                json={
                    "question": question,
                    "collection_name": collection_name,
                    "n_results": n_results,
                    "generate_answer": True,
                },
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()

                # Construire une réponse structurée
                answer = data.get("answer", "")
                chunks = data.get("chunks", [])

                # Format de réponse pour l'agent
                result = f"**Réponse:** {answer}\n\n"
                result += f"**Sources ({len(chunks)} extraits) :**\n"

                for i, chunk in enumerate(chunks[:3], 1):  # Limiter à 3 sources
                    score = chunk["score"]
                    content_type = chunk["content_type"]
                    text_preview = chunk["text"][:200] + "..."
                    result += f"\n{i}. [Score: {score:.2f} | Type: {content_type}]\n{text_preview}\n"

                return result

            elif response.status_code == 404:
                return f"Erreur: Collection '{collection_name}' non trouvée. Vérifiez que le document a été indexé."

            elif response.status_code == 503:
                return "Erreur: Le service Ollama n'est pas disponible. Assurez-vous qu'Ollama est en cours d'exécution."

            else:
                return f"Erreur lors de la requête RAG: Status {response.status_code}"

        except requests.exceptions.ConnectionError:
            return "Erreur: Impossible de se connecter à l'API RAG. Vérifiez que le serveur est démarré sur http://localhost:8000"

        except requests.exceptions.Timeout:
            return "Erreur: La requête a expiré. Le document est peut-être trop volumineux."

        except Exception as e:
            return f"Erreur inattendue lors de l'appel à l'API RAG: {str(e)}"


# Fonction helper pour créer facilement l'outil
def create_rag_tool(api_url: str = "http://localhost:8000") -> RAGTool:
    """
    Crée une instance de l'outil RAG

    Args:
        api_url: URL de l'API RAG

    Returns:
        Instance de RAGTool prête à être utilisée avec CrewAI

    Example:
        ```python
        from crewai import Agent, Task, Crew
        from api.crewai_tool import create_rag_tool

        # Créer l'outil RAG
        rag_tool = create_rag_tool()

        # Créer un agent qui utilise le RAG
        analyst = Agent(
            role='Financial Analyst',
            goal='Analyze financial reports',
            backstory='Expert in financial analysis',
            tools=[rag_tool],
            verbose=True
        )

        # Créer une tâche
        task = Task(
            description='Analyze LVMH Q1 2025 performance',
            agent=analyst,
            expected_output='Detailed analysis report'
        )

        # Exécuter
        crew = Crew(agents=[analyst], tasks=[task])
        result = crew.kickoff()
        ```
    """
    return RAGTool(api_url=api_url)
