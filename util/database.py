# from pymongo import MongoClient
import redis
from elasticsearch import Elasticsearch


dev_server = 'localhost'
prod_server = '159.203.170.25'


def get_redis_conn():
    return redis.Redis(host=prod_server)


def get_es_client():
    return Elasticsearch(hosts=['elasticsearch:9200'])
