import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app

# Ajoutez cette ligne
app.config.suppress_callback_exceptions = True

if __name__ == "__main__":
    app.run(
        host='0.0.0.0', 
        port=8000,
        debug=True
    )