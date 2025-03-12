import sys, os

# Add the application directory to the Python path
INTERP = os.path.join(os.environ['HOME'], '.venv', 'bin', 'python')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Path to your application directory
sys.path.insert(0, os.environ['HOME'])

# Import your Flask application
from app import app as application 