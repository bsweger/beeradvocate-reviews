import time
from beeradvocate.items import BeerReview
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy import Request
import urllib
import datetime
import logging
from datetime import timedelta
from dateutil.parser import *

class BeerReviewSpider(CrawlSpider):

    name = 'bareviews'
    allowed_domains = ['beeradvocate.com']

    def __init__(self, user=None, *args, **kwargs):
        self.rules = [Rule(LinkExtractor(allow=['/beer/profile/[a-z0-9]*/[a-z0-9]*/\?ba={}'.format(user)]), 'parse_review')]
        self.start_urls = ['http://www.beeradvocate.com/user/beers/?ba={}&order=dateD'.format(user)]
        self.user = user
        self.ba_url = 'http://www.beeradvocate.com'
        super(BeerReviewSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        '''Generate requests for pages that contain user's ratings and reviews'''
        rating_review = response.xpath('//dt[contains(text(),"Beers Rated")]/following::dd/text()')[0].extract()
        #first list item = number of ratings, second list item = number of reviews
        rating_review = rating_review.replace(',', '').split(' / ')
        ratings = int(rating_review[0])
        reviews = int(rating_review[1])
        #site displays 50 ratings/reviews per page
        urls = ['{}&start={}'.format(response.url, x ) for x in range(0, ratings) if x%50==0]
        for url in urls:
            yield Request(url, callback = self.parse_user_ratings_page)

    def parse_user_ratings_page(self, response):
        '''Generate requests for links to individual user ratings and reviews'''
        urls = response.xpath('//a[re:test(@href, "/beer/profile/[a-z0-9]*/[a-z0-9]*/\?ba={}")]/@href'.format(self.user)).extract()
        for url in urls:
            yield Request(urllib.parse.urljoin(self.ba_url, url), callback = self.parse_rating)

    def parse_rating(self, response):
        '''Scrape individual beer review'''
        review = BeerReview()

        #scrape info about the beer being rated
        review['url'] = response.url
        review['name'] = response.xpath('//h1/text()')[0].extract()
        review['brewer'] = response.xpath('//b[contains(text(),"Brewed by:")]/following::a[1]/b/text()')[0].extract()
        #for non-US beers, BA doesn't display brewer location, just a country
        places = response.xpath(
            '//b[contains(text(),"Brewed by:")]/following::a[re:test(@href, "place/directory/[a-z0-9]*/")]/text()')
        if len(places) == 1:
            review['location'] = places[0].extract()
            review['country'] = review['location']
        elif len(places) == 2:
            review['location'] = places[0].extract()
            review['country'] = places[1].extract()
        else:
            #if unable to parse brewer's location/country, log & move on
            logging.info('Unable to find brewer location')
        review['style'] = response.xpath('//b[contains(text(),"Style")]/following::a[1]/b/text()')
        if review['style']:
            review['style'] = review['style'][0].extract()
        else:
            print("Failed to get beer style")
            return
        abv = response.xpath('//b[contains(text(),"ABV")]/following::text()')
        if abv:
            abv = abv[0].extract()
        else:
            print("Failed to get beer ABV")
            return
        #abvindex = [i for i,s in enumerate(abv) if 'abv' in s.lower()]
        #print abvindex
        #if abvindex and len(abvindex) > 0:
        #    abvindex = abvindex[0]
        #If ABV has a '?', it's unknown, so skip this wretched code
        #if '?' not in abv[abvindex]:
        #    abv = abv[abvindex-1]
        abv = abv.strip()
        review['abv'] = abv
        review['baRating'] = response.xpath('//span[contains(@class, "BAscore_big ba-score")]/text()')[0].extract()
        review['baRating'] = review['baRating'].replace(u'-', '')

        #scrape info specific to the user's review of the beer
        #grab first review on the page, which will be the one by the user we're scraping
        userreview = response.xpath('//div[@id="rating_fullview_content_2"]')[0]
        #grab all text in the review
        reviewtextlist = userreview.xpath('descendant-or-self::*/text()').extract()
        reviewtextlist = [s.strip() for s in reviewtextlist]

        #overall user rating
        review['userRating'] = userreview.xpath('span/text()')[0].extract()

        #get ratings for look, smell, taste, etc. (not all reviews have these)
        subrating_index =  [i for i, s in enumerate(reviewtextlist) if 'look:' in s]
        if len(subrating_index):
            subrating_index = subrating_index[0]
            subratings = reviewtextlist[subrating_index].split(' | ')
            review['lookRating'] = subratings[0].split(': ')[1]
            review['smellRating'] = subratings[1].split(': ')[1]
            review['tasteRating'] = subratings[2].split(': ')[1]
            review['feelRating'] = subratings[3].split(': ')[1]
            review['overallRating'] = subratings[4].split(': ')[1]
        else:
            subrating_index = 0

        #if beer has an overall Beer Advocate rating, grab user's deviation
        percent_index = 0
        if len(review['baRating']):
            percent_index = [i for i, s in enumerate(reviewtextlist) if '%' in s]
            if len(percent_index):
                percent_index = percent_index[0]
                rdev = reviewtextlist[percent_index]
                review['rdev'] = rdev.split(' ')[-1].replace('%', '')

        today = datetime.datetime.now().date()
        review_date = userreview.xpath('div/span/a/text()')[-1].extract()
        if review_date.lower().find('today') >= 0:
            #beer was reviewed today
            review['reviewDate'] = today
        elif review_date.lower().find('yesterday') >= 0:
            #beer was reviewed yesterday
            review['reviewDate'] = today - timedelta(days = 1)
        else:
            review_date = parse(review_date).date()
            if review_date > today:
                #review date was in format "Friday at 8 PM"
                review['reviewDate'] = review_date - timedelta(weeks = 1)
            else:
                review['reviewDate'] = review_date
        review['accessDate'] = today

        #get the review text
        if subrating_index:
            review['review'] = ' '.join(
                reviewtextlist[subrating_index + 1 : -3])
        elif percent_index:
            review['review'] = ' '.join(
                reviewtextlist[percent_index + 1 : -3])
        else:
            review['review'] = ' '.join(reviewtextlist[4:-3])

        yield review
