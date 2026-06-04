from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# @app.route('/api/users')
#def get_users():
#    users = [{"id": 1, "name": "Алиса"}, {"id": 2, "name": "Борис"}]
#    return jsonify(users)