"""Live real-time map of Sousse — all smart city entities, auto-refreshed."""

import os
import sys
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from database.connection import execute_query
from dashboard.theme import apply_theme

# ── Constants ──────────────────────────────────────────────────────────────
SOUSSE_LAT = 35.8282
SOUSSE_LON = 10.6358
MAP_ZOOM = 12
REFRESH_SECONDS = 5

CAPTEUR_COLORS = {
    "ACTIF":          "#BBF351",
    "INACTIF":        "#6B7280",
    "SIGNALÉ":        "#F59E0B",
    "EN_MAINTENANCE": "#00BCFF",
    "HORS_SERVICE":   "#DC2626",
}
VEHICULE_COLORS = {
    "STATIONNÉ": "#6B7280",
    "EN_ROUTE":  "#00BCFF",
    "EN_PANNE":  "#DC2626",
    "ARRIVÉ":    "#BBF351",
}
SEVERITY_COLORS = {
    "CRITICAL": "#DC2626",
    "WARNING":  "#F59E0B",
    "INFO":     "#00BCFF",
}

# ── SQL Queries ────────────────────────────────────────────────────────────
_SQL_ZONES = """
SELECT z.id, z.nom,
       z.geom_lat  AS lat,
       z.geom_lon  AS lon,
       z.superficie,
       COUNT(DISTINCT c.id)                                     AS nb_capteurs,
       COUNT(DISTINCT c.id) FILTER (WHERE c.statut = 'ACTIF')  AS capteurs_actifs,
       ROUND(AVG(m.pm25)::numeric, 1)                          AS pm25_moy
FROM zones z
LEFT JOIN capteurs c ON c.zone_id = z.id
LEFT JOIN mesures  m ON m.capteur_id = c.id
     AND m.mesure_at > NOW() - INTERVAL '1 hour'
GROUP BY z.id, z.nom, z.geom_lat, z.geom_lon, z.superficie
"""

_SQL_CAPTEURS = """
SELECT c.id, c.nom, c.type, c.statut,
       c.latitude, c.longitude,
       z.nom                               AS zone_nom,
       m.pm25, m.temperature, m.co2,
       TO_CHAR(m.mesure_at, 'HH24:MI:SS') AS mesure_at
FROM capteurs c
JOIN zones z ON z.id = c.zone_id
LEFT JOIN LATERAL (
    SELECT pm25, temperature, co2, mesure_at
    FROM mesures
    WHERE capteur_id = c.id
    ORDER BY mesure_at DESC
    LIMIT 1
) m ON TRUE
WHERE c.latitude IS NOT NULL AND c.longitude IS NOT NULL
"""

_SQL_VEHICULES = """
SELECT v.id, v.immatriculation, v.type, v.statut,
       v.conducteur, v.autonome,
       z.nom AS zone_nom,
       z.geom_lat + ((v.id % 11) - 5) * 0.00035 AS lat,
       z.geom_lon + ((v.id %  7) - 3) * 0.00045 AS lon
FROM vehicules v
JOIN zones z ON z.id = v.zone_id
"""

_SQL_ALERTES = """
SELECT a.id, a.type, a.entity_type, a.entity_id,
       a.message, a.severity,
       TO_CHAR(a.created_at, 'YYYY-MM-DD HH24:MI') AS created_at,
       COALESCE(c.latitude,  z.geom_lat)  AS lat,
       COALESCE(c.longitude, z.geom_lon)  AS lon
FROM alertes a
LEFT JOIN capteurs c ON a.entity_type = 'capteur' AND a.entity_id = c.id
LEFT JOIN zones    z ON z.id = c.zone_id
WHERE a.resolved = FALSE
  AND (c.latitude IS NOT NULL OR z.geom_lat IS NOT NULL)
ORDER BY a.created_at DESC
"""

_SQL_STATS = """
SELECT
  (SELECT COUNT(*) FROM capteurs     WHERE statut = 'ACTIF')                           AS capteurs_actifs,
  (SELECT COUNT(*) FROM capteurs     WHERE statut = 'HORS_SERVICE')                    AS hors_service,
  (SELECT COUNT(*) FROM vehicules    WHERE statut = 'EN_ROUTE')                        AS vehicules_route,
  (SELECT COUNT(*) FROM alertes      WHERE resolved = FALSE AND severity = 'CRITICAL') AS alertes_critiques,
  (SELECT COUNT(*) FROM interventions WHERE statut <> 'TERMINÉ')                       AS interventions_actives
"""

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Carte Live – Neo-Sousse 2030",
    page_icon="🗺",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# ── Sidebar – layer & filter controls ─────────────────────────────────────
