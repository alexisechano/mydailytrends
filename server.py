"""
Created by Alexis Echano, 2020

My Daily Trends: A social media trend and post aggregator to keeping up to date with 
                 the latest trends and news strories easier.

Language: Python

"""

# import statements
from flask import Flask
from flask import request, render_template
import tweepy as tw 
import sys
import pymysql
import json
from datetime import date 
from datetime import timedelta 
import requests
import pandas as pd
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from newsapi import NewsApiClient

# initialize scheduler with your preferred timezone
scheduler = BackgroundScheduler()
scheduler.start()

# not currently in use, for future work
import facebook_scraper as fs   #From @kevinzg on Github


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

# flask app configuration
app = Flask(__name__, template_folder='template', static_folder='static')

"""
# FACEBOOK SCRAPING! --> still a work in progress
# Static Database --> pymysql
pages = []
try:
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
    con.close()

facebook_post_list = []
#id (letter + num), trend, text, image

for fbname in pages:
    page_name = fbname   #get these pages from the SQL table
    for post in fs.get_posts(page_name, pages=1):
        if(post != None):
            post_txt = post['text']
            pimng = post['image']
            postLink = post['post_url']
            if (post_txt != None and pimng !=None):
                if(pimng.find("https") != -1):
                    facebook_post_list.append((post_txt, pimng, postLink))

"""
fixed_names = []
def grab_news(): # grabbing relevant news stories and articles
    news_srcs = []
    news_titles = []
    news_links = []
    news_images = []
    match_news_trend = []
    
    for t in fixed_names:
        # grabbing news sources now...grab headlines per query
        headliners = newsapi.get_top_headlines(sources='business-insider, buzzfeed, associated-press, bbc-news, the-verge, fox-news, nbc-news, abc-news', q=t)
        
        # loop through the headlines
        for s in headliners['articles']:
            match_news_trend.append(t)
            
            # grabbing news article data
            from_src = s['source']['name']
            title_src = s['title']
            url_src = s['url']
            img_src = s['urlToImage']
            
            # load into lists
            news_srcs.append(from_src)
            news_titles.append(title_src)
            news_links.append(url_src)
            news_images.append(img_src)
    
    news_info = {'ntitles': news_titles, 'nsrcs': news_srcs, 'nlinks': news_links, 'nimgs': news_images, 'ntrends': match_news_trend}
    news_df = pd.DataFrame(data=news_info)
    
    # load into CSV
    news_df.to_csv('news.csv', index = False)
    
    #logging.warning(headlines)
    
    
# accesses the APIs and stores into CSV on the scheduler
def store_and_retrieve(): 
    trends1 = api.trends_place(23424977)    # based on trends only in America
    
    data = trends1[0]
        
    # grab the trends
    trends = data['trends']
    
    # grab the name from each trend
    names = [trend['name'] for trend in trends] #list of the trending hashtags
    names = names[:6]  #only keep the top 6 ones
    
    # initiation of lists for rendering     
    post_retr_tweets = []
    img_bools = []
    tweets = []
    tweet_images = []
    tweet_id = []
    match_tweet_trend = []
    tweet_link_id = []
    usernames = []
    
    id_let = 0
    id_num = 1
    letters_for_id = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'] #add more if needed
    curr_id = ''
    
    for n in names:
        #id (letter + num), trend, text, image
        search_word = n
        date_since = yesterday   #find way to auto find the date
        
        tweetsCurr = tw.Cursor(api.search, q = search_word, lang = "en", result_type='popular', since = date_since, tweet_mode='extended', include_entities = True).items(5)
        
        # manual editing
        edited_tag = n.replace('#','')
        edited_tag = edited_tag.replace('%','Percent')
        edited_tag = edited_tag.replace(' ','')
        
        # iterate through cursor of tweets
        for val in tweetsCurr:
            if val == None:
                break
            #creates unique id for each post
            #check if cursor has anything in it
            if 'media' in val.entities:
                image_content = val.entities['media'][0]['media_url']
                if image_content != "":
                    curr_id += letters_for_id[id_let]
                    id_num_str = str(id_num)
                    curr_id += id_num_str
                    
                     #add to lists for storage
                    text_tweet = val.full_text.rsplit('https', 1)[0]
                    text_tweet = text_tweet.replace('&amp','and')
                    url_str = "https://twitter.com/user/status/" + str(val.id)
                    id_in_use = edited_tag + curr_id
                    user = val.author.screen_name
                    
                    # load into lists
                    tweets.append(text_tweet)
                    tweet_images.append(image_content)
                    match_tweet_trend.append(edited_tag)
                    tweet_link_id.append(url_str)
                    usernames.append(user)
                    tweet_id.append(id_in_use)
                    img_bools.append(True)
                    
                    #logging.warning(id_in_use, edited_tag, text_tweet, image_content, url_str)
                    #post_retr_tweets.append([id_in_use, edited_tag, text_tweet, image_content, url_str, user])
                    
            else:
                    curr_id += letters_for_id[id_let]
                    id_num_str = str(id_num)
                    curr_id += id_num_str
                    
                    text_tweet = val.full_text.rsplit('https', 1)[0]
                    text_tweet = text_tweet.replace('&amp;','and')
                    url_str = "https://twitter.com/user/status/" + str(val.id)
                    
                    id_in_use = edited_tag + curr_id
                    user = val.author.screen_name
                    
                    # load into lists
                    tweets.append(text_tweet)
                    tweet_link_id.append(url_str)
                    match_tweet_trend.append(edited_tag)
                    usernames.append(user)
                    tweet_id.append(id_in_use)
                    tweet_images.append("null")
                    img_bools.append(False)
                   
                    #logging.warning(id_in_use, edited_tag, text_tweet, url_str)
                    #post_retr_tweets_noimg.append((id_in_use, edited_tag, text_tweet, url_str, user))
    
            #reset id vals
            id_num += 1 
            curr_id = ''
        fixed_names.append(edited_tag)   # adds for hashtag scroll bar at the top
        id_let += 1 

    # initialize dataframe for reading to CSV
    #logging.warning(len(tweet_id), len(tweet_link_id), len(post_retr_tweets), len(post_retr_tweets_noimg), len(match_tweet_trend))
    twit_info = {'ids': tweet_id, 'matching_trend': match_tweet_trend, 'list_of_tweets': tweets,'imgs': tweet_images, 'tweet_urls':tweet_link_id, 'users': usernames, 'has_image': img_bools}
    twit_df = pd.DataFrame(data=twit_info)
    
    # load into CSV
    twit_df.to_csv('tweet_store.csv', index = False)
    
    # grab news information, see function above
    grab_news()
    
