from app import create_app, db
from app.models import User, KPI, Area, Shift, Schedule
import datetime


app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'KPI': KPI, 'Area': Area,
            'Shift': Shift, 'Schedule': Schedule, 'datetime': datetime}
