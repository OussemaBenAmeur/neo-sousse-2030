# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Neo-Sousse 2030** — a Smart City platform built for a university module (Théorie des Langages et Compilation, Section IA 2, 2025-2026). The system integrates four components:

1. **NL→SQL Compiler** — tokenizer, parser, AST builder, SQL code generator (Python)
2. **Finite State Machine engine** — models sensor lifecycle, intervention workflows, and autonomous vehicle routes
3. **Generative AI module** — produces textual reports and action recommendations from DB data
4. **Interactive dashboard** — Streamlit (or React) front-end connecting all modules

## Recommended Tech Stack

- **Language:** Python (primary), SQL
- **Database:** PostgreSQL (with optional TimescaleDB for time-series bonus)
- **Python libs:** `transitions` (FSM), `sqlalchemy` + `psycopg2` (DB), `pandas` (data), `streamlit` + `plotly` (dashboard), `openai`/`langchain`/`transformers` (generative AI)
- **Visualization:** Graphviz (automaton diagrams), D3.js / Chart.js (web)

## Common Commands

```bash
# Install dependencies
pip install transitions sqlalchemy psycopg2-binary pandas streamlit plotly openai langchain graphviz

# Run the Streamlit dashboard
streamlit run app.py

# Run the compiler standalone
python compiler/main.py

# Seed the database with test data
python db/seed.py

# Run all test scenarios
python -m pytest tests/

# Run a single test file
python -m pytest tests/test_compiler.py -v
```

## Architecture

```
pm-compilation/
├── compiler/          # NL→SQL compilation pipeline
│   ├── lexer.py       # Tokenizer: French NL → token stream
│   ├── parser.py      # Parser: token stream → AST (hand-written or PLY)
│   ├── ast_nodes.py   # AST node definitions
│   ├── codegen.py     # AST → SQL string
│   └── errors.py      # Syntax/semantic error types
├── automata/          # FSM engine
│   ├── engine.py      # Core FSM: states, transitions, trigger hooks
│   ├── sensor_fsm.py  # INACTIF→ACTIF→SIGNALÉ→EN_MAINTENANCE→HORS_SERVICE
│   ├── intervention_fsm.py  # DEMANDE→TECH1_ASSIGNÉ→TECH2_VALIDE→IA_VALIDE→TERMINÉ
│   └── vehicle_fsm.py # STATIONNÉ→EN_ROUTE→EN_PANNE→ARRIVÉ
├── ai_module/         # Generative AI report & recommendation engine
│   └── reporter.py
├── db/
│   ├── schema.sql     # Tables: capteurs, interventions, citoyens, véhicules, mesures (3NF)
│   └── seed.py        # Generate 1000+ realistic records
├── tests/             # ≥10 end-to-end scenarios (see §3.2 of spec)
└── app.py             # Streamlit entry point
```

## Key Design Constraints

### Compiler pipeline (§2.1)
The compiler must handle French natural language. Pipeline: raw string → lexer → token list → parser → AST → codegen → SQL string. Errors must be caught and reported at the syntactic and semantic stages separately.

Example mappings to support:
| Natural Language | Expected SQL |
|---|---|
| "Affiche les 5 zones les plus polluées" | `SELECT zone, AVG(pollution) FROM mesures GROUP BY zone ORDER BY AVG(pollution) DESC LIMIT 5` |
| "Combien de capteurs sont hors service ?" | `SELECT COUNT(*) FROM capteurs WHERE statut = 'hors_service'` |
| "Quels citoyens ont un score écologique > 80 ?" | `SELECT nom, score FROM citoyens WHERE score_ecolo > 80 ORDER BY score_ecolo DESC` |

### FSM engine (§2.2)
Each FSM must support: (a) validating an event sequence, (b) querying current state of any entity, (c) firing automatic side-effects (e.g., alert when a sensor stays `HORS_SERVICE` > 24h). Use the `transitions` library or a custom engine.

### Database schema (§1.2)
Minimum 3NF. Core tables: `capteurs`, `interventions`, `citoyens`, `véhicules`, `mesures`. Include temporal columns for time-series data.

### Grading weights
| Criteria | Weight |
|---|---|
| Modelling (grammars, automata, theoretical justification) | 25% |
| Implementation (compiler, FSM, generative AI) | 30% |
| Interface (dashboard usability, interactive visuals) | 20% |
| Data & Tests (dataset quality, ≥10 test scenarios) | 15% |
| Innovation | 10% |

**Bonus:** +5% each for ambiguous query handling, TimescaleDB integration, and graphical automaton visualization.
