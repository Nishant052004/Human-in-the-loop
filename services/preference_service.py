import re
import json
from config import model
from database.db import get_db_connection
from agents.orchestrator import extract_json

def extract_and_store_preference(
    project_name,
    original_docker,
    corrected_docker,
    original_k8s,
    corrected_k8s,
    original_cicd,
    corrected_cicd,
    reason,
    db_conn=None
):
    """
    Analyze human corrections and extract user preferences automatically.
    Uses Gemini when configured, with a smart heuristic fallback when offline.
    Persists rule directly to the preferences table.
    """
    docker_changed = (original_docker or "").strip() != (corrected_docker or "").strip()
    k8s_changed = (original_k8s or "").strip() != (corrected_k8s or "").strip()
    cicd_changed = (original_cicd or "").strip() != (corrected_cicd or "").strip()
    
    if not (docker_changed or k8s_changed or cicd_changed):
        return None

    rule_data = None

    # 1. Attempt LLM Preference Extraction
    if model:
        prompt = f"""
        You are an AI Memory Assistant for a DevOps platform. A developer reviewed and corrected generated files for project '{project_name}'.
        Analyze the corrections and infer an actionable operational policy rule.

        Human Auditor Reason:
        "{reason}"

        Original Dockerfile:
        {original_docker if docker_changed else '[Unchanged]'}

        Corrected Dockerfile:
        {corrected_docker if docker_changed else '[Unchanged]'}

        Original Kubernetes YAML:
        {original_k8s if k8s_changed else '[Unchanged]'}

        Corrected Kubernetes YAML:
        {corrected_k8s if k8s_changed else '[Unchanged]'}

        Original CI/CD:
        {original_cicd if cicd_changed else '[Unchanged]'}

        Corrected CI/CD:
        {corrected_cicd if cicd_changed else '[Unchanged]'}

        Formulate a clear preference rule. Respond with a JSON block only:
        {{
            "pref_key": "unique_lowercase_key_with_underscores",
            "pref_value": "specific value or rule description",
            "description": "why this preference rule was derived"
        }}
        """
        try:
            resp = model.generate_content(prompt).text
            rule_data = extract_json(resp)
        except Exception as e:
            print(f"LLM Preference Extraction Notice: {e}. Using rule inference engine.")

    # 2. Heuristic Rule Inference Fallback (Offline / Resilient Mode)
    if not rule_data:
        rule_key = "general_devops_rule"
        rule_value = reason[:60] if reason else "Follow team best practices"
        description = reason or f"Correction on {project_name}"

        if docker_changed:
            # Check for FROM image line
            from_match = re.search(r'FROM\s+([^\s\n]+)', corrected_docker or "", re.IGNORECASE)
            if from_match:
                img = from_match.group(1).lower()
                if "python" in img:
                    rule_key = "python_base_image"
                    rule_value = from_match.group(1)
                elif "node" in img:
                    rule_key = "node_base_image"
                    rule_value = from_match.group(1)
                elif "alpine" in img:
                    rule_key = "alpine_container_policy"
                    rule_value = from_match.group(1)
                else:
                    rule_key = "docker_base_image"
                    rule_value = from_match.group(1)
            elif "expose" in (reason or "").lower() or "port" in (reason or "").lower():
                port_match = re.search(r'EXPOSE\s+(\d+)', corrected_docker or "", re.IGNORECASE)
                if port_match:
                    rule_key = "container_port_policy"
                    rule_value = f"port {port_match.group(1)}"
            else:
                rule_key = f"docker_{project_name.lower().replace(' ', '_')[:20]}_rule"

        elif k8s_changed:
            if "port" in (reason or "").lower():
                rule_key = "k8s_service_port_policy"
            elif "replica" in (reason or "").lower():
                rule_key = "k8s_replica_policy"
            else:
                rule_key = "k8s_manifest_policy"
            rule_value = reason[:50]

        elif cicd_changed:
            rule_key = "cicd_pipeline_policy"
            rule_value = reason[:50]

        rule_data = {
            "pref_key": rule_key,
            "pref_value": rule_value,
            "description": description
        }

    # 3. Persist to Database
    if rule_data and "pref_key" in rule_data and "pref_value" in rule_data:
        try:
            should_close = False
            if db_conn:
                conn_to_use = db_conn
            else:
                conn_to_use = get_db_connection()
                should_close = True
            cur = conn_to_use.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO preferences (pref_key, pref_value, description)
            VALUES (?, ?, ?)
            """, (rule_data['pref_key'], rule_data['pref_value'], rule_data.get('description', 'Derived from human review')))
            conn_to_use.commit()
            if should_close:
                conn_to_use.close()
            return rule_data
        except Exception as e:
            print(f"Error persisting preference to database: {e}")

    return rule_data

