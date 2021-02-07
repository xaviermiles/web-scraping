import scrapy
import json


class PreviousWeatherSpider(scrapy.Spider):
    name = 'previous_weather'
    custom_settings = {
        'ITEM_PIPELINES': {
            'metservice.pipelines.PreviousWeatherPipeline': 500
        }
    }

    def __init__(self):
        location = "christchurch"

        self.start_urls = [
            f'https://www.metservice.com/towns-cities/locations/{location}/past-weather/'
        ]
        self.headers = {
            'Accept': "*/*",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "en-GB,en;q=0.5",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Host': "www.metservice.com",
            'Pragma': "no-cache",
            'Referer': f"https://www.metservice.com/towns-cities/locations/{location}/past-weather",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"
        }

    def parse(self, response):
        url = 'https://www.metservice.com/publicData/webdata/towns-cities/locations/christchurch/past-weather'
        request = scrapy.Request(url, callback=self.parse_api, headers=self.headers)

        yield request

    def parse_api(self, response):
        raw_data = response.body
        jsonresponse = json.loads(raw_data)

        yield jsonresponse
