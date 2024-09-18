import logging

from lib.db import SQLite

log = logging.getLogger()

class Sensor:
    def __init__(self, config):
        self._config = config
        self.db = SQLite()
        
    def _update_sensor_database(self, date, var, value):
        if not self._config.testing:
            query = "INSERT INTO sensorout (date,var,value) VALUES (?,?,?);"
            self.db.cur.execute(query, (date, var, float(value)))
            self.db.con.commit()
        
    def _close(self):
        self.db.close()