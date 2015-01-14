# Beer Advocate User Review Scraper

##Overview
A simple scraper that extracts all Beeradvocate reviews and ratings for a specified username.

##Example
To generate a .csv file called _beerreviews.csv_ of reviews and ratings for Beeradvocate username _joebeer123_:

    scrapy crawl bareviews -a user=joebeer123 -o beerreviews.csv

##Background
This is a small, unmaintained project written to help my brother, who wanted a copy of the 1,400 reviews he's posted on Beeradvocate.com over the past 8 years.

Beeradvocate-reviews is not intended to (nor does it) copy Beeradvocate's entire database. Rather, it retrieves a dataset of reviews associated with a single user.

##Usage
**Requirements:**

Python 2.7


1. Install dependencies:

        pip install -r requirements.txt

1. Run crawl command:

    .csv output:

        scrapy crawl bareviews -a user=[username] -o [outputfilename].csv

    .json output:

        scrapy crawl bareviews -a user=[username] -o beerreviews.json

##Data
The scraper outputs the following information (if available) for each beer review:
* Review date
* Beer name
* Beer alcohol by volume (ABV)
* Beer style
* Brewer name
* Brewer location (U.S. brewers only)
* Brewer country
* BA score
* User score
* User's % difference from BA score
* User score - look
* User score - smell
* User score - taste
* User score - feel
* User score - overall
* User's review text
* Review URL
* Date scraped

##License
MIT License
