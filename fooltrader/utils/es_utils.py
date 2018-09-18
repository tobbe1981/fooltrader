# -*- coding: utf-8 -*-
import logging
from ast import literal_eval

from elasticsearch_dsl import Index

from fooltrader import es_client
from fooltrader.utils.time_utils import to_pd_timestamp

logger = logging.getLogger(__name__)


def es_get_latest_record(index, time_field='timestamp', query=None):
    body = '''
{
    "query": {
        "match_all": {}
    },
    "size": 1,
    "sort": [
        {
            "timestamp": {
                "order": "desc"
            }
        }
    ]
}
'''
    if time_field != 'timestamp':
        body = body.replace('timestamp', time_field)

    body = literal_eval(body)
    if query:
        body['query'] = query

    try:
        logger.info("search index:{},body:{}".format(index, body))
        response = es_client.search(index=index, body=body)
        if response['hits']['hits']:
            return response['hits']['hits'][0]['_source']
    except Exception as e:
        logger.warning(e)
    return None


def es_get_latest_timestamp(index, time_field='timestamp', query=None):
    latest_record = es_get_latest_record(index, time_field, query)
    if latest_record:
        return to_pd_timestamp(latest_record['timestamp'])


def es_delete(index, query=None):
    if query:
        body = {"query": query}
        es_client.delete_by_query(index=index, body=body,ignore_unavailable=True)
    else:
        es_client.delete(index=index)


def es_index_mapping(index_name, doc_type, force=False):
    # 创建索引
    index = Index(index_name)
    index.doc_type(doc_type)

    if not index.exists():
        index.create()
    else:
        if force:
            index.upgrade()


def es_resp_to_payload(resp, csv=False):
    datas = [hit['_source'].to_dict() for hit in resp['hits']['hits']]

    if csv:
        datas = [[data['timestamp'], data['open'], data['high'], data['low'], data['close'], data['volume']] for data in
                 datas]

    return {
        'total': resp['hits']['total'],
        'data': datas
    }
