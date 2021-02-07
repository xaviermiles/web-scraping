# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MetserviceItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class PreviousWeatherItem(scrapy.Item):
    yesterday = scrapy.Field()
    last_30_days = scrapy.Field()
    historical_data = scrapy.Field()
