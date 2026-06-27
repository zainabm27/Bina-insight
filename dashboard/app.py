"""Compatibility wrapper. Prefer: streamlit run dashboard/dashboard_app.py"""
from pathlib import Path
exec(Path(__file__).with_name("dashboard_app.py").read_text(encoding="utf-8"))
