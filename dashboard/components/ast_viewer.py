"""Debug stepper: tokens → AST → SQL."""

import streamlit as st


def show_debug_pipeline(tokens: list, ast_dict: dict, sql: str) -> None:
    st.markdown("---")
    st.markdown("### Mode débogage — pipeline de compilation")

    cols = st.columns(3, gap="medium")

    with cols[0]:
        st.markdown("**1. Tokens (lexer)**")
        for tok in tokens:
            if tok["type"] == "EOF":
                continue
            st.markdown(
                f'<div style="font-family:monospace;font-size:0.85rem;'
                f'padding:0.2rem 0.5rem;margin:0.15rem 0;border:1px solid #d8d4ca;'
                f'background:#f6f3eb;border-radius:2px;">'
                f'<span style="color:#1f3a5f;font-weight:600;">{tok["type"]}</span>'
                f' &nbsp;{tok["value"]}</div>',
                unsafe_allow_html=True,
            )

    with cols[1]:
        st.markdown("**2. AST (parser)**")
        st.json(ast_dict, expanded=2)

    with cols[2]:
        st.markdown("**3. SQL généré**")
        st.code(sql, language="sql")
