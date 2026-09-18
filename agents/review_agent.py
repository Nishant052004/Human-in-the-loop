from config import model
def github_review_agent(code):
    prompt = f"""
    Review this repository and provide:
    1.Security Issues
    2. Code Quality Issues
    3. Improvements
    4. Deployment Suggestions
    Repository Content:
    {code}
    """
    response = model.generate_content(prompt)
    return response.text