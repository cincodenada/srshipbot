#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import yaml

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

r = praw.Reddit(config['useragent'])
r.login(config['username'], config['password']) 

def scanSub():
    print('Searching '+ config['subreddit'] + '.')
    subreddit = r.get_subreddit(config['subreddit'])
    posts = subreddit.get_comments(limit=config['maxposts'])
    for post in posts:
        result = []
        pid = post.id
        pbody = post.body
        if config['parentstring'].lower() in pbody.lower():
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                pbodysplit = pbody.split()
                print(pid)
                for sent in pbodysplit:
                    if config['parentstring'].lower() in sent.lower():
                        try:
                            url = sent.replace(config['parentstring'], config['replacestring'])
                            if '(' in url:
                                url = url[url.index('(')+1:]
                                url = url.replace(')', '')                            
                            int(url[PLEN:-1])
                            pauthor = post.author.name
                            if pauthor !=config['username']:
                                result.append(url)
                        except ValueError:
                            print('Not a valid url')
                        except AttributeError:
                            print('Comment author does not exist')
                        except Exception:
                            print('Error.')
                if len(result) > 0:
                    final = config['header'] + '\n\n'.join(result)
                    post.reply(final)
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])    
    sql.commit()

while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(config['wait'])
