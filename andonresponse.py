from app import create_app, db
from app.models import User, KPI, Area, Shift, Schedule
from functions.text import convert_text_area_to_list as conv
import datetime
from config import Config


app = create_app(config_class=Config)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'KPI': KPI, 'Area': Area,
            'Shift': Shift, 'Schedule': Schedule, 'datetime': datetime,
            'conv': conv}
