"""Requêtes en langage naturel — saisie, compilation, exécution, visualisation."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from dashboard import state as S
from dashboard.components.ast_viewer import show_debug_pipeline
from dashboard.components.chart_builder import auto_chart
from dashboard.components.results_table import show_results_table
from dashboard.theme import apply_theme

st.set_page_config(page_title="Requêtes — Neo-Sousse 2030", layout="wide")
apply_theme()

st.markdown("# Requêtes en langage naturel")
st.caption(
    "Posez une question en français : le compilateur produit la requête SQL, "
    "l'exécute, puis présente les résultats."
)


for key in (
    S.LAST_SQL, S.LAST_AST, S.LAST_TOKENS, S.QUERY_RESULTS,
    S.AMBIGUITY_QUESTION, S.AMBIGUITY_INTERPRETATIONS,
    S.SQL_NL_EXPLANATION, S.QUERY_DESCRIPTION,
):
    st.session_state.setdefault(key, None)
st.session_state.setdefault(S.DEBUG_MODE, False)


@st.cache_resource
def get_pipeline():
    from compiler.pipeline import NLToSQLPipeline
    return NLToSQLPipeline()


@st.cache_resource
def get_report_gen():
    from ai.report_generator import ReportGenerator
    return ReportGenerator()


pipeline = get_pipeline()
report_gen = get_report_gen()


with st.sidebar:
    st.markdown("### Exemples")
    examples = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score écologique > 80 ?",
        "Donne-moi le trajet le plus économique en CO2",
        "Affiche les interventions avec priorité urgente",
        "Combien d'interventions sont en cours ?",
        "Moyenne du pm25 des capteurs actifs",
        "Affiche les capteurs dont le statut est hors_service",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:24]}", use_container_width=True):
            st.session_state[S.QUERY_INPUT] = ex
            st.rerun()

    st.divider()
    st.session_state[S.DEBUG_MODE] = st.toggle(
        "Mode débogage",
        value=st.session_state[S.DEBUG_MODE],
        help="Affiche les tokens, l'AST et le SQL côte à côte.",
    )


st.markdown(
    '<span class="ns-card-title">Question en langage naturel</span>',
    unsafe_allow_html=True,
)
query = st.text_input(
    "Votre question",
    value=st.session_state.get(S.QUERY_INPUT, ""),
    placeholder="Affiche les 5 zones les plus polluées",
    key=S.QUERY_INPUT,
    label_visibility="collapsed",
)

col_a, col_b, _ = st.columns([1, 1, 6])
submitted = col_a.button("Compiler", type="primary")
if col_b.button("Effacer"):
    for key in (
        S.LAST_SQL, S.LAST_AST, S.LAST_TOKENS, S.QUERY_RESULTS,
        S.AMBIGUITY_QUESTION, S.AMBIGUITY_INTERPRETATIONS, S.SQL_NL_EXPLANATION,
    ):
        st.session_state[key] = None
    st.rerun()


if st.session_state[S.AMBIGUITY_QUESTION]:
    st.warning(f"Ambiguïté détectée — {st.session_state[S.AMBIGUITY_QUESTION]}")
    interps = st.session_state[S.AMBIGUITY_INTERPRETATIONS] or []
    chosen = st.radio(
        "Interprétations possibles",
        options=[f"Option {i + 1}" for i in range(len(interps))],
        captions=[sql.splitlines()[0][:80] + "..." for sql in interps],
        key="ambiguity_choice",
    )
    if st.button("Retenir cette interprétation", type="primary"):
        idx = int(chosen.split()[-1]) - 1
        st.session_state[S.LAST_SQL] = interps[idx]
        st.session_state[S.AMBIGUITY_QUESTION] = None
        st.session_state[S.AMBIGUITY_INTERPRETATIONS] = None
        submitted = True


if submitted and query:
    result = pipeline.compile_safe(query)

    if result.get("ambiguous"):
        st.session_state[S.AMBIGUITY_QUESTION] = result.get("question")
        st.session_state[S.AMBIGUITY_INTERPRETATIONS] = result.get("interpretations", [])
        st.session_state[S.LAST_SQL] = None
        st.session_state[S.QUERY_RESULTS] = None
        st.rerun()

    elif not result["success"]:
        st.error(f"Erreur de compilation — {result['error']}")
        st.session_state[S.LAST_SQL] = None

    else:
        sql = result["sql"]
        st.session_state[S.LAST_SQL] = sql
        st.session_state[S.LAST_SQL_PARAMS] = result.get("params", {})
        st.session_state[S.LAST_AST] = result.get("ast")
        st.session_state[S.LAST_TOKENS] = result.get("tokens", [])
        st.session_state[S.QUERY_DESCRIPTION] = result.get("description")

        try:
            st.session_state[S.SQL_NL_EXPLANATION] = report_gen.explain_sql(sql)
        except Exception:
            st.session_state[S.SQL_NL_EXPLANATION] = None

        try:
            from database.connection import execute_query
            st.session_state[S.QUERY_RESULTS] = execute_query(sql, result.get("params", {}))
        except Exception as exc:
            st.error(f"Erreur d'exécution SQL — {exc}")
            st.session_state[S.QUERY_RESULTS] = None


if st.session_state[S.LAST_SQL]:
    st.divider()

    if st.session_state.get(S.SQL_NL_EXPLANATION):
        st.markdown(f"> {st.session_state[S.SQL_NL_EXPLANATION]}")

    if st.session_state.get(S.QUERY_DESCRIPTION):
        st.caption(st.session_state[S.QUERY_DESCRIPTION])

    st.markdown(
        '<span class="ns-tag info">SQL Généré</span>',
        unsafe_allow_html=True,
    )
    with st.expander("Requête SQL générée", expanded=True):
        st.code(st.session_state[S.LAST_SQL], language="sql")

    results = st.session_state[S.QUERY_RESULTS]
    if results is not None:
        st.markdown(f"#### Résultats — {len(results)} ligne(s)")
        tab_chart, tab_table = st.tabs(["Visualisation", "Tableau"])
        with tab_chart:
            auto_chart(results, st.session_state[S.LAST_SQL])
        with tab_table:
            show_results_table(results)

    if st.session_state[S.DEBUG_MODE] and st.session_state[S.LAST_AST]:
        show_debug_pipeline(
            tokens=st.session_state[S.LAST_TOKENS] or [],
            ast_dict=st.session_state[S.LAST_AST],
            sql=st.session_state[S.LAST_SQL],
        )
