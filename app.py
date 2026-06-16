# RiskNova — Hugging Face Spaces Entry Point
# This file is required by Hugging Face Spaces SDK
# It simply imports and runs the main Streamlit app

import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the API base URL to point to Render backend
os.environ.setdefault('API_BASE_URL', 'https://credit-risk-api-i7bq.onrender.com')

# Run the main app
from frontend.app import *
