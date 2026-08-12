from app.main import app
from sqlalchemy.orm import configure_mappers

try:
    configure_mappers()
    print('MAPPERS OK')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()