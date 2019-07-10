# -*- coding: utf-8 -*-

import scrapy
from datetime import datetime, date
import logging
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose, Join, MapCompose, TakeFirst

logger = logging.getLogger(__name__)

class StripText:
	def __init__(self, chars=' \r\t\n'):
		self.chars = chars
	def __call__(self, value):
		try:
			return value.strip(self.chars)
		except:  # noqa E722
			return value

def str_to_float(x):
	x = x.replace(',', '')
	try:
		return float(x)
	except:  # noqa E722
		return x

def str_to_int(x):
	try:
		return int(str_to_float(x))
	except:  # noqa E722
		return x

def simplify_recommended(x):
	return True if x == 'Recommended' else False

class ReviewItem(scrapy.Item):
	product_id = scrapy.Field()
	page = scrapy.Field()
	page_order = scrapy.Field()
	recommended = scrapy.Field(
		output_processor=Compose(TakeFirst(), simplify_recommended),
	)
	date = scrapy.Field()
	text = scrapy.Field(
		input_processor=MapCompose(StripText()),
		output_processor=Compose(Join('\n'), StripText())
	)
	hours = scrapy.Field(
		output_processor=Compose(TakeFirst(), str_to_float)
	)
	found_helpful = scrapy.Field()
	found_funny = scrapy.Field()
	compensation = scrapy.Field()
	username = scrapy.Field()
	user_profile = scrapy.Field()
	products = scrapy.Field(
		output_processor=Compose(TakeFirst(), str_to_int)
	)
	early_access = scrapy.Field()

class ProductItem(scrapy.Item):
	url = scrapy.Field()
	id = scrapy.Field()
	app_name = scrapy.Field()
	reviews_url = scrapy.Field()
	img_url = scrapy.Field()
	title = scrapy.Field()
	genres = scrapy.Field(
		output_processor=Compose(TakeFirst(), lambda x: x.split(','), MapCompose(StripText()))
	)
	developer = scrapy.Field()
	franchise = scrapy.Field()
	publisher = scrapy.Field()
	release_date = scrapy.Field()
	short_game_description = scrapy.Field()
	long_game_description = scrapy.Field()
	game_modes = scrapy.Field()
	game_features = scrapy.Field()
	tags = scrapy.Field(
		output_processor=MapCompose(StripText())
	)
	price = scrapy.Field(
		output_processor=Compose(TakeFirst(),
								 StripText(chars=' ₹\n\t\r'),
								 str_to_float)
	)
	discount_price = scrapy.Field(
		output_processor=Compose(TakeFirst(),
								 StripText(chars=' ₹\n\t\r'),
								 str_to_float)
	)
	sentiment = scrapy.Field()
	n_reviews = scrapy.Field(
		output_processor=Compose(
			MapCompose(StripText(), lambda x: x.replace(',', ''), str_to_int),
			max
		)
	)
	user_reviews_info = scrapy.Field()
	metascore = scrapy.Field(
		output_processor=Compose(TakeFirst(), StripText(), str_to_int)
	)
	early_access = scrapy.Field()





class ProductItemLoader(ItemLoader):
	default_output_processor = Compose(TakeFirst(), StripText())


class ReviewItemLoader(ItemLoader):
	default_output_processor = TakeFirst()