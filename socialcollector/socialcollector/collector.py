'''

'''
import settings
import psycopg2
import requests
import json
import oauth2
from datetime import datetime
from dateutil import parser, tz
from xml.etree import ElementTree as ET

DJANGO_DB = settings.DATABASES['default']
DATA_DB = settings.DATABASES['data_db']

utc_zone = tz.gettz('UTC')

INSTA_LIMIT = 20
TWEET_LIMIT = 200
FOURSQUARE_LIMIT = 250
FLICKR_LIMIT = 400
OSM_LIMIT = 100
MAPILLARY_LIMIT = 1000
STRAVA_LIMIT = 100
INAT_LIMIT = 200
MEETUP_LIMIT = 200
FB_LIMIT = 100

class DBHandler():
    def __init__(self):
        self.django_db = psycopg2.connect(host=DJANGO_DB['HOST'], port=DJANGO_DB['PORT'], user=DJANGO_DB['USER'], password=DJANGO_DB['PASSWORD'], dbname=DJANGO_DB['NAME'])
        self.data_db = psycopg2.connect(host=DATA_DB['HOST'], port=DATA_DB['PORT'], user=DATA_DB['USER'], password=DATA_DB['PASSWORD'], dbname=DATA_DB['NAME'])

    def getAllParams(self):
        sql = '''
          select provider.id as acc_id, provider.provider, provider.user_id, provider.uid, token.token, token.token_secret, provider.client_id, provider.secret, provider.extra_data::json
                from (select distinct on (provider, user_id) acc.id, acc.provider, acc.user_id, acc.uid, app.id app_id, app.client_id, app.secret, acc.extra_data
                from socialaccount_socialaccount acc, socialaccount_socialapp app where
                    acc.provider = app.provider order by provider, user_id, id asc) provider,
                    socialaccount_socialtoken token
            where provider.id = token.account_id
        '''
        cur =  self.django_db.cursor()
        data = []
        try:
            cur.execute(sql)
            user = cur.fetchall()
            for u in user:
                params = {
                    "platform": u[1],
                    "user_django": u[2],
                    "user_platform": u[3],
                    "access_token": u[4],
                    "token_secret":  u[5],
                    "client_id":  u[6],
                    "client_secret": u[7],
                }
                print params
                try:
                    print 'CHECK FOR LOGIN!!!!'
                    login = u[8]['login']
                    print login
                    params['login'] = login
                    data.append(params)
                except:
                    print 'ERROR IN LOGIN CHECK'
                    data.append(params)
        except Exception, e:
            print(Exception, e)

        return data

    def getUserParams(self, user_id, platform):
        sql = '''
          select provider.id as acc_id, provider.provider, provider.user_id, provider.uid, token.token, token.token_secret, provider.client_id, provider.secret, provider.extra_data::json
                from 
                    (
                    select distinct on (provider, user_id) acc.id, acc.provider, acc.user_id, acc.uid, app.id app_id, app.client_id, app.secret, acc.extra_data from 
                            socialaccount_socialaccount acc,
                            (select * from socialaccount_socialapp where provider = %s) app 
                        where
                            acc.provider = app.provider and
                            acc.user_id = %s order by provider, user_id, id asc
                    ) provider,
                    socialaccount_socialtoken token
            where provider.id = token.account_id
        '''
        cur =  self.django_db.cursor()
        try:
            cur.execute(sql, (platform, user_id))
            user = cur.fetchone()
            params = {
                    "platform": user[1],
                    "user_django": user[2],
                    "user_platform": user[3],
                    "access_token": user[4],
                    "token_secret":  user[5],
                    "client_id":  user[6],
                    "client_secret": user[7],
                }
            try:
                login = json.loads(user[8])['login']
                params['login'] = login
            except:
                pass
        except Exception, e:
            print(Exception, e)

        return params

    def downloadData(self, params, collector):
        print 'User id: %s,platform: %s' % (params['user_django'], params['platform'])
        if params['platform'] == 'instagram':
            collector.getInstaMedia(params, self.data_db)
        elif params['platform'] == 'twitter':
            collector.getTweets(params, self.data_db)
        elif params['platform'] == 'foursquare':
            collector.getFoursquareCheckins(params, self.data_db)
        elif params['platform'] == 'flickr':
            collector.getFlickrPhotos(params, self.data_db)
        elif params['platform'] == 'openstreetmap':
            collector.getOSMChangesets(params, self.data_db)
        elif params['platform'] == 'mapillary':
            collector.getMapillarySequences(params, self.data_db)
        elif params['platform'] == 'strava':
            collector.getStravaActivities(params, self.data_db)
        elif params['platform'] == 'inaturalist':
            collector.getInatObservations(params, self.data_db)
        elif params['platform'] == 'meetup':
            collector.getMeetups(params, self.data_db)

    def getNewUserParams(self):
        data_cur = self.data_db.cursor()
        params = self.getAllParams()
        fb_users = data_cur.execute('select array_agg(distinct user_id) from facebook_places')
        return params

    def setupTables(self):
        cursor = self.data_db.cursor()
        insta_table_sql = '''
            CREATE TABLE insta_media (
                    pid serial primary key,
        '''
        cursor.execute(insta_table_sql)

