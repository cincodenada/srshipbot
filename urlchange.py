#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import yaml
import sys
import traceback

'''USER CONFIGURATION'''

config = yaml.load(open('config.yaml','r'))

'''All done!'''

PLEN = len(config['parentstring'])
WAITS = str(config['wait'])

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(**config['auth'])

def checkItem(id, text):
    result = []
    if config['parentstring'].lower() in text.lower():
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [id])
        if not cur.fetchone():
            textsplit = text.split()
            print(id)
            for sent in textsplit:
                if config['parentstring'].lower() in sent.lower():
                    try:
                        url = sent.lower().replace(config['parentstring'].lower(), config['replacestring'])
                        if '(' in url:
                            url = url[url.index('(')+1:]
                            url = url.replace(')', '')
                        int(url[PLEN:-1])
                        result.append(url)
                    except ValueError:
                        print('Not a valid url')
                    except AttributeError:
                        print('Comment author does not exist')
                    except Exception:
                        print('Error.')

            cur.execute('INSERT INTO oldposts VALUES(?)', [id])

            if len(result) > 0:
                final = config['header'] + '\n\n'.join(result)
                return final;

    return None

def scanSub():
    print('Searching '+ config['subreddit'] + ' comments...')
    subreddit = r.subreddit(config['subreddit'])
    posts = subreddit.comments(limit=config['maxposts'])
    for post in posts:
        if post.author and post.author.name.lower() != config['auth']['username'].lower():
            reply = checkItem(post.id, post.body)
            if(reply is not None):
                post.reply(reply % ('comment'))

    if(config['maxthreads'] > 0):
        print('Searching '+ config['subreddit'] + ' threads...')
        threads = subreddit.new(limit=config['maxthreads'])
        for thread in threads:
            if(thread.is_self):
                reply = checkItem(thread.name, thread.selftext)
            else:
                reply = checkItem(thread.name, thread.url)

            if(reply is not None):
                thread.reply(reply % ('post'))

    sql.commit()

while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', str(e))
        print(traceback.format_exc())
    print('Running again in ' + WAITS + ' seconds \n')
    sys.stdout.flush()
    sql.commit()
    time.sleep(config['wait'])
