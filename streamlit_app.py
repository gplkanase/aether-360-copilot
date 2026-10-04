"""Streamlit Community Cloud entry point (main file at repo root)."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "app" / "streamlit_app.py"), run_name="__main__")
