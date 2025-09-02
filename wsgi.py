import sys
import os

from app import app

app.config.suppress_callback_exceptions = True

if __name__ == "__main__":
    app.run(
        host='0.0.0.0', 
        port=8000,
        debug=True
    )