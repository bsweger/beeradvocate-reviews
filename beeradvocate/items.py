# scrapy model for individual Beer Advocate review

import scrapy


class BeerReview(scrapy.Item):
    url = scrapy.Field()
    name = scrapy.Field()
    brewer = scrapy.Field()
    location = scrapy.Field()
    country = scrapy.Field()
    style = scrapy.Field()
    abv = scrapy.Field()
    baRating = scrapy.Field()
    userRating = scrapy.Field()
    rdev = scrapy.Field()
    lookRating = scrapy.Field()
    smellRating = scrapy.Field()
    tasteRating = scrapy.Field()
    feelRating = scrapy.Field()
    overallRating = scrapy.Field()
    review = scrapy.Field()
    reviewDate = scrapy.Field()
    accessDate = scrapy.Field()
