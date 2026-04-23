"""
LLM client abstraction.

Two implementations:
  - OpenAIClient: uses the OpenAI API (production)
  - MockLLMClient: returns deterministic strings (testing / offline)

Switch via USE_MOCK_LLM=true in .env or config/settings.py.
"""

from __future__ import annotations
from typing import Protocol

from config.settings import get_settings

_MOCK_RESPONSES: dict[str, str] = {
    "rapport": (
        "## Rapport de qualité de l'air\n\n"
        "Au cours de la période analysée, trois zones ont dépassé le seuil PM2.5 "
        "de 25 µg/m³. La Médina et la Zone Industrielle concentrent les pics les plus "
        "fréquents, avec des dépassements surtout en début de matinée et en fin de journée.\n\n"
        "### Points clés\n"
        "- Les capteurs de qualité de l'air restent globalement stables.\n"
        "- Les zones à fort trafic montrent une hausse régulière des particules fines.\n"
        "- Une intervention préventive est recommandée sur les capteurs les plus sollicités."
    ),
    "action": (
        '{"actions": [{"priorite": 1, "titre": "Maintenance capteur C-12", '
        '"urgence": "HAUTE", "detail": "Taux d\'erreur 18% sur les mesures PM2.5.", '
        '"description": "Inspection et recalibrage immédiats du capteur C-12.", '
        '"responsable": "technicien", "delai_heures": 2, '
        '"impact": "Restauration de la couverture de surveillance sur la zone Nord."}], '
        '"resume": "Deux capteurs nécessitent une intervention immédiate.", '
        '"niveau_urgence": "ORANGE"}'
    ),
    "sql": (
        "Cette requête retourne les zones dont la concentration moyenne en PM2.5 "
        "dépasse le seuil réglementaire."
    ),
    "validation": (
        '{"approved": true, "confidence": 0.93, '
        '"reason": "Les rapports techniques sont cohérents et la clôture est justifiée."}'
    ),
    "clarification": "Souhaitez-vous toutes les mesures ou uniquement les PM2.5 ?",
    "default": "Rapport généré automatiquement par le module IA de Neo-Sousse 2030.",
}


class LLMClient(Protocol):
    def complete(self, prompt: str, max_tokens: int = 1500) -> str: ...


class OpenAIClient:
    def __init__(self):
        import openai
        settings = get_settings()
        self._client = openai.OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    def complete(self, prompt: str, max_tokens: int = 1500) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content or ""


class MockLLMClient:
    """Returns canned responses for testing without API calls."""

    def complete(self, prompt: str, max_tokens: int = 1500) -> str:
        prompt_lower = prompt.lower()
        matchers = (
            ("clarification", ("clarification", "ambiguïté", "ambiguite")),
            ("validation", ("json strict", "approved", "validation ia", "intervention peut être validée")),
            ("action", ("actions", "action", "prioritaires", "recommandations")),
            ("sql", ("sql", "requête", "traduis cette requête")),
            ("rapport", ("rapport", "résumé", "qualité", "capteurs", "interventions")),
        )
        for key, keywords in matchers:
            if any(keyword in prompt_lower for keyword in keywords):
                return _MOCK_RESPONSES[key]
        return _MOCK_RESPONSES["default"]


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.use_mock_llm or not settings.openai_api_key:
        return MockLLMClient()
    return OpenAIClient()
