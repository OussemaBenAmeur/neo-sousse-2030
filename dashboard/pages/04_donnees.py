"""Explorateur de données — tables relationnelles et séries temporelles."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components.chart_builder import _neon_fig
from dashboard.components.results_table import show_results_table
from dashboard.theme import apply_theme
from database.connection import execute_query

st.set_page_config(page_title="Données — Neo-Sousse 2030", layout="wide")
apply_theme()

st.markdown("# Explorateur de données")
st.caption(
    "Parcourez les entités relationnelles et les séries temporelles brutes "
    "stockées dans PostgreSQL/TimescaleDB."
)


def _tone(status: str) -> str:
    return {
        "ACTIF": "good",
        "SIGNALÉ": "warn",
        "EN_MAINTENANCE": "warn",
        "HORS_SERVICE": "bad",
        "INACTIF": "idle",
    }.get(status, "info")


def _status_badges(rows: list[dict]) -> None:
    if not rows:
        return
    badges = "".join(
        f'<span class="ns-tag {_tone(row["statut"])}">{row["statut"]} · {row["total"]}</span>'
        for row in rows
    )
    st.markdown(f'<div class="ns-badge-row">{badges}</div>', unsafe_allow_html=True)


tab_capteurs, tab_mesures, tab_inter, tab_citoyens = st.tabs(
    ["Capteurs", "Mesures (séries temporelles)", "Interventions", "Citoyens"]
)

with tab_capteurs:
    st.markdown("### Réseau de capteurs")
    try:
        status_rows = execute_query(
            "SELECT statut, COUNT(*) AS total FROM capteurs GROUP BY statut ORDER BY total DESC"
        )
        _status_badges(status_rows)

        col1, col2 = st.columns(2)
        zones = execute_query("SELECT nom FROM zones ORDER BY nom")
        zone_names = ["Toutes"] + [zone["nom"] for zone in zones]
        selected_zone = col1.selectbox("Zone", zone_names, key="zone_filter")
        statuts = ["Tous", "ACTIF", "INACTIF", "SIGNALÉ", "EN_MAINTENANCE", "HORS_SERVICE"]
        selected_statut = col2.selectbox("Statut", statuts, key="statut_filter")

        sql = (
            "SELECT c.id, c.nom, c.type, z.nom AS zone, c.statut, "
            "       c.fabricant, c.date_installation::date AS installation "
            "FROM capteurs c LEFT JOIN zones z ON z.id=c.zone_id "
            "WHERE 1=1"
        )
        params = {}
        if selected_zone != "Toutes":
            sql += " AND z.nom=:zone"
            params["zone"] = selected_zone
        if selected_statut != "Tous":
            sql += " AND c.statut=:statut"
            params["statut"] = selected_statut
        sql += " ORDER BY c.id"

        show_results_table(execute_query(sql, params), key="capteurs_table")
    except Exception as exc:
        st.error(f"Erreur — {exc}")

with tab_mesures:
    st.markdown("### Séries temporelles — TimescaleDB")
    try:
        col1, col2, col3 = st.columns(3)
        capteurs = execute_query(
            "SELECT id, nom FROM capteurs WHERE statut='ACTIF' ORDER BY nom"
        )
        if not capteurs:
            st.caption("Aucun capteur actif.")
        else:
            cap_options = {f"{capteur['nom']} (ID {capteur['id']})": capteur["id"] for capteur in capteurs}
            selected = col1.selectbox("Capteur", list(cap_options.keys()))
            cap_id = cap_options[selected]
            metric = col2.selectbox("Mesure", ["pm25", "pm10", "temperature", "humidite", "co2", "no2"])
            days = col3.slider("Jours", min_value=1, max_value=90, value=7)

            try:
                rows = execute_query(
                    (
                        "SELECT time_bucket('1 hour', mesure_at) AS heure, "
                        f"ROUND(AVG({metric})::numeric, 2) AS valeur "
                        "FROM mesures "
                        "WHERE capteur_id=:id AND mesure_at > NOW() - (:days || ' days')::INTERVAL "
                        f"  AND {metric} IS NOT NULL "
                        "GROUP BY heure ORDER BY heure"
                    ),
                    {"id": cap_id, "days": days},
                )
            except Exception:
                rows = execute_query(
                    (
                        "SELECT DATE_TRUNC('hour', mesure_at) AS heure, "
                        f"ROUND(AVG({metric})::numeric, 2) AS valeur "
                        "FROM mesures "
                        "WHERE capteur_id=:id AND mesure_at > NOW() - (:days || ' days')::INTERVAL "
                        f"  AND {metric} IS NOT NULL "
                        "GROUP BY heure ORDER BY heure"
                    ),
                    {"id": cap_id, "days": days},
                )

            if not rows:
                st.caption("Aucune donnée pour cette période.")
            else:
                df = pd.DataFrame(rows)
                df["heure"] = pd.to_datetime(df["heure"])
                fig = px.line(
                    df,
                    x="heure",
                    y="valeur",
                    title=f"{metric.upper()} — {selected} (derniers {days} jours)",
                    labels={"heure": "Date / heure", "valeur": metric},
                    color_discrete_sequence=["#00BCFF"],
                )
                fig.add_hline(
                    y=float(df["valeur"].mean()),
                    line_dash="dot",
                    line_color="#BBF351",
                    annotation_text=f"Moyenne : {df['valeur'].mean():.1f}",
                )
                st.plotly_chart(_neon_fig(fig), use_container_width=True)
                st.caption(
                    f"{len(rows)} points — min {df['valeur'].min():.2f} | "
                    f"max {df['valeur'].max():.2f} | "
                    f"moyenne {df['valeur'].mean():.2f}"
                )
    except Exception as exc:
        st.error(f"Erreur TimescaleDB — {exc}")

with tab_inter:
    st.markdown("### Interventions")
    try:
        rows = execute_query(
            "SELECT i.id, c.nom AS capteur, i.statut, i.priorite, i.description, "
            "       i.created_at::date AS date_creation, "
            "       CASE WHEN i.ai_validation IS NOT NULL "
            "            THEN (i.ai_validation->>'approved')::boolean ELSE NULL END AS ia_approuvee "
            "FROM interventions i JOIN capteurs c ON c.id=i.capteur_id "
            "ORDER BY i.created_at DESC LIMIT 100"
        )
        show_results_table(rows, key="inter_table")
    except Exception as exc:
        st.error(f"Erreur — {exc}")

with tab_citoyens:
    st.markdown("### Citoyens")
    try:
        rows = execute_query(
            "SELECT c.nom, c.prenom, z.nom AS zone, c.score_ecolo "
            "FROM citoyens c LEFT JOIN zones z ON z.id=c.zone_id "
            "ORDER BY c.score_ecolo DESC LIMIT 100"
        )
        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        if not df.empty:
            fig = px.histogram(
                df,
                x="score_ecolo",
                nbins=20,
                title="Distribution des scores écologiques",
                labels={"score_ecolo": "Score écologique"},
                color_discrete_sequence=["#BBF351"],
            )
            st.plotly_chart(_neon_fig(fig), use_container_width=True)
        show_results_table(rows, key="citoyens_table")
    except Exception as exc:
        st.error(f"Erreur — {exc}")
