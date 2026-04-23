"""Neo-Sousse 2030 — neon landing page for the Smart City platform."""

import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dashboard.theme import apply_theme

st.set_page_config(
    page_title="Neo-Sousse 2030",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()


def _db_badge() -> str:
    try:
        from database.connection import test_connection

        ok = test_connection()
        return (
            '<span class="ns-tag good">Connectée</span>'
            if ok
            else '<span class="ns-tag bad">Hors ligne</span>'
        )
    except Exception:
        return '<span class="ns-tag idle">Non configurée</span>'


def _card(title: str, body: str) -> str:
    return (
        '<div class="ns-card">'
        f'<div class="ns-card-title">{title}</div>'
        f"<p>{body}</p>"
        "</div>"
    )


with st.sidebar:
    st.markdown("### Neo-Sousse 2030")
    st.markdown(
        """
<div class="ns-card">
  <div class="ns-card-title">Plateforme intelligente</div>
  <p class="ns-subtle">Compilation, automates et IA générative réunis dans une même console opérationnelle.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ns-status-line"><span class="ns-muted">Base de données</span>{_db_badge()}</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("Théorie des Langages et Compilation")
    st.caption("Section IA 2 — 2025/2026")


st.markdown(
    """
<div class="ns-hero">
  <div class="ns-kicker">Neo-Sousse 2030</div>
  <h1>Centre de commandement urbain</h1>
  <p class="ns-subtle">Une interface unique pour compiler des requêtes en français, piloter des automates métier et générer des rapports analytiques dans une esthétique neon à contraste élevé.</p>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown(
        _card(
            "Compilateur NL → SQL",
            "Le pipeline lexer / parser / AST transforme les demandes en français en SQL paramétré, avec diagnostics de syntaxe et de sémantique.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        _card(
            "Automates à états finis",
            "Les cycles de vie des capteurs, interventions et véhicules sont modélisés comme des FSM déterministes persistables et visualisables.",
        ),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        _card(
            "Module IA",
            "Le moteur génératif produit des rapports, propose des actions prioritaires et peut fonctionner en mode mock sans clé API.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        _card(
            "Tableau de bord temps réel",
            "Les pages Streamlit relient les modules entre eux pour exécuter des requêtes, déclencher des transitions et explorer les données opérationnelles.",
        ),
        unsafe_allow_html=True,
    )

st.divider()
st.markdown("## Indicateurs en temps réel")

try:
    from database.connection import execute_query

    metric_specs = [
        ("Capteurs actifs", "SELECT COUNT(*) AS n FROM capteurs WHERE statut='ACTIF'"),
        ("Capteurs hors service", "SELECT COUNT(*) AS n FROM capteurs WHERE statut='HORS_SERVICE'"),
        ("Interventions en cours", "SELECT COUNT(*) AS n FROM interventions WHERE statut <> 'TERMINÉ'"),
        ("Alertes critiques", "SELECT COUNT(*) AS n FROM alertes WHERE resolved=FALSE AND severity='CRITICAL'"),
    ]
    cols = st.columns(4, gap="medium")
    for col, (label, sql) in zip(cols, metric_specs):
        with col:
            rows = execute_query(sql)
            value = rows[0]["n"] if rows else "—"
            st.metric(label, value)
except Exception:
    st.caption("La base n'est pas joignable. Les cartes restent visibles, les métriques passeront à jour dès la reconnexion.")

st.divider()
st.markdown(
    """
<div class="ns-card">
  <div class="ns-card-title">Navigation</div>
  <table class="ns-nav-table">
    <thead>
      <tr>
        <th>Module</th>
        <th>Rôle</th>
        <th>Point d'entrée</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Requêtes</td>
        <td>Compiler une question en langage naturel, lire le SQL généré et visualiser les résultats.</td>
        <td>Page <strong>01_requetes</strong></td>
      </tr>
      <tr>
        <td>Automates</td>
        <td>Consulter les diagrammes, déclencher les transitions et suivre l'historique par entité.</td>
        <td>Page <strong>02_automates</strong></td>
      </tr>
      <tr>
        <td>Rapports IA</td>
        <td>Produire des synthèses analytiques, afficher un niveau d'urgence et exporter un PDF.</td>
        <td>Page <strong>03_rapports_ia</strong></td>
      </tr>
      <tr>
        <td>Données</td>
        <td>Explorer les tables relationnelles et les séries temporelles avec des graphiques dark-theme.</td>
        <td>Page <strong>04_donnees</strong></td>
      </tr>
    </tbody>
  </table>
</div>
""",
    unsafe_allow_html=True,
)
