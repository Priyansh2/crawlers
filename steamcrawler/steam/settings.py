from smart_getenv import getenv

BOT_NAME = 'steam'

SPIDER_MODULES = ['steam.spiders']
NEWSPIDER_MODULE = 'steam.spiders'

USER_AGENT = 'Steam Scraper'

ROBOTSTXT_OBEY = True
# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 2

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 2
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
    'steam.middlewares.CircumventAgeCheckMiddleware': 600,
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 1
DUPEFILTER_CLASS = 'steam.middlewares.SteamDupeFilter'

HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0  # Never expire.
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [301, 302, 303, 306, 307, 308]
HTTPCACHE_STORAGE = 'steam.middlewares.SteamCacheStorage'

AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID', type=str, default=None)
AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY', type=str, default=None)

FEED_EXPORT_ENCODING = 'utf-8'
