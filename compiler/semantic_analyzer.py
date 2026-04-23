"""
SemanticAnalyzer — walks the AST and fills in resolved names.

Responsibilities:
  1. Resolve entity raw_name → canonical table name (via ENTITY_TABLE_MAP)
  2. Resolve attribute raw_name → (table, column) (via SCHEMA_REGISTRY + ATTRIBUTE_COLUMN_MAP)
  3. Type-coerce ValueNode literals (string → quoted, number → float/int)
  4. Infer missing AVG/COUNT target from context
  5. Raise SemanticError with French messages for unknown entities/columns
"""

from compiler.ast_nodes import (
    QueryNode, EntityRef, AttributeRef, ValueNode,
    AvgIntent, CountIntent, TopNIntent, SelectIntent,
    WhereClause, GroupByClause, OrderByClause,
)
from compiler.tokens import ENTITY_TABLE_MAP, ATTRIBUTE_COLUMN_MAP, SCHEMA_REGISTRY
from compiler.errors import SemanticError

# Cross-table join paths: (entity_table, data_table) → join SQL fragment
# Used when an attribute can't be resolved in entity_table but lives in data_table.
_JOIN_PATHS: dict[tuple[str, str], str] = {
    ("zones", "mesures"):
        "JOIN capteurs _c ON _c.zone_id = {entity}.id "
        "JOIN mesures ON mesures.capteur_id = _c.id",
    ("capteurs", "mesures"):
        "JOIN mesures ON mesures.capteur_id = {entity}.id",
    ("zones", "capteurs"):
        "JOIN capteurs ON capteurs.zone_id = {entity}.id",
}

# Columns that make sense as AVG targets for cross-table aggregation
_NUMERIC_AGG_COLS = {"pm25", "pm10", "temperature", "humidite", "co2", "no2",
                     "niveau_bruit", "indice_trafic", "score_ecolo", "economie_co2"}


