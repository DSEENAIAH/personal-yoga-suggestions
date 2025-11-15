import nltk
try:
    nltk.download('punkt', quiet=True)
    print("NLTK punkt downloaded successfully")
except Exception as e:
    print(f"Warning: Could not download NLTK data: {e}")