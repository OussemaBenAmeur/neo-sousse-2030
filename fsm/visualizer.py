"""Graphviz-based FSM visualizer with a safe HTML fallback."""

from __future__ import annotations
import html

import graphviz


_STATE_COLORS = {
    "HORS_SERVICE": "#DC2626",
    "EN_PANNE": "#DC2626",
    "EN_MAINTENANCE": "#D97706",
    "SIGNALÉ": "#F59E0B",
    "TERMINÉ": "#00BCFF",
    "ARRIVÉ": "#00BCFF",
}
_CURRENT_COLOR = "#BBF351"
_DEFAULT_COLOR = "#141414"
_FONT_COLOR = "#F0F0F0"
_BORDER_COLOR = "#2A2A2A"
_RECENT_EDGE_COLOR = "#00BCFF"
_STATE_TONES = {
    "INACTIF": "idle",
    "STATIONNÉ": "idle",
    "DEMANDE": "idle",
    "ACTIF": "good",
    "EN_ROUTE": "good",
    "TERMINÉ": "good",
    "ARRIVÉ": "good",
    "SIGNALÉ": "warn",
    "EN_MAINTENANCE": "warn",
    "TECH1_ASSIGNÉ": "info",
    "TECH2_VALIDE": "info",
    "IA_VALIDE": "info",
    "HORS_SERVICE": "bad",
    "EN_PANNE": "bad",
}


class GraphvizVisualizer:

    def render(
        self,
        fsm,
        current_state: str | None = None,
        recent_transitions: list[dict] | None = None,
        title: str = "",
    ) -> tuple[bytes | None, str | None]:
        try:
            dot = graphviz.Digraph(
                format="svg",
                graph_attr={
                    "rankdir": "LR",
                    "bgcolor": "#0A0A0A",
                    "fontname": "Roboto",
                    "fontcolor": _FONT_COLOR,
                    "label": title,
                    "labelloc": "t",
                    "fontsize": "16",
                    "pad": "0.3",
                },
                node_attr={
                    "shape": "box",
                    "style": "rounded,filled",
                    "fontname": "Roboto",
                    "fontsize": "12",
                    "fontcolor": _FONT_COLOR,
                    "color": _BORDER_COLOR,
                },
                edge_attr={
                    "fontname": "Source Code Pro",
                    "fontsize": "10",
                    "fontcolor": _FONT_COLOR,
                    "color": _BORDER_COLOR,
                },
            )

            recent_edges: set[tuple[str, str]] = set()
            if recent_transitions:
                for transition in recent_transitions[-5:]:
                    recent_edges.add(
                        (transition.get("from_state", ""), transition.get("to_state", ""))
                    )

            for state in fsm.states:
                if state == current_state:
                    fillcolor = _CURRENT_COLOR
                    fontcolor = "#0A0A0A"
                    penwidth = "2.5"
                elif state in _STATE_COLORS:
                    fillcolor = _STATE_COLORS[state]
                    fontcolor = _FONT_COLOR
                    penwidth = "1.6"
                else:
                    fillcolor = _DEFAULT_COLOR
                    fontcolor = _FONT_COLOR
                    penwidth = "1.0"

                is_final = hasattr(fsm, "FINAL_STATES") and state in fsm.FINAL_STATES
                shape = "doublecircle" if is_final else "box"

                dot.node(
                    state,
                    label=state,
                    fillcolor=fillcolor,
                    fontcolor=fontcolor,
                    shape=shape,
                    penwidth=penwidth,
                )

            dot.node(
                "__start__",
                label="",
                shape="point",
                width="0.18",
                fillcolor=_FONT_COLOR,
                color=_FONT_COLOR,
            )
            dot.edge("__start__", fsm.initial_state, arrowhead="vee", color=_FONT_COLOR)

            for transition in fsm.transitions:
                is_recent = (transition.source, transition.target) in recent_edges
                label = transition.event
                if transition.guard:
                    label += "\n[garde]"

                dot.edge(
                    transition.source,
                    transition.target,
                    label=label,
                    color=_RECENT_EDGE_COLOR if is_recent else _BORDER_COLOR,
                    penwidth="2.2" if is_recent else "1.1",
                    fontcolor=_RECENT_EDGE_COLOR if is_recent else _FONT_COLOR,
                )

            return dot.pipe(), None
        except Exception as exc:
            return None, self._render_fallback_html(
                fsm=fsm,
                current_state=current_state,
                title=title,
                error=exc,
            )

    def _render_fallback_html(
        self,
        fsm,
        current_state: str | None,
        title: str,
        error: Exception,
    ) -> str:
        rows = []
        for transition in fsm.transitions:
            guard = "Oui" if transition.guard else "Non"
            rows.append(
                "<tr>"
                f"<td>{html.escape(transition.source)}</td>"
                f"<td><code>{html.escape(transition.event)}</code></td>"
                f"<td>{html.escape(transition.target)}</td>"
                f"<td>{guard}</td>"
                "</tr>"
            )

        tone = _STATE_TONES.get(current_state or "", "idle")
        title_html = html.escape(title or "Automate")
        current_label = html.escape(current_state or "Non disponible")
        error_label = html.escape(str(error))
        rows_html = "".join(rows)
        return f"""
<div class="ns-card">
  <div class="ns-card-title">{title_html}</div>
  <p class="ns-muted">Graphviz indisponible, affichage tabulaire de secours.</p>
  <div class="ns-badge-row" style="margin: 0.75rem 0 1rem 0;">
    <span class="ns-tag {tone}">{current_label}</span>
  </div>
  <div style="overflow-x:auto;">
    <table class="ns-nav-table">
      <thead>
        <tr>
          <th>Depuis</th>
          <th>Événement</th>
          <th>Vers</th>
          <th>Garde</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
  <p class="ns-muted" style="margin-top: 0.75rem;">Détail technique : {error_label}</p>
</div>
"""
