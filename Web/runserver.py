"""
This script runs the HomeServer application using a development server.
"""

from os import environ
from ClimateControl import app

if __name__ == '__main__':
    HOST = "0.0.0.0"
    PORT = int(environ.get('SERVER_PORT', '8080'))
    
    app.run(HOST, PORT)
