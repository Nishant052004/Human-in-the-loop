from config import model
def docker_agent(project_description):
    prompt = f"""
    Generate Dockerfile.
    Project:
    {project_description}
    """
    response = model.generate_content(prompt)
    return response.text