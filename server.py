from flask import Flask
from flask import request, render_template
import tweepy as tw
import facebook_scraper as fs
import sys
import pymysql
import json
from datetime import date 
from datetime import timedelta 
import facebook as fb
import requests
import pandas as pd
import logging
from newsapi import NewsApiClient

# API KEYS AND DB PASSWORDS
news_api_key = '1f07507dd6b14f108ae1ccb2e310428d'
host='mysql1.csl.tjhsst.edu'
user = 'site_2020aechano'
password = '3dNQL6ha3rrpY9ysUdaE2y6W'
db = 'site_2020aechano'

# tweepy authentication keys and tokens
consumer_key = '9lt1rqknybMBGbI3OOEsttj1i'
consumer_secret = '3ksZ1GfIg9XeuTx1F7lJ3yDNePmdgVlooVYgX2pfHwyuebAgiO'
access_token = '940307799476760581-xFkbbSJwCjFwVeXIqSgfnQK2bqZriWu'
access_token_secret = 'r550WBT3eYNmxpmz2cZLzYf22LHYAx1RZBpdUylk5JI4L'
fb_access_token = "188206839207957|Eh8r3YJ0mGjZ9bQ94A2GYvuybM8" #token type is bearer

# Init for News API
newsapi = NewsApiClient(api_key=news_api_key)

# Init for Tweepy
auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth, wait_on_rate_limit=True)
    

# Get today's date FOR QUERY SEARCH
today = date.today() 
# Yesterday date to grab current tweets!
yesterday = today - timedelta(days = 1)

#for facebook scraping - right now, database is static, but I might add things
#If I implement NEWS API properly, then I can get rid of facebook!
pages = []
'''try:
    con = pymysql.connect(host=host, user=user, password=password, db=db, use_unicode=True, charset='utf8')
    cur = con.cursor()
    cur.execute("SELECT * FROM fbpages")
    data = cur.fetchall()
    for row in data:
        pages.append(row[2])

except Exception as e:
    sys.exit(e)

finally:
    # close the database connection using close() method.
    con.close()'''

#simple flask app configuration
app = Flask(__name__, template_folder='template', static_folder='static')

#begin new facebook retrieval function
""" FACEBOOK SCRAPING!
facebook_post_list = []
#id (letter + num), trend, text, image
# facebook grabbing mechanism works!
for fbname in pages:
    page_name = fbname   #get these from the SQL table
    for post in fs.get_posts(page_name, pages=1):
        if(post != None):
            post_txt = post['text']
            pimng = post['image']
            postLink = post['post_url']
            if (post_txt != None and pimng !=None):
                if(pimng.find("https") != -1):
                    facebook_post_list.append((post_txt, pimng, postLink))

"""
@app.route('/', methods=['GET'])
def index():
    return render_template('landing.html')  # i need to do database matching here with login and stuff

@app.route('/home', methods=['GET'])
def content():
    trends1 = api.trends_place(23424977)    #based on trends only in America
    
    data = trends1[0]
        
    # grab the trends
    trends = data['trends']
    
    # grab the name from each trend
    names = [trend['name'] for trend in trends] #list of the trending hashtags
    names = names[:6]  #only keep the top 6 ones
    
    #lists for the rendering        
    post_retr_tweets = []
    post_retr_tweets_noimg = []
    fixed_names = []
    tweets = []
    tweet_images = []
    tweet_id = []
    match_tweet_trend = []
    tweet_link_id = []
    
    id_let = 0
    id_num = 1
    letters_for_id = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'] #add more if needed
    curr_id = ''
    
    for n in names:
        #id (letter + num), trend, text, image
        search_word = n
        date_since = yesterday   #find way to auto find the date
        
        tweetsCurr = tw.Cursor(api.search, q = search_word, lang = "en", result_type='popular', since = date_since, tweet_mode='extended', include_entities = True).items(5)
        edited_tag = n.replace('#','')
        edited_tag = edited_tag.replace('%','Percent')
        edited_tag = edited_tag.replace(' ','')
        
        for val in tweetsCurr:  #WORKING to retrieve images!
            if val == None:
                break
            #creates unique id for each post
            #check if CUrsor has anything in it
            if 'media' in val.entities:
                image_content=val.entities['media'][0]['media_url']
                if image_content != "":
                    curr_id += letters_for_id[id_let]
                    id_num_str = str(id_num)
                    curr_id += id_num_str
                    
                     #add to lists for storage
                    tweet_id.append(curr_id)
                    text_tweet = val.full_text.rsplit('https', 1)[0]
                    text_tweet = text_tweet.replace('&amp','and')
                    tweets.append(text_tweet)
                    tweet_images.append(image_content)
                    
                    match_tweet_trend.append(edited_tag)
                    url_str = "https://twitter.com/user/status/" + str(val.id)
                    tweet_link_id.append(url_str)
                    id_in_use = edited_tag + curr_id
                    user = val.author.screen_name
                    #put in to rendering list
                    #logging.warning(id_in_use, edited_tag, text_tweet, image_content, url_str)
                    post_retr_tweets.append((id_in_use, edited_tag, text_tweet, image_content, url_str, user))
            else:
                    curr_id += letters_for_id[id_let]
                    id_num_str = str(id_num)
                    curr_id += id_num_str
                    
                    text_tweet = val.full_text.rsplit('https', 1)[0]
                    text_tweet = text_tweet.replace('&amp;','and')
                    url_str = "https://twitter.com/user/status/" + str(val.id)
                    id_in_use = edited_tag + curr_id
                    user = val.author.screen_name
                    #put in to rendering list
                    #logging.warning(id_in_use, edited_tag, text_tweet, url_str)
                    post_retr_tweets_noimg.append((id_in_use, edited_tag, text_tweet, url_str, user))
            #reset
            id_num += 1 
            curr_id = ''
        fixed_names.append(edited_tag)   #adds for hashtag scroll bar at the top
        id_let += 1 
    
    #NEWS API HERE - problem: getting proper query
    # /v2/top-headlines
    """top_headlines = newsapi.get_top_headlines(q='coronavirus',
                                              sources='bbc-news,the-verge',
                                              category='business',
                                              language='en',
                                              country='us')
    
    # /v2/sources
    sources = newsapi.get_sources()"""
    
    
    return render_template("index.html", leng = len(post_retr_tweets), lengthy = len(post_retr_tweets_noimg), list_of_tweets = post_retr_tweets, list_of_tweets_noimg = post_retr_tweets_noimg, hashtags = fixed_names) 
#end    
if __name__ == "__main__":
    app.run(debug=True)