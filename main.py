"""
main.py

Application Entry Point.

Parses command-line arguments and launches the appropriate Aegis workflow:
interactive QA with the hardened RAG pipeline, batch evaluation via the
evaluation harness, or model fine-tuning.  Loads configuration from
config.py and wires together the selected pipeline components.
"""
