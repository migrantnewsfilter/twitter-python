from itertools import islice, takewhile, count
import os
import dateutil.parser
from datetime import datetime
from birdy.twitter import StreamClient
from pymongo import MongoClient, UpdateOne
from indexing_utils import chunk

consumer_token = os.environ.get('T_CONSUMER_TOKEN')
consumer_secret = os.environ.get('T_CONSUMER_SECRET')
access_token = os.environ.get('T_ACCESS_TOKEN')
access_token_secret = os.environ.get('T_TOKEN_SECRET')

def prepare_entry(status):
    user = status.user.screen_name
    _id = str(status.id)
    link = 'https://twitter.com/' + user + '/status/' + _id
    return {
        '_id': 'tw:' + _id,
        'published': dateutil.parser.parse(status.created_at),
        'added': datetime.utcnow(),
        'content': {
            'link': link,
            'author': user,
            'body': status.text
        }
    }

def read_and_write(client, resource):
    collection = client['newsfilter'].news
    prepared = (prepare_entry(entry) for entry in resource.stream() if entry.get('id'))
    chunked = chunk(20, prepared)
    for c in chunked:
        print 'TWITTER: writing tweets to DB'
        requests = [ UpdateOne({ '_id': obj['_id']},
                               { '$setOnInsert': obj }
                               , upsert=True) for obj in c]
        collection.bulk_write(requests, ordered=False)


def get_keywords(client):
    collection = client['newsfilter'].terms
    words = collection.find_one({ '_id': 'twitter' })
    return words.get('keywords')


if __name__ == '__main__':
    twitter_client = StreamClient(consumer_token,
                                  consumer_secret,
                                  access_token,
                                  access_token_secret)

    client = MongoClient(
        host = os.environ.get('MONGO_HOST') or None
    )

    keywords = get_keywords(client)
    resource = twitter_client.stream.statuses.filter.post(track=keywords)

    print 'TWITTER: connected to twitter. Beginning to read tweetz'
    read_and_write(client, resource)
