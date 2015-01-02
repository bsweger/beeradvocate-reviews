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
            #self.log('Finding links on {}'.format(url), level=log.INFO)
            yield Request(url, callback = self.parse_user_ratings_page)

    def parse_user_ratings_page(self, response):
        '''Generate requests for links to individual user ratings and reviews'''
        urls = response.xpath('//a[re:test(@href, "/beer/profile/[a-z0-9]*/[a-z0-9]*/\?ba={}")]/@href'.format(self.user)).extract()
        for url in urls:
            yield Request(urlparse.urljoin(self.ba_url, url), callback = self.parse_rating)

    def parse_rating(self, response):
        '''Scrape individual beer review'''
        review = BeerReview()
        review['url'] = response.url
        review['name'] = response.xpath('//h1/text()')[0].extract()
        review['brewer'] = response.xpath('//b[contains(text(),"Brewed by:")]/following::a[1]/b/text()')[0].extract()
        review['location'] = response.xpath('//b[contains(text(),"Brewed by:")]/following::a[3]/text()')[0].extract()
        review['country'] = response.xpath('//b[contains(text(),"Brewed by:")]/following::a[4]/text()')[0].extract()
        if not len(review['country']):
            review['country'] = review['location']
        review['style'] = response.xpath('//b[contains(text(),"Style | ABV")]/following::a[1]/b/text()')[0].extract()
        review['abv'] = response.xpath('//b[contains(text(),"Style | ABV")]/following::text()[3]')[0].extract()
        review['abv'] = review['abv'].split(' | ')[1]
        review['baRating'] = response.xpath('//span[contains(@class, "BAscore_big ba-score")]/text()')[0].extract()
        reviewtext = response.xpath('//div[@id="rating_fullview_content_2"]')[0].xpath('.//text()').extract()
        review['userRating'] = reviewtext[0]
        review['rdev'] = reviewtext[3]
        reviewslist = reviewtext[4].split(' | ')
        review['lookRating'] = reviewslist[0].split(': ')[1]
        review['smellRating'] = reviewslist[1].split(': ')[1]
        review['tasteRating'] = reviewslist[2].split(': ')[1]
        review['feelRating'] = reviewslist[3].split(': ')[1]
        review['overallRating'] = reviewslist[4].split(': ')[1]
        review['reviewDate'] = reviewtext[-1]
        review['accessDate'] = time.strftime('%b %d, %Y')
        yield review
