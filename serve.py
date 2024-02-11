from waitress import serve
from app import app  # Import your Flask app
host = '0.0.0.0'
port = 8000 
print(f"App listening on {host}:{port}")
serve(app, host=host , port=port)