# function that loads information on to the site
def load_data_site():
    # read in information
    data = pd.read_csv("tweet_store.csv")
    news_data = pd.read_csv("news.csv")
    
    # readable pandas dataframe
    ready_to_load_df = pd.DataFrame(data) 
    nready_to_load_df = pd.DataFrame(news_data) 
    
    # init lists to render
    post_tweets_prerendered = []
    post_tweets_noimg_prerendered = []
    trend_names_prerendered = []
    
    news_posts_prerendered = []

    # consolidate news API source
    for index, rows in nready_to_load_df.iterrows(): 
        # current row in correct order for rendering
        temp_list_n =[rows.ntitles, rows.nsrcs, rows.nlinks, rows.nimgs, rows.ntrends] 
          
        # append the list to the final list 
        news_posts_prerendered.append(temp_list_n) 
    
    # get trending names for hashtags!
    trending_names_unedited = list(ready_to_load_df['matching_trend'].copy())
    
    # dict.fromkeys gets rid of duplicates in the rows!
    trend_names_prerendered = list(dict.fromkeys(trending_names_unedited))
    
    # filter rows with image posts
    with_image_df = ready_to_load_df.loc[ready_to_load_df['has_image'] == True]
    
    post_tweets_prerendered = []
    
    # Iterate over IMAGE rows
    for index, rows in with_image_df.iterrows(): 
        # current row in correct order for rendering
        temp_list_1 =[rows.ids, rows.matching_trend, rows.list_of_tweets, rows.imgs, rows.tweet_urls, rows.users] 
          
        # append the list to the final list 
        post_tweets_prerendered.append(temp_list_1) 
    
    # filter rows without image posts
    without_image_df = ready_to_load_df.loc[ready_to_load_df['has_image'] == False]
    
    post_tweets_noimg_prerendered = []
    
    # Iterate over each NON IMAGE row 
    for index, rows in without_image_df.iterrows(): 
        # current row in correct order for rendering
        temp_list_2 = [rows.ids, rows.matching_trend, rows.list_of_tweets, rows.tweet_urls, rows.users] 
          
        # append the list to the final list 
        post_tweets_noimg_prerendered.append(temp_list_2) 
    
    # returns lists to be sent to HTML code
    return post_tweets_prerendered, post_tweets_noimg_prerendered, trend_names_prerendered, news_posts_prerendered

# LANDING PAGE, just pure web development no server needed  
@app.route('/', methods=['GET'])
def index():
    return render_template('landing.html')  # Basic landing page --> log in process still in progress

# scheduler is here to run background task (to speed up loadtime), every 6 hours for now
job = scheduler.add_job(store_and_retrieve, 'interval', hours=6)

# MAIN 
@app.route('/home', methods=['GET'])
def content():
    post_tweets, post_tweets_noimg, trend_names, news_posts = load_data_site()
    return render_template("index.html", lengImg = len(post_tweets), lengNoImg = len(post_tweets_noimg), list_of_tweets = post_tweets, list_of_tweets_noimg = post_tweets_noimg, hashtags = trend_names)
 
#end    
if __name__ == "__main__":
    app.run(debug=True)