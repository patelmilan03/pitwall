"""PitWall — an OpenF1 → S3 lake → Postgres warehouse → Streamlit data pipeline.

Package layout (see docs/TRD.md §4). Business-logic modules
(``transform``, ``aggregate``, ``schemas`` …) never import Prefect and are plain,
unit-testable functions; only ``flows.py`` orchestrates and only
``storage.py`` / ``warehouse.py`` touch cloud services.
"""

__version__ = "0.1.0"
