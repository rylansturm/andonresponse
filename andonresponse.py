from app import create_app, db
from app.models import User, KPI, Area


app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'KPI': KPI, 'Area': Area}
