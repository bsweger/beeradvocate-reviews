import time
from beeradvocate.items import BeerReview
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import Request
from scrapy import log
import urlparse

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
            yield Request(urlparse.urljoin(self.ba_url, url), callback = self.parse_rating)

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
            self.log('Unable to find brewer location', level=log.INFO)
        review['style'] = response.xpath('//b[contains(text(),"Style | ABV")]/following::a[1]/b/text()')[0].extract()
        abv = response.xpath('//b[contains(text(),"Style | ABV")]/following::text()[3]')[0].extract()
        #website displays '?' when ABV is unknown
        if abv.find('?') < 0:
            abv = abv.split(' | ')[1]
            abv = abv.replace(u'\xa0','').strip()[:-1]
            review['abv'] = abv
        review['baRating'] = response.xpath('//span[contains(@class, "BAscore_big ba-score")]/text()')[0].extract()
        review['baRating'] = review['baRating'].replace(u'-', '')

        #scrape info specific to the user's review of the beer
        #grab first review on the page, which will be the one by the user we're scraping
        userreview = response.xpath('//div[@id="rating_fullview_content_2"]')[0]
        #grab all text in the review
        reviewtextlist = userreview.xpath('descendant-or-self::*/text()').extract()

        #get ratings for look, smell, taste, etc. (not all reviews have these)
        subrating_index =  [i for i, s in enumerate(reviewtextlist) if 'look:' in s]
        if len(subrating_index):
            subratings = reviewtextlist[subrating_index[0]].split(' | ')
            review['lookRating'] = subratings[0].split(': ')[1]
            review['smellRating'] = subratings[1].split(': ')[1]
            review['tasteRating'] = subratings[2].split(': ')[1]
            review['feelRating'] = subratings[3].split(': ')[1]
            review['overallRating'] = subratings[4].split(': ')[1]
        review['userRating'] = userreview.xpath('span/text()')[0].extract()

        #if beer has an overall Beer Advocate rating, grab user's deviation
        if len(review['baRating']):
            percent_index = [i for i, s in enumerate(reviewtextlist) if '%' in s]
            if len(percent_index):
                rdev = reviewtextlist[percent_index[0]]
                review['rdev'] = rdev.split(' ')[-1].replace('%', '')

        review['reviewDate'] = userreview.xpath('div/span/a/text()')[-1].extract()
        review['accessDate'] = time.strftime('%b %d, %Y')

        yield review
