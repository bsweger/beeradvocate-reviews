import time
from beeradvocate.items import BeerReview
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor

class BeerReviewSpider(CrawlSpider):

    name = 'bareviews'
    allowed_domains = ['beeradvocate.com']
    #rules = [Rule(LinkExtractor(allow=['/beer/profile/[a-z0-9]*/[a-z0-9]*/\?ba=DIM']), 'parse_review')]
    
    def __init__(self, user=None, *args, **kwargs):
        self.rules = [Rule(LinkExtractor(allow=['/beer/profile/[a-z0-9]*/[a-z0-9]*/\?ba={}'.format(user)]), 'parse_review')]
        self.start_urls = ['http://www.beeradvocate.com/user/beers/?ba={}'.format(user)]
        super(BeerReviewSpider, self).__init__(*args, **kwargs)

    def parse_review(self, response):
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
