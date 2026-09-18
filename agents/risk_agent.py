from config import model
def risk_agent(review):
    prompt = f"""
    Analyze deployment risk.
    
    Review:
    {review}
    """
    response = model.generate_content(prompt)
    return response.text