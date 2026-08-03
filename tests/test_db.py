
import sys; sys.path.append('src')
from core.config import config
print('DB PATH:', config.data_dir)
from database.database import DB_PATH, DATABASE_URL
print('URL:', DATABASE_URL)

