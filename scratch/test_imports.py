import sys
import os

# Append project directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Testing database.db import...")
    from database.db import conn, cursor, populate_mock_data_if_empty
    print("Success.")

    print("Testing agents.github_agent import...")
    from agents.github_agent import get_repo_readme
    print("Success.")

    print("Testing agents.orchestrator import...")
    from agents.orchestrator import run_orchestration_pipeline, extract_json
    print("Success.")

    print("Testing utils.pdf_generator import...")
    from utils.pdf_generator import generate_pdf
    print("Success.")

    print("Testing utils.blockchain import...")
    from utils.blockchain import add_blockchain_block, verify_chain_integrity, init_blockchain
    print("Success.")

    print("Checking database tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:", [t[0] for t in tables])
    
    print("All modules and DB tables validated successfully!")
except Exception as e:
    print("Import or DB validation failed:", e)
    sys.exit(1)
