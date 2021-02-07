# web-scraping
Learn how to do some basic web scraping in Python. The media bias tutorial used the Requests+BeautifulSoup4 librarys, but I abandoned these for the Scrapy library as this is able to better handle websites that rely on JavaScript.

Original aim was to extract previous Christchurch weather from Metservice and write it to CSV files. This information is also added to CSV files which keep an ongoing record of previous weather (going back as far as the first run of the web scraper). This information was being used to make a temperature blanket, so the daily highs/lows are also written to an Excel document. All these files are in "./metservice/previous weather".

Doesn't actually use Julia code, just has some "JSON lines" files which share the .jl file extension with Julia.