class DataCollector():
    def getInstaMedia(self, user_params, db):
        url = 'https://api.instagram.com/v1/users/self/media/recent/?count=20&access_token=' + user_params['access_token']

        cursor = db.cursor()
        insert_sql = '''
                INSERT INTO insta_media (user_id, created_at, location_name, geom, raw) VALUES (%s, %s, %s, st_setsrid(st_makepoint(%s, %s), 4326), %s::json)
        '''
        insert_sql_noloc = '''
                INSERT INTO insta_media (user_id, created_at, raw) VALUES (%s, %s, %s::json)
        '''
        curr_url = url
        more = True
        while more:
            resp = requests.get(curr_url)
            if resp.status_code == 200:
                data = resp.json()
                for media in data['data']:
                    id = media['id']
                    if media['location'] and 'latitude' in media['location'].keys():
                        loc_name = media['location']['name']
                        lat = media['location']['latitude']
                        lng = media['location']['longitude']
                        cursor.execute(insert_sql, (user_params['user_django'], datetime.utcfromtimestamp(int(media['created_time'])),  loc_name, lng, lat, json.dumps(media)))
                    else:
                        cursor.execute(insert_sql_noloc, (user_params['user_django'], datetime.utcfromtimestamp(int(media['created_time'])), json.dumps(media)))
                db.commit()
                if len(data['data']) == INSTA_LIMIT:
                    more = True
                    curr_url = url + "&max_id=" + id
                    db.commit()
                else:
                    more = False
            else:
                more = False

    def getTweets(self, user_params, db):
        url =  'https://api.twitter.com/1.1/statuses/user_timeline.json?count=' + str(TWEET_LIMIT)
        consumer = oauth2.Consumer(key=user_params['client_id'], secret=user_params['client_secret'])
        token = oauth2.Token(key=user_params['access_token'], secret=user_params['token_secret'])
        client = oauth2.Client(consumer, token)

        cursor = db.cursor()
        insert_sql = '''
                INSERT INTO tweets (user_id, created_at, coordinates, place_name, place_bbox, raw) VALUES (%s, %s, st_setsrid(st_geomfromgeojson(%s), 4326), %s, st_makevalid(st_setsrid(st_geomfromgeojson(%s), 4326)), %s::json)
        '''

        more = True
        curr_url = url
        while more:
            resp, content = client.request(curr_url, method='GET', headers=None)
            if resp.status == 200:
                content = json.loads(content)
                for tweet in content:
                    created_at = parser.parse(tweet['created_at'])
                    id = tweet['id']
                    if tweet['coordinates']:
                        coordinates = json.dumps(tweet['coordinates'])
                    else:
                        coordinates = None
                    if tweet['place']:
                        place_name = tweet['place']['full_name']
                        place_bbox = json.dumps(tweet['place']['bounding_box'])
                    else:
                        place_name = None
                        place_bbox = None
                    cursor.execute(insert_sql, (user_params['user_django'], created_at, coordinates, place_name, place_bbox, json.dumps(tweet)))
                if len(content) == TWEET_LIMIT:
                    more = True
                    curr_url = url + '&max_id=' + str(id)
                    db.commit()
                else:
                    more = False
            else:
                print resp

            db.commit()

    def getFoursquareCheckins(self, user_params, db):
        url ='https://api.foursquare.com/v2/users/self/checkins?v=20180401&limit=' + str(FOURSQUARE_LIMIT) + '&oauth_token=' + user_params['access_token']
        cursor = db.cursor()
        insert_sql = '''
                INSERT INTO foursquare_checkins (user_id, created_at, venue_name, geom, raw) VALUES (%s, %s, %s, st_setsrid(st_makepoint(%s, %s), 4326), %s::json)
        '''
        insert_sql_private = '''
                INSERT INTO foursquare_checkins (user_id, created_at, venue_name, raw) VALUES (%s, %s, %s, %s::json)
        '''

        curr_url = url
        more = True
        while more:
            checkins = requests.get(curr_url)
            if checkins.status_code == 200:
                checkins = checkins.json()
                for checkin in checkins['response']['checkins']['items']:
                    created_at = checkin['createdAt']
                    venue_name = checkin['venue']['name']
                    if 'private' in checkin['venue'].keys():
                        lat = None
                        lng = None
                    else:
                        lat = checkin['venue']['location']['lat']
                        lng = checkin['venue']['location']['lng']
                    if lat is None:
                        cursor.execute(insert_sql_private, (user_params['user_django'], datetime.utcfromtimestamp(created_at), venue_name, json.dumps(checkin)))
                    else:
                        cursor.execute(insert_sql, (user_params['user_django'], datetime.utcfromtimestamp(created_at), venue_name,  lng, lat, json.dumps(checkin)))
                if len(checkins['response']['checkins']['items']) == FOURSQUARE_LIMIT:
                    more = True
                    curr_url = url + '&beforeTimestamp=' + str(created_at)
                    db.commit()
                else:
                    more = False
            else:
                print checkins.text

        db.commit()

    def getFlickrPhotos(self, user_params, db):
        url =  url = 'https://api.flickr.com/services/rest/?oauth_consumer_key=' + user_params['client_id'] + '&method=flickr.people.getPhotos&user_id=me&extras=date_upload,date_taken,geo,url_m&format=json&nojsoncallback=1&oauth_token=' + user_params['access_token'] + '&oauth_signature=' + user_params['token_secret']+ '&per_page=' + str(FLICKR_LIMIT)

        cursor = db.cursor()

        insert_sql = '''
            insert into flickr_photos (user_id, created_at, geom, raw) values (%s, %s, st_setsrid(st_makepoint(%s, %s), 4326), %s::json)
        '''
        insert_sql_noloc = '''
            insert into flickr_photos (user_id, created_at, raw) values (%s, %s, %s::json)
        '''
        more = True
        curr_url = url
        while more:
            resp = requests.get(curr_url)
            if resp.status_code == 200:
                photos = resp.json()
                for photo in photos['photos']['photo']:
                    created_at = datetime.utcfromtimestamp(int(photo['dateupload']))
                    lat = photo['latitude']
                    lng = photo['longitude']
                    if lat == 0 and lng == 0:
                        cursor.execute(insert_sql_noloc, (user_params['user_django'], created_at, json.dumps(photo)))
                    else:
                        cursor.execute(insert_sql, (user_params['user_django'], created_at, lng, lat, json.dumps(photo)))
                if photos['photos']['page'] < photos['photos']['pages']:
                    more = True
                    curr_url = url + '&page=' + str(photos['photos']['page'] + 1)
                    db.commit()
                    if created_at < datetime(2014, 1, 1):
                        more = False
                else:
                    more = False
            else:
                print resp.text

        db.commit()

    def getOSMChangesets(self, user_params, db):
        url = 'https://api.openstreetmap.org/api/0.6/changesets?user=' + user_params['user_platform'] + '&time=2014-01-01,' 
        
        cursor = db.cursor()
        
        insert_sql = '''
            insert into osm_changesets (user_id, created_at, geom) values (%s, %s, st_setsrid(st_makeenvelope(%s, %s, %s, %s), 4326))
        '''
        more = True
        curr_url = url + str(datetime.now().date())
        while more:
            resp  = requests.get(curr_url)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                changesets = list(root.iter('changeset'))
                for changeset in changesets:
                    attr = changeset.attrib
                    try:
                        min_lon = attr['min_lon']
                        min_lat = attr['min_lat']
                        max_lon = attr['max_lon']
                        max_lat = attr['max_lat']
                    except KeyError:
                        continue
                    created_at = parser.parse(attr['created_at'])
                    cursor.execute(insert_sql, (user_params['user_django'], created_at, min_lon, min_lat, max_lon, max_lat))
                if len(changesets) == OSM_LIMIT:
                    more = True
                    curr_url = url + str(created_at)
                    db.commit()
                else:
                    more = False
                if changesets and created_at.replace(tzinfo=None) < datetime(2015, 1, 1):
                    more = False
            
        db.commit()

    def getMapillarySequences(self, user_params, db):
        url = 'https://a.mapillary.com/v3/sequences?userkeys=' + user_params['user_platform'] + '&client_id=' + user_params['client_id'] + '&per_page=' + str(MAPILLARY_LIMIT)
        cursor = db.cursor()
        insert_sql = '''
            insert into mapillary_sequences (user_id, created_at, geom, raw) values (%s, %s, st_setsrid(st_geomfromgeojson(%s), 4326), %s::json)
        '''
        more = True
        curr_url = url
        while more:
            resp = requests.get(curr_url)
            if resp.status_code == 200:
                headers = resp.headers
                resp = resp.json()
                for sequence in resp['features']:
                    created_at = parser.parse(sequence['properties']['created_at'])
                    geom = sequence['geometry']
                    cursor.execute(insert_sql, (user_params['user_django'], created_at, json.dumps(geom), json.dumps(sequence)))
                next_link = findNextLink(headers)
                if next_link:
                    more = True
                    curr_url = next_link
                    db.commit()
                else:
                    more = False
        db.commit()

    def getStravaActivities(self, user_params, db):
        import polyline

        auth = {"Authorization": "Bearer " + user_params['access_token']}
        url = 'https://www.strava.com/api/v3/athlete/activities?per_page=' + str(STRAVA_LIMIT)

        cursor = db.cursor()
        insert_sql = '''
            insert into strava_activities (user_id, created_at, geom, raw) values (%s, %s, st_setsrid(st_geomfromgeojson(%s), 4326), %s::json)
        '''
        
        more = True
        curr_url = url
        while more:
            resp = requests.get(curr_url, headers=auth)
            if resp.status_code == 200:
                resp = resp.json()
                for activity in resp:
                    created_at = parser.parse(activity['start_date'])
                    if 'map' in activity.keys():
                        if 'polyline' in activity['map'].keys():
                            line = polyline.decode(activity['map']['polyline'])
                        elif 'summary_polyline' in activity['map'].keys():
                            line = polyline.decode(activity['map']['summary_polyline'])
                        # Watch order in geojson. reverse latlng with [::-1]
                        geom = {
                                "type": "LineString",
                                    "coordinates": [list(coords)[::-1] for coords in line]
                            }
                    else:
                        continue
                    cursor.execute(insert_sql, (user_params['user_django'], created_at, json.dumps(geom), json.dumps(activity)))
            if len(activity) == STRAVA_LIMIT:
                more = True
                curr_url = url + '&before=' + str(int((created_at.replace(tzinfo=None) - datetime(1970,1,1)).total_seconds()))
                db.commit()
            else:
                more = False
        db.commit()

    def getInatObservations(self, user_params, db):
        auth = {"Authorization": "Bearer " + user_params['access_token']}
        url = 'https://www.inaturalist.org/observations/' + user_params['login'] + '.json?per_page=' + str(INAT_LIMIT) + "&has[]=geo"
        cursor = db.cursor()
        insert_sql = '''
            insert into inat_observations (user_id, created_at, geom, raw) values (%s, %s, st_setsrid(st_makepoint(%s, %s), 4326), %s::json)
        '''
        more = True
        curr_url = url
        while more:
            resp = requests.get(curr_url, headers=auth)
            if resp.status_code == 200:
                headers = resp.headers
                resp = resp.json()
                for obs in resp:
                    created_at = parser.parse(obs['created_at']).astimezone(utc_zone).replace(tzinfo=None)
                    lat = float(obs['latitude'])
                    lng = float(obs['longitude'])
                    cursor.execute(insert_sql, (user_params['user_django'], created_at, lng, lat, json.dumps(obs)))
            cont = findNextPage(headers)
            if cont:
                more = True
                curr_url = url + '&page=' + str(cont)
                db.commit()
            else:
                more = False
        db.commit()

    def getMeetups(self, user_params, db):
        auth = {"Authorization": "Bearer " + user_params['access_token']}
        url = 'https://api.meetup.com/self/events?desc=true&page=' + str(MEETUP_LIMIT)
         
        cursor = db.cursor()
        insert_sql = '''
            insert into meetups (user_id, created_at, venue_name, geom, raw) values (%s, %s, %s, st_setsrid(st_makepoint(%s, %s), 4326), %s::json)
        '''
        curr_url = url
        more = True
        while more:
            resp = requests.get(curr_url, headers=auth)
            if resp.status_code == 200:
                headers = resp.headers
                resp = resp.json()
                for meetup in resp:
                    created_at = datetime.fromtimestamp(meetup['created']/1000.0)
                    venue_name = meetup['venue']['name']
                    lat = meetup['venue']['lat']
                    lng = meetup['venue']['lon']
                    cursor.execute(insert_sql, (user_params['user_django'], created_at, venue_name, lng, lat, json.dumps(meetup)))
            next_link = findNextLink(headers)
            if next_link:
                more = True
                curr_url = next_link
                db.commit()
            else:
                more = False
        db.commit()

    def getFacebookPlaces(self, user_params, db):
        url = "https://graph.facebook.com/v2.12/me/tagged_places?access_token=" + user_params['access_token'] + "&limit=" + str(FB_LIMIT)

        cursor = db.cursor()
        insert_sql = '''
            insert into facebook_places (user_id, created_at, name, geom, raw) values (%s, %s, %s, st_setsrid(st_makepoint(%s, %s), 4326), %s::json)
        '''
        insert_sql_nogeom = '''
            insert into facebook_places (user_id, created_at, name, raw) values (%s, %s, %s, %s::json)

        '''
        curr_url = url
        more = True
        while more:
            resp = requests.get(curr_url)
            if resp.status_code == 200:
                resp = resp.json()
                for place in resp:
                    created_at = parser.parse(place['created_time'])
                    name = place['place']['name']
                    try:
                        lat = place['place']['location']['latitude']
                        lng = place['place']['location']['longitude']
                    except KeyError:
                        lat = None
                    if not lat:
                        cursor.execute(insert_sql_nogeom, (user_params['user_django'], created_at, name, json.dumps(place)))
                    else:
                        cursor.execute(insert_sql, (user_params['user_django'], created_at, name, lng, lat, json.dumps(place)))

            if 'next' in resp['paging'].keys():
                more = True
                curr_url = resp['paging']['next']
            else:
                more = False
        db.commit()

def findNextLink(headers):
    try:
        links = headers['link']
    except KeyError:
        try:
            links = headers['Link']
        except KeyError:
            return False
    for x in links.split(','):
        if 'next' in x:
            next_link = x.split('<')[1].split('>')[0]
        else:
            next_link = False
    return next_link

def findNextPage(headers):
    tot = int(headers['X-Total-Entries'])
    perpage = int(headers['X-Per-Page'])
    curr_page = int(headers['X-Page'])
    if curr_page * perpage < tot:
        return curr_page + 1
    else:
        return False


