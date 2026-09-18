import sqlite3
import os
import time
import json
import hashlib

# Connect to database with thread safety and timeout settings
DB_PATH = "approval.db"
conn = sqlite3.connect(
    DB_PATH,
    check_same_thread=False,
    timeout=10.0
)
cursor = conn.cursor()

# Create approvals table (advanced version)
cursor.execute("""
CREATE TABLE IF NOT EXISTS approvals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT,
    risk_score REAL,
    confidence_score REAL,
    status TEXT,
    reviewer_level TEXT,
    docker_code TEXT,
    k8s_code TEXT,
    cicd_code TEXT,
    explanation TEXT,
    metrics_json TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Create feedback table for RLHF
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT,
    original_docker TEXT,
    original_k8s TEXT,
    original_cicd TEXT,
    corrected_docker TEXT,
    corrected_k8s TEXT,
    corrected_cicd TEXT,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Create preferences table for personalization memory
cursor.execute("""
CREATE TABLE IF NOT EXISTS preferences(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pref_key TEXT UNIQUE,
    pref_value TEXT,
    description TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Create knowledge_base table for RAG
cursor.execute("""
CREATE TABLE IF NOT EXISTS knowledge_base(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT,
    project_description TEXT,
    docker_code TEXT,
    k8s_code TEXT,
    cicd_code TEXT,
    rating REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Create blockchain table for audit log
cursor.execute("""
CREATE TABLE IF NOT EXISTS blockchain(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_index INTEGER,
    timestamp TEXT,
    data_json TEXT,
    prev_hash TEXT,
    block_hash TEXT
)
""")

# Create agent_metrics table for analytics
cursor.execute("""
CREATE TABLE IF NOT EXISTS agent_metrics(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT,
    tokens_used INTEGER,
    cost REAL,
    response_time REAL,
    hallucination_score REAL,
    accuracy_score REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# Self-healing database migrations: add missing columns to approvals table if schema is outdated
try:
    cursor.execute("PRAGMA table_info(approvals)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    expected_columns = {
        "confidence_score": "REAL",
        "reviewer_level": "TEXT",
        "docker_code": "TEXT",
        "k8s_code": "TEXT",
        "cicd_code": "TEXT",
        "explanation": "TEXT",
        "metrics_json": "TEXT"
    }
    migration_needed = False
    for col_name, col_type in expected_columns.items():
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE approvals ADD COLUMN {col_name} {col_type}")
            migration_needed = True
    if migration_needed:
        conn.commit()
except sqlite3.Error as e:
    print(f"Error migrating approvals table: {e}")


def populate_mock_data_if_empty():
    """Populates the SQLite database with realistic HAULT portfolio data if empty."""
    cursor.execute("SELECT COUNT(*) FROM approvals")
    if cursor.fetchone()[0] == 0:
        # Insert mock approvals
        approvals = [
            ("Flask Web App", 12.0, 95.0, "Approved", "Auto-Approved", 
             "FROM python:3.10-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nEXPOSE 5000\nCMD [\"python\", \"app.py\"]", 
             "# Kubernetes Service...\napiVersion: v1\nkind: Service\nmetadata:\n  name: flask-service", 
             "# Github Workflow...\nname: CI\non:\n  push:\n    branches: [ main ]", 
             "Auto-approved due to >95% confidence score and standard Python pattern.", 
             '{"completeness": 96, "security": 94, "readability": 98, "hallucination": 2}', 
             "2026-06-23 10:14:00"),
            ("NodeJS Service", 35.0, 82.0, "Approved", "Junior/Senior Review", 
             "FROM node:18-alpine\nWORKDIR /app\nCOPY package*.json ./\nRUN npm install\nCOPY . .\nEXPOSE 3000\nCMD [\"node\", \"index.js\"]", 
             "# Kubernetes Deployment...\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: node-deployment", 
             "# CI/CD Work...\nname: Node Deploy", 
             "Approved after human review and custom adjustment of node base image to alpine.", 
             '{"completeness": 85, "security": 75, "readability": 90, "hallucination": 8}', 
             "2026-06-24 14:22:00"),
            ("Go Auth API", 65.0, 62.0, "Approved", "Domain Expert", 
             "FROM golang:1.20\nWORKDIR /app\nCOPY . .\nRUN go build -o main\nEXPOSE 8080\nCMD [\"./main\"]", 
             "# Kubernetes Manifests...", 
             "# CI/CD Deploy...", 
             "Domain Expert approved after verifying container port binding and security contexts.", 
             '{"completeness": 70, "security": 60, "readability": 80, "hallucination": 12}', 
             "2026-06-25 18:45:00"),
            ("React SPA Frontend", 18.0, 88.0, "Rejected", "Junior/Senior Review", 
             "FROM nginx:latest\nCOPY build/ /usr/share/nginx/html\nEXPOSE 80", 
             "# Deployment Manifest...", 
             "# CI/CD build config...", 
             "Rejected due to missing customized nginx.conf configuration routing.", 
             '{"completeness": 80, "security": 85, "readability": 92, "hallucination": 5}', 
             "2026-06-26 09:30:00")
        ]
        for app in approvals:
            cursor.execute("""
            INSERT INTO approvals (project_name, risk_score, confidence_score, status, reviewer_level, docker_code, k8s_code, cicd_code, explanation, metrics_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, app)
            
        # Insert mock feedback
        feedback = [
            ("NodeJS Service", "FROM node:latest", "FROM node:18-alpine", "Avoid latest tags and use smaller alpine base images to optimize build size.", "2026-06-24 14:15:00"),
            ("Go Auth API", "EXPOSE 80", "EXPOSE 8080", "Standardize container internal ports to non-privileged ports like 8080.", "2026-06-25 18:40:00")
        ]
        for fb in feedback:
            cursor.execute("""
            INSERT INTO feedback (project_name, original_docker, corrected_docker, corrected_k8s, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (fb[0], fb[1], fb[2], "", fb[3], fb[4]))
            
        # Insert mock preferences
        preferences = [
            ("python_base_image", "python:3.10-slim", "Derived from user feedback: prefer slim python base images.", "2026-06-23 10:20:00"),
            ("node_base_image", "node:18-alpine", "Derived from user feedback: prefer alpine node base images.", "2026-06-24 14:25:00")
        ]
        for pref in preferences:
            cursor.execute("""
            INSERT OR REPLACE INTO preferences (pref_key, pref_value, description, timestamp)
            VALUES (?, ?, ?, ?)
            """, pref)
            
        # Insert mock agent metrics
        metrics = [
            ("Flask Web App", 1200, 0.00042, 4.5, 2.0, 95.0, "2026-06-23 10:13:00"),
            ("NodeJS Service", 2400, 0.00085, 7.2, 5.0, 88.0, "2026-06-24 14:10:00"),
            ("Go Auth API", 3100, 0.00115, 9.8, 10.0, 80.0, "2026-06-25 18:35:00"),
            ("React SPA Frontend", 1800, 0.00062, 5.1, 3.0, 89.0, "2026-06-26 09:28:00")
        ]
        for met in metrics:
            cursor.execute("""
            INSERT INTO agent_metrics (project_name, tokens_used, cost, response_time, hallucination_score, accuracy_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, met)
            
        # Insert mock knowledge base (RAG)
        kb = [
            ("Flask Web App Template", "Python Flask framework using port 5000", 
             "FROM python:3.10-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nEXPOSE 5000\nCMD [\"python\", \"app.py\"]", 
             "# K8s Deployment...", "# CI/CD Work...", 95.0, "2026-06-23 10:15:00"),
            ("NodeJS Web App Template", "NodeJS Express framework using port 3000", 
             "FROM node:18-alpine\nWORKDIR /app\nCOPY package*.json ./\nRUN npm install\nCOPY . .\nEXPOSE 3000\nCMD [\"node\", \"index.js\"]", 
             "# K8s Deployment...", "# CI/CD Work...", 90.0, "2026-06-24 14:30:00")
        ]
        for item in kb:
            cursor.execute("""
            INSERT INTO knowledge_base (project_name, project_description, docker_code, k8s_code, cicd_code, rating, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, item)
            
        # Genesis Block
        timestamp = "2026-06-22 12:00:00"
        genesis_data = json.dumps({"message": "Genesis Block - HAULT DevOps Auditor Initiated"})
        prev_hash = "0" * 64
        genesis_string = f"0{timestamp}{genesis_data}{prev_hash}"
        genesis_hash = hashlib.sha256(genesis_string.encode('utf-8')).hexdigest()
        
        cursor.execute("""
        INSERT INTO blockchain (block_index, timestamp, data_json, prev_hash, block_hash)
        VALUES (?, ?, ?, ?, ?)
        """, (0, timestamp, genesis_data, prev_hash, genesis_hash))
        
        # Block 1 - Flask Web App Approval
        b1_timestamp = "2026-06-23 10:14:00"
        b1_data = json.dumps({"project_name": "Flask Web App", "status": "Approved", "reviewer": "System - Auto-Approved", "confidence": 95.0})
        b1_string = f"1{b1_timestamp}{b1_data}{genesis_hash}"
        b1_hash = hashlib.sha256(b1_string.encode('utf-8')).hexdigest()
        
        cursor.execute("""
        INSERT INTO blockchain (block_index, timestamp, data_json, prev_hash, block_hash)
        VALUES (?, ?, ?, ?, ?)
        """, (1, b1_timestamp, b1_data, genesis_hash, b1_hash))
        
        conn.commit()

populate_mock_data_if_empty()