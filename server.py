import os
import io
import json
import time
import sqlite3
from typing import Optional, List, Dict, Any
from PIL import Image

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Project imports
from database.db import get_db_connection, populate_mock_data_if_empty
from agents.github_agent import get_repo_readme
from agents.orchestrator import run_orchestration_pipeline, extract_json
from utils.pdf_generator import generate_pdf
from utils.blockchain import add_blockchain_block, verify_chain_integrity, init_blockchain
from services.preference_service import extract_and_store_preference

# Initialize database mock data & blockchain genesis
populate_mock_data_if_empty()
init_blockchain()

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
REPORTS_DIR = os.path.join(STATIC_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

app = FastAPI(
    title="HAULT - Human-in-the-Loop DevOps Command Suite",
    description="Enterprise AI DevOps Command Center with multi-agent orchestration, human-in-the-loop review, and immutable cryptographic audit ledgers.",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Models
class GitHubReadmeRequest(BaseModel):
    repo: str

class QueueItemRequest(BaseModel):
    project_name: str
    risk_level: str
    confidence_score: float
    reviewer_level: str
    dockerfile: str
    kubernetes_yaml: str
    cicd_yaml: str
    explanation: Optional[str] = ""
    completeness: Optional[float] = 90.0
    security: Optional[float] = 85.0
    readability: Optional[float] = 95.0
    hallucination: Optional[float] = 5.0

class InstantApproveRequest(BaseModel):
    project_name: str
    risk_level: str
    confidence_score: float
    dockerfile: str
    kubernetes_yaml: str
    cicd_yaml: str
    explanation: Optional[str] = ""
    evidence: Optional[str] = ""
    completeness: Optional[float] = 90.0
    security: Optional[float] = 85.0
    readability: Optional[float] = 95.0
    hallucination: Optional[float] = 5.0

class AuditorActionRequest(BaseModel):
    action: str  # "approve" or "reject"
    reviewer_role: str
    docker_code: str
    k8s_code: str
    cicd_code: str
    reason: Optional[str] = ""

class PreferenceCreateRequest(BaseModel):
    pref_key: str
    pref_value: str
    description: Optional[str] = ""


# ==========================================
# PAGE ROUTE
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Web application template not found.")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


# ==========================================
# SYSTEM STATUS & CORE STATS
# ==========================================
@app.get("/api/status")
async def get_system_status():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM approvals")
    approvals_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM preferences")
    preferences_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM knowledge_base")
    kb_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM blockchain")
    blockchain_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM feedback")
    feedback_count = cur.fetchone()[0]
    
    conn.close()
    
    return {
        "status": "ONLINE",
        "nodes": {
            "planner_agent": "ONLINE",
            "coding_agent": "ONLINE",
            "critic_agent": "ONLINE",
            "scorer_agent": "ONLINE",
            "simulation_sandbox": "ONLINE",
            "blockchain_engine": "ONLINE"
        },
        "stats": {
            "approvals": approvals_count,
            "preferences": preferences_count,
            "knowledge_base": kb_count,
            "blockchain_blocks": blockchain_count,
            "feedback_records": feedback_count
        }
    }


# ==========================================
# GITHUB README RETRIEVER
# ==========================================
@app.post("/api/github/readme")
async def fetch_github_readme(req: GitHubReadmeRequest):
    repo = req.repo.strip()
    if not repo:
        raise HTTPException(status_code=400, detail="Repository path required.")
    
    try:
        readme = get_repo_readme(repo)
        return {"success": True, "repo": repo, "readme": readme}
    except Exception as e:
        # Graceful simulated fallback
        fallback = f"""# {repo}
Simulated repository context extracted for DevOps orchestration.
- Target Architecture: Microservice
- Standard ports: 8000 / 3000
- Health route: /healthz
- Tested environments: Production, Staging
"""
        return {
            "success": True,
            "repo": repo,
            "readme": fallback,
            "notice": f"Retrieved via simulated fallback: {str(e)}"
        }


# ==========================================
# MULTI-AGENT ORCHESTRATION PIPELINE
# ==========================================
@app.post("/api/pipeline/run")
async def run_pipeline(request: Request):
    content_type = request.headers.get("content-type", "")
    project_description = ""
    repo_name = None
    voice_pref = None
    image_obj = None

    if "application/json" in content_type:
        body = await request.json()
        project_description = body.get("project_description", "")
        repo_name = body.get("repo_name")
        voice_pref = body.get("voice_pref")
    else:
        form = await request.form()
        project_description = str(form.get("project_description", ""))
        repo_name = form.get("repo_name")
        voice_pref = form.get("voice_pref")
        image_file = form.get("image")
        if image_file and hasattr(image_file, "filename") and image_file.filename:
            try:
                image_bytes = await image_file.read()
                if image_bytes:
                    image_obj = Image.open(io.BytesIO(image_bytes))
            except Exception as e:
                print(f"Warning processing image: {e}")

    if not project_description.strip():
        raise HTTPException(status_code=400, detail="project_description is required.")

    # Build full prompt description
    full_description = project_description
    if repo_name and str(repo_name).strip():
        try:
            readme = get_repo_readme(str(repo_name).strip())
            full_description += f"\n\nGithub Repository Context:\n{readme}"
        except Exception:
            pass

    if voice_pref and str(voice_pref).strip():
        full_description += f"\n\nHuman Voice Preference Instructions:\n{str(voice_pref).strip()}"

    try:
        result = run_orchestration_pipeline(
            full_description,
            uploaded_image=image_obj
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {str(e)}")



# ==========================================
# APPROVAL QUEUE ENDPOINTS
# ==========================================
@app.get("/api/approvals")
async def list_approvals(status: Optional[str] = Query(None)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if status and status.lower() != "all":
        cur.execute("""
        SELECT id, project_name, risk_score, confidence_score, status, reviewer_level, 
               explanation, metrics_json, timestamp 
        FROM approvals 
        WHERE status = ? 
        ORDER BY id DESC
        """, (status,))
    else:
        cur.execute("""
        SELECT id, project_name, risk_score, confidence_score, status, reviewer_level, 
               explanation, metrics_json, timestamp 
        FROM approvals 
        ORDER BY id DESC
        """)
        
    rows = cur.fetchall()
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "project_name": r["project_name"],
            "risk_score": r["risk_score"],
            "confidence_score": r["confidence_score"],
            "status": r["status"],
            "reviewer_level": r["reviewer_level"],
            "explanation": r["explanation"],
            "metrics": json.loads(r["metrics_json"]) if r["metrics_json"] else {},
            "timestamp": r["timestamp"]
        })
    conn.close()
    return {"approvals": items}


@app.get("/api/approvals/{app_id}")
async def get_approval_detail(app_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, project_name, risk_score, confidence_score, status, reviewer_level, 
           docker_code, k8s_code, cicd_code, explanation, metrics_json, timestamp 
    FROM approvals 
    WHERE id = ?
    """, (app_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Approval request not found.")
        
    return {
        "id": row["id"],
        "project_name": row["project_name"],
        "risk_score": row["risk_score"],
        "confidence_score": row["confidence_score"],
        "status": row["status"],
        "reviewer_level": row["reviewer_level"],
        "docker_code": row["docker_code"] or "",
        "k8s_code": row["k8s_code"] or "",
        "cicd_code": row["cicd_code"] or "",
        "explanation": row["explanation"] or "",
        "metrics": json.loads(row["metrics_json"]) if row["metrics_json"] else {},
        "timestamp": row["timestamp"]
    }


@app.post("/api/approvals")
async def queue_pipeline_result(req: QueueItemRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    
    metrics = {
        "completeness": req.completeness,
        "security": req.security,
        "readability": req.readability,
        "hallucination": req.hallucination
    }
    
    cur.execute("""
    INSERT INTO approvals (project_name, risk_score, confidence_score, status, reviewer_level, docker_code, k8s_code, cicd_code, explanation, metrics_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        req.project_name[:50],
        req.risk_level,
        req.confidence_score,
        "Pending Review" if req.reviewer_level != "Auto-Approved" else "Approved",
        req.reviewer_level,
        req.dockerfile,
        req.kubernetes_yaml,
        req.cicd_yaml,
        req.explanation or "Queued via Agent Console.",
        json.dumps(metrics)
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    
    return {"success": True, "id": new_id, "message": "Project added to review queue."}


@app.post("/api/approvals/instant-approve")
async def instant_approve_result(req: InstantApproveRequest):
    # Add to blockchain ledger
    block_data = {
        "project_name": req.project_name[:50],
        "status": "Approved",
        "reviewer": "Immediate-Developer-Commit",
        "confidence_score": req.confidence_score,
        "risk_level": req.risk_level
    }
    new_hash = add_blockchain_block(block_data)
    
    # Save to SQLite approvals
    conn = get_db_connection()
    cur = conn.cursor()
    
    metrics = {
        "completeness": req.completeness,
        "security": req.security,
        "readability": req.readability,
        "hallucination": req.hallucination
    }
    
    cur.execute("""
    INSERT INTO approvals (project_name, risk_score, confidence_score, status, reviewer_level, docker_code, k8s_code, cicd_code, explanation, metrics_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        req.project_name[:50],
        req.risk_level,
        req.confidence_score,
        "Approved",
        "Instant Approve",
        req.dockerfile,
        req.kubernetes_yaml,
        req.cicd_yaml,
        "Immediate developer sign-off.",
        json.dumps(metrics)
    ))
    new_id = cur.lastrowid
    
    # Save to knowledge base for RAG
    cur.execute("""
    INSERT INTO knowledge_base (project_name, project_description, docker_code, k8s_code, cicd_code, rating)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        f"{req.project_name[:40]} Template",
        req.project_name,
        req.dockerfile,
        req.kubernetes_yaml,
        req.cicd_yaml,
        96.0
    ))
    conn.commit()
    conn.close()
    
    # Generate PDF report
    pdf_filename = f"report_{new_id}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    generate_pdf(
        project=req.project_name[:50],
        review=req.explanation,
        risk=req.evidence,
        docker=req.dockerfile,
        k8s=req.kubernetes_yaml,
        cicd=req.cicd_yaml,
        confidence_score=req.confidence_score,
        risk_level=req.risk_level,
        audit_hash=new_hash,
        output_path=pdf_path
    )
    
    return {
        "success": True,
        "id": new_id,
        "audit_hash": new_hash,
        "pdf_download_url": f"/api/report/{new_id}/pdf"
    }


@app.post("/api/approvals/{app_id}/action")
async def handle_auditor_action(app_id: int, req: AuditorActionRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, project_name, docker_code, k8s_code, cicd_code FROM approvals WHERE id = ?", (app_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Approval request not found.")
        
    project_name = row["project_name"]
    orig_docker = row["docker_code"] or ""
    orig_k8s = row["k8s_code"] or ""
    orig_cicd = row["cicd_code"] or ""
    
    if req.action == "approve":
        docker_changed = orig_docker.strip() != req.docker_code.strip()
        k8s_changed = orig_k8s.strip() != req.k8s_code.strip()
        cicd_changed = orig_cicd.strip() != req.cicd_code.strip()
        corrections_made = docker_changed or k8s_changed or cicd_changed
        
        pref_extracted = None
        if corrections_made and req.reason:
            pref_extracted = extract_and_store_preference(
                project_name,
                orig_docker, req.docker_code,
                orig_k8s, req.k8s_code,
                orig_cicd, req.cicd_code,
                req.reason,
                db_conn=conn
            )
            # Log correction in feedback table
            cur.execute("""
            INSERT INTO feedback (project_name, original_docker, corrected_docker, corrected_k8s, reason)
            VALUES (?, ?, ?, ?, ?)
            """, (project_name, orig_docker, req.docker_code, req.k8s_code, req.reason))
            
        # Update approval
        cur.execute("""
        UPDATE approvals
        SET status = 'Approved', docker_code = ?, k8s_code = ?, cicd_code = ?, explanation = ?
        WHERE id = ?
        """, (
            req.docker_code,
            req.k8s_code,
            req.cicd_code,
            f"Approved by {req.reviewer_role}. Adjustments: {req.reason or 'None'}",
            app_id
        ))
        
        # Save to RAG knowledge base
        cur.execute("""
        INSERT INTO knowledge_base (project_name, project_description, docker_code, k8s_code, cicd_code, rating)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"{project_name[:40]} Approved Pattern",
            f"Audited by {req.reviewer_role}.",
            req.docker_code,
            req.k8s_code,
            req.cicd_code,
            98.0
        ))
        
        # Append block to blockchain
        block_data = {
            "project_name": project_name,
            "status": "Approved",
            "reviewer": req.reviewer_role,
            "corrections_made": "Yes" if corrections_made else "No",
            "reason": req.reason or "Approved"
        }
        new_hash = add_blockchain_block(block_data, db_conn=conn)
        conn.commit()
        conn.close()
        
        # Generate PDF report
        pdf_path = os.path.join(REPORTS_DIR, f"report_{app_id}.pdf")
        generate_pdf(
            project=project_name,
            review=f"Approved by {req.reviewer_role}",
            risk=req.reason or "Deployment verified",
            docker=req.docker_code,
            k8s=req.k8s_code,
            cicd=req.cicd_code,
            confidence_score=95,
            risk_level="Low",
            audit_hash=new_hash,
            output_path=pdf_path
        )
        
        return {
            "success": True,
            "status": "Approved",
            "audit_hash": new_hash,
            "preference_extracted": pref_extracted,
            "pdf_url": f"/api/report/{app_id}/pdf"
        }
        
    elif req.action == "reject":
        cur.execute("""
        UPDATE approvals
        SET status = 'Rejected', explanation = ?
        WHERE id = ?
        """, (f"Rejected by {req.reviewer_role}. Notes: {req.reason or 'No reason provided'}", app_id))
        
        block_data = {
            "project_name": project_name,
            "status": "Rejected",
            "reviewer": req.reviewer_role,
            "reason": req.reason or "Rejected"
        }
        new_hash = add_blockchain_block(block_data, db_conn=conn)
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "status": "Rejected",
            "audit_hash": new_hash
        }
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")


# ==========================================
# PREFERENCE MEMORY ENDPOINTS
# ==========================================
@app.get("/api/preferences")
async def list_preferences():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, pref_key, pref_value, description, timestamp FROM preferences ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    
    return {
        "preferences": [
            {
                "id": r["id"],
                "pref_key": r["pref_key"],
                "pref_value": r["pref_value"],
                "description": r["description"],
                "timestamp": r["timestamp"]
            }
            for r in rows
        ]
    }


@app.post("/api/preferences")
async def add_preference(req: PreferenceCreateRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO preferences (pref_key, pref_value, description)
    VALUES (?, ?, ?)
    """, (req.pref_key.strip(), req.pref_value.strip(), req.description.strip()))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Preference rule added to memory."}


@app.delete("/api/preferences/{pref_id}")
async def delete_preference(pref_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM preferences WHERE id = ?", (pref_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Rule ID {pref_id} deleted."}


# ==========================================
# RAG KNOWLEDGE BASE ENDPOINTS
# ==========================================
@app.get("/api/knowledge-base")
async def list_knowledge_base():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, project_name, project_description, rating, timestamp FROM knowledge_base ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    
    return {
        "knowledge_base": [
            {
                "id": r["id"],
                "project_name": r["project_name"],
                "project_description": r["project_description"],
                "rating": r["rating"],
                "timestamp": r["timestamp"]
            }
            for r in rows
        ]
    }


@app.get("/api/knowledge-base/{kb_id}")
async def get_knowledge_base_template(kb_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, project_name, project_description, docker_code, k8s_code, cicd_code, rating, timestamp FROM knowledge_base WHERE id = ?", (kb_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Template not found.")
        
    return {
        "id": row["id"],
        "project_name": row["project_name"],
        "project_description": row["project_description"],
        "docker_code": row["docker_code"] or "",
        "k8s_code": row["k8s_code"] or "",
        "cicd_code": row["cicd_code"] or "",
        "rating": row["rating"],
        "timestamp": row["timestamp"]
    }


# ==========================================
# ANALYTICS & TELEMETRY ENDPOINT
# ==========================================
@app.get("/api/analytics")
async def get_analytics():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM approvals")
    total_runs = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM approvals WHERE status='Approved'")
    approved_runs = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM approvals WHERE status='Rejected'")
    rejected_runs = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM approvals WHERE status='Pending Review'")
    pending_runs = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM feedback")
    correction_count = cur.fetchone()[0]
    
    saved_hours = round((approved_runs * 0.75) + (rejected_runs * 0.2) + (correction_count * 0.3), 1)
    
    cur.execute("SELECT id, project_name, tokens_used, cost, response_time, hallucination_score, accuracy_score, timestamp FROM agent_metrics ORDER BY id ASC")
    metric_rows = cur.fetchall()
    
    cur.execute("SELECT project_name, original_docker, corrected_docker, reason, timestamp FROM feedback ORDER BY id DESC LIMIT 20")
    feedback_rows = cur.fetchall()
    
    conn.close()
    
    total_decided = approved_runs + rejected_runs
    success_rate = round((approved_runs / max(1, total_decided)) * 100, 1) if total_decided > 0 else 100.0
    
    return {
        "kpi": {
            "total_runs": total_runs,
            "approved_runs": approved_runs,
            "rejected_runs": rejected_runs,
            "pending_runs": pending_runs,
            "success_rate": success_rate,
            "correction_count": correction_count,
            "saved_hours": saved_hours
        },
        "metrics_series": [
            {
                "id": r["id"],
                "project_name": r["project_name"],
                "tokens": r["tokens_used"],
                "cost": round(r["cost"], 5),
                "response_time": r["response_time"],
                "hallucination_score": r["hallucination_score"],
                "accuracy_score": r["accuracy_score"],
                "timestamp": r["timestamp"]
            }
            for r in metric_rows
        ],
        "decisions": {
            "approved": approved_runs,
            "rejected": rejected_runs,
            "pending": pending_runs
        },
        "feedback_history": [
            {
                "project_name": f["project_name"],
                "original_docker": f["original_docker"],
                "corrected_docker": f["corrected_docker"],
                "reason": f["reason"],
                "timestamp": f["timestamp"]
            }
            for f in feedback_rows
        ]
    }


# ==========================================
# BLOCKCHAIN LEDGER ENDPOINTS
# ==========================================
@app.get("/api/blockchain")
async def get_blockchain_ledger():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT block_index, timestamp, data_json, prev_hash, block_hash FROM blockchain ORDER BY block_index ASC")
    rows = cur.fetchall()
    conn.close()
    
    blocks = []
    for r in rows:
        try:
            payload = json.loads(r["data_json"])
        except Exception:
            payload = r["data_json"]
        blocks.append({
            "block_index": r["block_index"],
            "timestamp": r["timestamp"],
            "data": payload,
            "prev_hash": r["prev_hash"],
            "block_hash": r["block_hash"]
        })
    return {"blocks": blocks}


@app.post("/api/blockchain/verify")
async def verify_blockchain():
    is_valid, logs = verify_chain_integrity()
    return {
        "is_valid": is_valid,
        "logs": logs,
        "total_blocks": len(logs)
    }


# ==========================================
# PDF AUDIT REPORT EXPORT
# ==========================================
@app.get("/api/report/{app_id}/pdf")
async def download_pdf_report(app_id: int):
    pdf_filename = f"report_{app_id}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    
    # If not already generated on disk, generate now
    if not os.path.exists(pdf_path):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT project_name, confidence_score, risk_score, docker_code, k8s_code, cicd_code, explanation FROM approvals WHERE id = ?", (app_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Report target project not found.")
            
        generate_pdf(
            project=row["project_name"],
            review=row["explanation"] or "DevOps Audit Report",
            risk="System verified",
            docker=row["docker_code"] or "",
            k8s=row["k8s_code"] or "",
            cicd=row["cicd_code"] or "",
            confidence_score=row["confidence_score"] or 90,
            risk_level=str(row["risk_score"]),
            audit_hash="CHAIN-SEALED",
            output_path=pdf_path
        )
        
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"HAULT_{app_id}_Audit_Report.pdf"
    )


# ==========================================
# DATABASE UTILITIES
# ==========================================
@app.post("/api/database/clear")
async def clear_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM approvals")
    cur.execute("DELETE FROM feedback")
    cur.execute("DELETE FROM agent_metrics")
    cur.execute("DELETE FROM preferences")
    cur.execute("DELETE FROM knowledge_base")
    cur.execute("DELETE FROM blockchain")
    conn.commit()
    conn.close()
    return {"success": True, "message": "Database purged."}


@app.post("/api/database/repopulate")
async def repopulate_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM approvals")
    cur.execute("DELETE FROM feedback")
    cur.execute("DELETE FROM agent_metrics")
    cur.execute("DELETE FROM preferences")
    cur.execute("DELETE FROM knowledge_base")
    cur.execute("DELETE FROM blockchain")
    conn.commit()
    conn.close()
    
    populate_mock_data_if_empty()
    init_blockchain()
    return {"success": True, "message": "Mock dataset and blockchain genesis restored."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("\n" + "="*60)
    print("🛸 HAULT: Human-in-the-Loop DevOps Command Suite")
    print(f"🚀 Launching Web Application on: http://{host}:{port}")
    print("="*60 + "\n")
    uvicorn.run("server:app", host=host, port=port)

