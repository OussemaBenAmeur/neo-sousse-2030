"""Auto-selects and builds appropriate Plotly chart from query results."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_NEON_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0A0A0A",
    plot_bgcolor="#0A0A0A",
    font=dict(family="Roboto, sans-serif", color="#F0F0F0", size=13),
    title_font=dict(family="STIX Two Text, serif", color="#BBF351", size=16),
    colorway=["#BBF351", "#00BCFF", "#D97706", "#DC2626", "#16A34A", "#6B7280"],
    xaxis=dict(gridcolor="#2A2A2A", linecolor="#2A2A2A"),
    yaxis=dict(gridcolor="#2A2A2A", linecolor="#2A2A2A"),
    legend=dict(bgcolor="rgba(20,20,20,0.8)", bordercolor="#2A2A2A"),
    margin=dict(l=40, r=20, t=50, b=40),
)


def _neon_fig(fig):
    fig.update_layout(**_NEON_LAYOUT)
    return fig


def auto_chart(rows: list[dict], sql: str = "") -> None:
    """Analyze columns and render the most appropriate chart type."""
    if not rows:
        return

    df = pd.DataFrame(rows)
    if df.empty:
        return

    cols = list(df.columns)
    sql_upper = (sql or "").upper()

    time_cols = [c for c in cols if any(k in c.lower() for k in ("at", "date", "time", "bucket", "heure"))]
    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    categorical_cols = [c for c in cols if c not in numeric_cols and c not in time_cols]
    geo_cols = [c for c in cols if "lat" in c.lower() or "lon" in c.lower()]

    if len(cols) == 1 and len(rows) == 1:
        st.metric("Résultat", list(rows[0].values())[0])
        return

    if time_cols and numeric_cols:
        x_col = time_cols[0]
        y_col = numeric_cols[0]
        try:
            df[x_col] = pd.to_datetime(df[x_col])
            df = df.sort_values(x_col)
        except Exception:
            pass
        else:
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=f"Évolution de {y_col} dans le temps",
                labels={x_col: "Date / heure", y_col: y_col},
                color_discrete_sequence=["#00BCFF"],
            )
            fig.update_layout(hovermode="x unified")
            fig.add_hline(
                y=float(df[y_col].mean()),
                line_dash="dot",
                line_color="#BBF351",
                annotation_text=f"Moyenne : {df[y_col].mean():.2f}",
            )
            st.plotly_chart(_neon_fig(fig), use_container_width=True)
            return

    if categorical_cols and numeric_cols and "GROUP BY" in sql_upper:
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        df_sorted = df.sort_values(y_col, ascending=False)
        fig = px.bar(
            df_sorted,
            x=x_col,
            y=y_col,
            title=f"{y_col} par {x_col}",
            color=y_col,
            color_continuous_scale=[[0, "#00BCFF"], [1, "#BBF351"]],
        )
        st.plotly_chart(_neon_fig(fig), use_container_width=True)
        return

    if len(geo_cols) >= 2:
        lat_col = next(c for c in geo_cols if "lat" in c.lower())
        lon_col = next(c for c in geo_cols if "lon" in c.lower())
        color_col = numeric_cols[0] if numeric_cols else None
        fig = px.scatter_mapbox(
            df,
            lat=lat_col,
            lon=lon_col,
            color=color_col,
            hover_data=cols,
            mapbox_style="carto-darkmatter",
            zoom=11,
            height=420,
            title="Carte des résultats",
            color_continuous_scale=[[0, "#00BCFF"], [1, "#BBF351"]],
        )
        fig.update_layout(mapbox=dict(style="carto-darkmatter"))
        st.plotly_chart(_neon_fig(fig), use_container_width=True)
        return

    if "AVG" in sql_upper and len(rows) == 1 and numeric_cols:
        value = float(df[numeric_cols[0]].iloc[0])
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                title={"text": numeric_cols[0], "font": {"color": "#9CA3AF"}},
                number={"font": {"color": "#BBF351"}},
                gauge={
                    "axis": {"range": [0, max(100, value * 1.5)], "tickcolor": "#9CA3AF"},
                    "bar": {"color": "#BBF351"},
                    "bgcolor": "#141414",
                    "bordercolor": "#2A2A2A",
                },
            )
        )
        st.plotly_chart(_neon_fig(fig), use_container_width=True)
        return

    if categorical_cols and numeric_cols:
        fig = px.bar(
            df,
            x=categorical_cols[0],
            y=numeric_cols[0],
            color_discrete_sequence=["#BBF351"],
        )
        st.plotly_chart(_neon_fig(fig), use_container_width=True)
        return

    st.dataframe(df, use_container_width=True)