with st.sidebar:
    st.markdown("### Couches")
    st.toggle("Zones",          True, key="show_zones")
    st.toggle("Capteurs",       True, key="show_capteurs")
    st.toggle("Véhicules",      True, key="show_vehicules")
    st.toggle("Alertes actives",True, key="show_alertes")

    st.markdown("---")
    st.markdown("### Filtres capteurs")
    st.multiselect(
        "Statut",
        list(CAPTEUR_COLORS.keys()),
        default=list(CAPTEUR_COLORS.keys()),
        key="capteur_statuts",
    )

    st.markdown("---")
    st.markdown("### Filtres véhicules")
    st.multiselect(
        "Statut",
        list(VEHICULE_COLORS.keys()),
        default=list(VEHICULE_COLORS.keys()),
        key="vehicule_statuts",
    )

    st.markdown("---")
    st.caption(f"↻ Actualisation auto toutes les {REFRESH_SECONDS} s")
    st.caption("Zoom / déplacez la carte librement — la vue est conservée.")

# ── Header ─────────────────────────────────────────────────────────────────
st.title("Carte Live — Sousse 2030")
st.caption("Capteurs · Véhicules · Alertes · Zones — mise à jour en temps réel")


# ── Live fragment (re-runs every REFRESH_SECONDS without full page reload) ──
@st.fragment(run_every=REFRESH_SECONDS)
def _live_map() -> None:
    # Read sidebar state into local vars
    show_zones     = st.session_state.get("show_zones",     True)
    show_capteurs  = st.session_state.get("show_capteurs",  True)
    show_vehicules = st.session_state.get("show_vehicules", True)
    show_alertes   = st.session_state.get("show_alertes",   True)
    cap_statuts    = st.session_state.get("capteur_statuts",  list(CAPTEUR_COLORS.keys()))
    veh_statuts    = st.session_state.get("vehicule_statuts", list(VEHICULE_COLORS.keys()))

    # ── Fetch all data ────────────────────────────────────────────────────
    df_zones = pd.DataFrame(execute_query(_SQL_ZONES))
    df_cap   = pd.DataFrame(execute_query(_SQL_CAPTEURS))
    df_veh   = pd.DataFrame(execute_query(_SQL_VEHICULES))
    df_alr   = pd.DataFrame(execute_query(_SQL_ALERTES))
    stats    = execute_query(_SQL_STATS)
    stat     = stats[0] if stats else {}

    # ── KPI strip ─────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Capteurs actifs",       stat.get("capteurs_actifs",       "–"))
    c2.metric("Hors service",          stat.get("hors_service",          "–"))
    c3.metric("Véhicules en route",    stat.get("vehicules_route",       "–"))
    c4.metric("Alertes critiques",     stat.get("alertes_critiques",     "–"))
    c5.metric("Interventions actives", stat.get("interventions_actives", "–"))

    # ── Build Plotly map ──────────────────────────────────────────────────
    fig = go.Figure()

    # Layer 1 — Zones (large translucent bubbles)
    if show_zones and not df_zones.empty:
        z = df_zones.dropna(subset=["lat", "lon"])
        sizes = (z["nb_capteurs"].fillna(0).clip(lower=1) * 4 + 16).tolist()
        fig.add_trace(go.Scattermapbox(
            name="Zones",
            lat=z["lat"].tolist(),
            lon=z["lon"].tolist(),
            mode="markers+text",
            text=z["nom"].tolist(),
            textposition="top center",
            textfont=dict(color="#9CA3AF", size=10),
            marker=dict(size=sizes, color="rgba(187,243,81,0.10)", opacity=0.9),
            customdata=z[["nom", "nb_capteurs", "capteurs_actifs", "pm25_moy", "superficie"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Capteurs : %{customdata[1]} (%{customdata[2]} actifs)<br>"
                "PM2.5 moy (1h) : %{customdata[3]} µg/m³<br>"
                "Superficie : %{customdata[4]} km²"
                "<extra></extra>"
            ),
        ))

    # Layer 2 — Capteurs (one trace per status for independent legend entries)
    if show_capteurs and not df_cap.empty:
        df_cap = df_cap[df_cap["statut"].isin(cap_statuts)]
        for statut, color in CAPTEUR_COLORS.items():
            sub = df_cap[df_cap["statut"] == statut]
            if sub.empty:
                continue
            fig.add_trace(go.Scattermapbox(
                name=f"Capteur · {statut}",
                lat=sub["latitude"].tolist(),
                lon=sub["longitude"].tolist(),
                mode="markers",
                marker=dict(size=10, color=color, opacity=0.92),
                customdata=sub[["nom", "type", "zone_nom", "pm25", "temperature", "co2", "mesure_at"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
                    "Zone : %{customdata[2]}<br>"
                    "PM2.5 : %{customdata[3]} µg/m³  ·  Temp : %{customdata[4]} °C<br>"
                    "CO₂ : %{customdata[5]} ppm<br>"
                    "Mesuré à : %{customdata[6]}"
                    "<extra></extra>"
                ),
            ))

    # Layer 3 — Véhicules
    if show_vehicules and not df_veh.empty:
        df_veh = df_veh[df_veh["statut"].isin(veh_statuts)]
        for statut, color in VEHICULE_COLORS.items():
            sub = df_veh[df_veh["statut"] == statut]
            if sub.empty:
                continue
            fig.add_trace(go.Scattermapbox(
                name=f"Véhicule · {statut}",
                lat=sub["lat"].tolist(),
                lon=sub["lon"].tolist(),
                mode="markers",
                marker=dict(size=14, color=color, opacity=0.95),
                customdata=sub[["immatriculation", "type", "statut", "conducteur", "zone_nom", "autonome"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                    "Statut : %{customdata[2]}<br>"
                    "Conducteur : %{customdata[3]}<br>"
                    "Zone : %{customdata[4]}<br>"
                    "Autonome : %{customdata[5]}"
                    "<extra></extra>"
                ),
            ))

    # Layer 4 — Active alerts (large pulsing markers on top)
    if show_alertes and not df_alr.empty:
        alr = df_alr.dropna(subset=["lat", "lon"])
        for severity, color in SEVERITY_COLORS.items():
            sub = alr[alr["severity"] == severity]
            if sub.empty:
                continue
            fig.add_trace(go.Scattermapbox(
                name=f"Alerte · {severity}",
                lat=sub["lat"].tolist(),
                lon=sub["lon"].tolist(),
                mode="markers",
                marker=dict(
                    size=20 if severity == "CRITICAL" else 15,
                    color=color,
                    opacity=1.0,
                ),
                customdata=sub[["type", "entity_type", "entity_id", "message", "severity", "created_at"]].values,
                hovertemplate=(
                    "⚠ <b>%{customdata[4]}</b><br>"
                    "Type : %{customdata[0]}<br>"
                    "Entité : %{customdata[1]} #%{customdata[2]}<br>"
                    "%{customdata[3]}<br>"
                    "Créée : %{customdata[5]}"
                    "<extra></extra>"
                ),
            ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",  # dark tile, no Mapbox token needed
            center=dict(lat=SOUSSE_LAT, lon=SOUSSE_LON),
            zoom=MAP_ZOOM,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=580,
        paper_bgcolor="#0A0A0A",
        plot_bgcolor="#0A0A0A",
        font=dict(color="#F0F0F0", family="Roboto, sans-serif"),
        legend=dict(
            bgcolor="rgba(14,14,14,0.88)",
            bordercolor="#2A2A2A",
            borderwidth=1,
            font=dict(size=11),
            x=0.01,
            y=0.99,
            xanchor="left",
            yanchor="top",
        ),
        # uirevision keeps zoom/pan state between fragment reruns
        uirevision="sousse-map-stable",
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": False})

    # ── Last-updated timestamp ────────────────────────────────────────────
    st.caption(f"Dernière mise à jour : **{datetime.now().strftime('%H:%M:%S')}** — prochain refresh dans {REFRESH_SECONDS} s")

    # ── Active alerts table ───────────────────────────────────────────────
    if show_alertes and not df_alr.empty:
        with st.expander(f"⚠ Alertes actives ({len(df_alr)})", expanded=False):
            display_cols = {
                "severity": "Sévérité",
                "type": "Type",
                "entity_type": "Entité",
                "entity_id": "ID",
                "message": "Message",
                "created_at": "Créée le",
            }
            st.dataframe(
                df_alr[[c for c in display_cols if c in df_alr.columns]].rename(columns=display_cols),
                hide_index=True,
                use_container_width=True,
            )


_live_map()
