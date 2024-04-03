import logging
import pymongo

log = logging.getLogger()

class Mongo():
    def __init__(self,**config):
        self.client = None
        if 'ssl=true' in config['uri']:
            self.client = pymongo.MongoClient(config["uri"], tlsCAFile=certifi.where())
        else:
            self.client = pymongo.MongoClient(config["uri"])
        
        self.database = config['database']
        self.db = self.client[self.database]
        self.collection = self.db[config['collection']]

    def drop(self):
        self.client.drop_database(self.database)

    def create_ttl(self,key,sec):
        self.collection.create_index(
            key, expireAfterSeconds=sec
            )

    def close(self):
        self.client.close()