class SemanticAnalyzer:

    def analyze(self, node: QueryNode) -> QueryNode:
        """Mutates and returns the QueryNode with all resolved fields set."""
        self._resolve_entity(node)
        self._resolve_attributes(node)
        self._coerce_values(node)
        self._infer_aggregation_target(node)
        self._rewrite_cross_table_aggregation(node)
        return node

    # ──────────────────────────────────────────────────────────

    def _resolve_entity(self, node: QueryNode) -> None:
        if node.entity is None:
            return
        raw = node.entity.raw_name.lower()
        table = ENTITY_TABLE_MAP.get(raw)
        if table is None:
            known = ", ".join(sorted(set(ENTITY_TABLE_MAP.values())))
            raise SemanticError(
                f"Entité inconnue : '{node.entity.raw_name}'. "
                f"Entités disponibles : {known}.",
                pos=node.entity.pos,
            )
        node.entity.resolved_table = table

    def _resolve_attributes(self, node: QueryNode) -> None:
        table = node.entity.resolved_table if node.entity else None

        def resolve(attr: AttributeRef) -> None:
            raw = attr.raw_name.lower()
            # Try alias map first
            canonical = ATTRIBUTE_COLUMN_MAP.get(raw, raw)

            if table and table in SCHEMA_REGISTRY:
                cols = SCHEMA_REGISTRY[table]
                if canonical in cols:
                    attr.resolved_column = canonical
                    attr.resolved_table = table
                    return
                # Fuzzy: check if any column starts with raw
                matches = [c for c in cols if c.startswith(raw) or raw.startswith(c)]
                if len(matches) == 1:
                    attr.resolved_column = matches[0]
                    attr.resolved_table = table
                    return
                if len(matches) > 1:
                    raise SemanticError(
                        f"Attribut ambigu : '{attr.raw_name}' correspond à plusieurs colonnes "
                        f"({', '.join(matches)}) dans '{table}'. Précisez.",
                        pos=attr.pos,
                    )
                # Not found in current table — try cross-table lookup before raising
                cross = self._find_in_any_table(canonical)
                if cross:
                    attr.resolved_column = canonical
                    attr.resolved_table = cross
                    return
                # Try fuzzy in all tables
                cross_fuzzy = self._find_fuzzy_any_table(raw)
                if cross_fuzzy:
                    attr.resolved_column = cross_fuzzy[1]
                    attr.resolved_table = cross_fuzzy[0]
                    return
                available = ", ".join(cols)
                raise SemanticError(
                    f"Colonne inconnue : '{attr.raw_name}' n'existe pas dans '{table}'. "
                    f"Colonnes disponibles : {available}.",
                    pos=attr.pos,
                )
            # No table context → keep raw as best-effort
            attr.resolved_column = canonical

        for attr in node.attributes:
            resolve(attr)

        if node.where:
            for cond in node.where.conditions:
                resolve(cond.left)

        if node.groupby:
            for attr in node.groupby.attributes:
                resolve(attr)

        if node.orderby and node.orderby.attribute:
            resolve(node.orderby.attribute)

        # AVG / COUNT intents may carry an attribute
        if isinstance(node.intent, (AvgIntent, CountIntent)) and node.intent.target:
            resolve(node.intent.target)

    def _coerce_values(self, node: QueryNode) -> None:
        if not node.where:
            return
        table = node.entity.resolved_table if node.entity else None

        for cond in node.where.conditions:
            v = cond.right
            if v.kind == "number":
                try:
                    v.coerced = float(v.raw)
                except ValueError:
                    raise SemanticError(
                        f"Impossible de convertir '{v.raw}' en nombre.", pos=v.pos
                    )
            elif v.kind == "string":
                v.coerced = v.raw  # already clean
            else:
                # identifier — could be a string value (e.g., statut = actif)
                v.coerced = v.raw
                v.kind = "string"

    def _find_in_any_table(self, canonical: str) -> str | None:
        """Return the first table name in SCHEMA_REGISTRY that contains `canonical`."""
        for tname, cols in SCHEMA_REGISTRY.items():
            if canonical in cols:
                return tname
        return None

    def _find_fuzzy_any_table(self, raw: str) -> tuple[str, str] | None:
        """Fuzzy match `raw` across all tables. Returns (table, column) or None."""
        for tname, cols in SCHEMA_REGISTRY.items():
            matches = [c for c in cols if c.startswith(raw) or raw.startswith(c)]
            if len(matches) == 1:
                return tname, matches[0]
        return None

    def _rewrite_cross_table_aggregation(self, node: QueryNode) -> None:
        """
        Detect TopN/Select queries where the entity is a dimension table (e.g. zones)
        but the ORDER BY attribute belongs to a fact table (e.g. mesures.pm25).
        Rewrites the node to emit a JOIN + GROUP BY + AVG aggregation.

        The join metadata is stored in node.meta["cross_join"] for the codegen.
        """
        if node.entity is None:
            return
        entity_table = node.entity.resolved_table
        if entity_table is None:
            return

        orderby_attr = node.orderby.attribute if node.orderby else None
        if orderby_attr is None:
            return

        data_table = orderby_attr.resolved_table
        if data_table is None or data_table == entity_table:
            return  # no cross-table situation

        join_key = (entity_table, data_table)
        join_sql = _JOIN_PATHS.get(join_key)
        if join_sql is None:
            return  # unknown join path — leave as-is, codegen will do best-effort

        # Store join info in node metadata for the codegen
        if not hasattr(node, "meta") or node.meta is None:
            node.meta = {}
        node.meta["cross_join"] = join_sql.format(entity=entity_table)
        node.meta["agg_col"] = orderby_attr.resolved_column
        node.meta["agg_table"] = data_table
        node.meta["group_col"] = "nom"  # dimension label column (zones.nom, etc.)

    def _infer_aggregation_target(self, node: QueryNode) -> None:
        """
        If AVG has no explicit target but the entity has a single numeric column,
        use it automatically. Otherwise require explicit specification.
        """
        if not isinstance(node.intent, AvgIntent):
            return
        if node.intent.target is not None:
            return
        table = node.entity.resolved_table if node.entity else None
        if table is None:
            raise SemanticError(
                "La moyenne nécessite une colonne cible (ex: 'moyenne du pm25 des capteurs').",
                pos=node.intent.pos,
            )
        numeric_cols = [
            c for c in SCHEMA_REGISTRY.get(table, [])
            if any(c.startswith(p) for p in ("pm", "temp", "hum", "co2", "no2", "score", "dist", "eco", "bruit", "traf"))
        ]
        if len(numeric_cols) == 1:
            node.intent.target = AttributeRef(
                raw_name=numeric_cols[0],
                resolved_column=numeric_cols[0],
                resolved_table=table,
            )
        else:
            cols_str = ", ".join(numeric_cols) or "aucune"
            raise SemanticError(
                f"Ambiguïté : quelle colonne calculer en moyenne pour '{table}'? "
                f"Colonnes numériques disponibles : {cols_str}. "
                f"Exemple : 'moyenne du pm25 des capteurs'.",
                pos=node.intent.pos,
            )
