import certifi
import logging
import sqlite3

log = logging.getLogger()
        
class SQLite():
    def __init__(self):
        self.con = sqlite3.connect('ClimateControlDB')
        self.cur = self.con.cursor()
        
        self._initialize()
        
    def _initialize(self):
        table_schema = {
            'sensorout': {
                'date'  : 'DATE',
                'var'   : 'TEXT',
                'value' : 'FLOAT'
            }
        }
        
        result = self.cur.execute("SELECT * FROM sqlite_master WHERE type='table'")
        tables = result.fetchall()
        for table, cols in table_schema.items():
            if not any(item[1] == table for item in tables):
                query_params = []
                for col, dtype in cols.items():
                    query_params.append('{} {}'.format(col, dtype))
                query_string = "CREATE TABLE {}({})".format(table, ', '.join(query_params))
                
                log.info('Executing query string {}'.format(query_string))
                self.cur.execute(query_string)

        self.cur.execute("PRAGMA busy_timeout = 100;")
        
    def close(self):
        self.cur.close()
        self.con.close()

