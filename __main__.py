from itertools import islice, takewhile, count
import os
import dateutil.parser
from datetime import datetime
from birdy.twitter import StreamClient
from pymongo import MongoClient, UpdateOne

consumer_token = os.environ.get('T_CONSUMER_TOKEN')
consumer_secret = os.environ.get('T_CONSUMER_SECRET')
access_token = os.environ.get('T_ACCESS_TOKEN')
access_token_secret = os.environ.get('T_TOKEN_SECRET')

def prepare_entry(status):
    return {
        '_id': 'tw:' + str(status.id),
        'published': dateutil.parser.parse(status.created_at),
        'added': datetime.utcnow(),
        'content': {
            'author': status.user.screen_name,
            'body': status.text
        }
    }

def chunk(n, it):
    src = iter(it)
    return takewhile(bool, (list(islice(src, n)) for _ in count(0)))

def read_and_write(client, resource):
    collection = client['newsfilter'].alerts
    prepared = (prepare_entry(entry) for entry in resource.stream() if entry.get('id'))
    chunked = chunk(20, prepared)
    for c in chunked:
        requests = [ UpdateOne({ '_id': obj['_id']},
                               { '$setOnInsert': obj }
                               , upsert=True) for obj in c]
        collection.bulk_write(requests, ordered=False)


def get_keywords(client):
    # TODO: get these from database, combine with feeds data, decide on view for user!

    return 'aegean drown, asylum detention death, asylum seeker death, bay of bengal drown, border death, cadaver inmigrante, canary islands migrant, christmas islands drown, inmigrante muerto, inmigrantes murieron, la bestia muerto, lampedusa death, libya migrant death, libya refugee death, limpopo crocodile, mediterranean migrant dead, migrant death, migrant death, migrant detention death, migrant missing, migrant suicide, migrante muerto, migrants die, migrants drown, migration dead, migration death, migration detention death, migration missing, migration suicide, refugee dead, refugee death, refugee detention death, refugee missing, refugiado muerto, rio bravo ahogado, rio bravo muerto, rio grande death, rio grande drown,  rohingya dead, rohingya drown, sueno americano muerto, sueno americano ahogado'


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
    read_and_write(client, resource)
