from config import model
def kubernetes_agent(project_description):
    prompt = f"""
    Generate Kubernetes Deployment YAML.
    Project:
    {project_description}
    """
    response = model.generate_content(prompt)
    return response.text