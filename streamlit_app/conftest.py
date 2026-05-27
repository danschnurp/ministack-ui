"""
pytest configuration — adds streamlit_app root to sys.path so that
`from aws_client import client` and `from pages.X import Y` resolve
the same way they do when streamlit runs app.py.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
