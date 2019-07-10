#scrapy crawl products -o output/products_all.jl --logfile=output/products_all.log --loglevel=INFO -s JOBDIR=output/products_all_job

import logging
import re,html2text,os
from w3lib.url import canonicalize_url, url_query_cleaner
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ..items import ProductItem, ProductItemLoader
from scrapy.loader.processors import Compose, Join, MapCompose, TakeFirst

logger = logging.getLogger(__name__)
h = html2text.HTML2Text()
h.unicode_snob=True
h.ignore_links=True
h.ignore_images=True
h.decode_errors="ignore"
h.single_line_break=True
h.ignore_emphasis = True

def extract_game_description(response):
	raw_info = response.xpath("//*[@id='game_area_description' and @class='game_area_description']").extract()
	if raw_info:
		return h.handle(raw_info[0])
	else:
		return "NA"

def strip_commas_and_brackets(item):
	return int(item.replace(",","").replace("(","").replace(")","").strip())

def extract_user_reviews_counts(response):
	total_reviews = response.xpath('//*[contains(@for,"review_type_all")]/span[@class="user_reviews_count"]/text()').extract()
	if total_reviews:
		total_reviews = strip_commas_and_brackets(total_reviews[0])
	else:
		total_reviews = 0
	positive_reviews = response.xpath('//*[contains(@for,"review_type_positive")]/span[@class="user_reviews_count"]/text()').extract()
	if positive_reviews:
		positive_reviews = strip_commas_and_brackets(positive_reviews[0])
	else:
		positive_reviews = 0

	steam_purchasers_reviews = response.xpath('//*[contains(@for,"purchase_type_steam")]/span[@class="user_reviews_count"]/text()').extract()
	if steam_purchasers_reviews:
		steam_purchasers_reviews = strip_commas_and_brackets(steam_purchasers_reviews[0])
	else:
		steam_purchasers_reviews = 0
	negative_reviews = total_reviews - positive_reviews
	other_purchasers_reviews = total_reviews - steam_purchasers_reviews
	## Language is set to be "english" by default, otherwise below code will give reviews in language set in steam preference.
	en_lang_reviews = response.xpath('//*[contains(@for,"review_language_mine")]/span[@class="user_reviews_count"]/text()').extract()
	if en_lang_reviews:
		en_lang_reviews = strip_commas_and_brackets(en_lang_reviews[0])
	else:
		en_lang_reviews = 0
	all_lang_reviews = total_reviews
	user_reviews_info={"total_reviews":total_reviews,
	"positive_reviews":positive_reviews,
	"negative_reviews":negative_reviews,
	"steam_purchasers_reviews":steam_purchasers_reviews,
	"other_purchasers_reviews":other_purchasers_reviews,
	"en_lang_reviews":en_lang_reviews,
	"all_lang_reviews":all_lang_reviews}
	return user_reviews_info

def extract_dev_info(response):
	details = response.xpath('//*[@class="details_block" and not(contains(@class,"vr"))]').extract_first()
	items_list=["developer","franchise","release_date","publisher"]
	curr_items_list=[]
	dev_info={}
	try:
		details = details.split('<br>')
		for x in range(len(details)-1):
			line = details[x]
			line = re.sub('<[^<]+?>', '', line).strip()
			if x in (0,1):
				line = re.sub('[\r\t\n]', '', line).strip()
				for prop,name in [('Title:', 'title'),('Genre:', 'genres')]:
					if prop in line:
						item = line.replace(prop, '').strip()
						dev_info[name]=item
			else:
				line = line.split("\r\n\t\t\r\n\t\r\n\t\t\t\r\n\t\t\t")
				for i in range(len(line)):
					item = line[i]
					item =re.sub('[\r\t\n]', '',item).strip()
					if i!=len(line)-1:
						if item:
							item_name = item.split(":")[0].strip().lower()
							curr_items_list.append(item_name)
							if item_name in items_list:
								item = item.split(":")[1].strip()
								dev_info[item_name]=item
					else:
						if item:
							items = item.split("Release Date")
							item_name = items[0].split(":")[0].strip().lower()
							curr_items_list.append(item_name)
							if item_name in items_list:
								item = items[0].split(":")[1].strip()
								dev_info[item_name]=item
							date  = items[-1].split(":")[1].strip()
							curr_items_list.append("release_date")
							dev_info["release_date"]=date
		for item_name in items_list:
			if item_name not in curr_items_list:
				dev_info[item_name]="NA"
	except:  # noqa E722
		pass
	return dev_info

def filter(x):
	chars=' \r\t\n\xa0'
	return x.strip(chars)

def load_product(response):
	"""Load a ProductItem from the product page response."""
	loader = ProductItemLoader(item=ProductItem(), response=response)

	url = url_query_cleaner(response.url, ['snr'], remove=True)
	url = canonicalize_url(url)
	loader.add_value('url', url)

	found_id = re.findall('/app/(.*?)/', response.url)
	if found_id:
		id = found_id[0]
		loader.add_value('id', id)

		img_url = f'https://steamcdn-a.akamaihd.net/steam/apps/{id}/header.jpg'
		loader.add_value('img_url',img_url)

		reviews_url = f'http://steamcommunity.com/app/{id}/reviews/?browsefilter=mostrecent&p=1'
		loader.add_value('reviews_url', reviews_url)

	brief_game_description= response.css("div.game_description_snippet::text").extract()
	if brief_game_description:
		brief_game_description = brief_game_description[0].strip()
	else:
		brief_game_description = "NA"
	loader.add_value('short_game_description',brief_game_description)
	detail_game_description=extract_game_description(response)
	loader.add_value('long_game_description',detail_game_description)

	dev_info = extract_dev_info(response)
	for item in dev_info:
		loader.add_value(item,dev_info[item])
	loader.add_css('app_name', '.apphub_AppName ::text')
	#game_modes_list=response.xpath('//*[@class="tab_filter_control " and @data-param="category3"]/span[@class="tab_filter_control_label"]/text()').extract()
	#game_features_list = response.xpath('//*[@class="tab_filter_control " and @data-param="category2" or @data-param="special_categories"]/span[@class="tab_filter_control_label"]/text()').extract()
	game_modes_list = ['Single-player', 'Multi-player', 'Online Multi-Player', 'Local Multi-Player', 'Co-op', 'Online Co-op', 'Local Co-op', 'Shared/Split Screen', 'Cross-Platform Multiplayer']
	game_features_list = ['Played with Steam Controller', 'Steam Achievements', 'Full controller support', 'Steam Trading Cards', 'Captions available', 'Steam Workshop', 'SteamVR Collectibles', 'Partial Controller Support', 'Steam Cloud', 'Valve Anti-Cheat enabled', 'Includes Source SDK']
	game_area_details  = response.css(".game_area_details_specs a::text").extract()
	proc = 	MapCompose(filter)
	filtered_game_area_details = proc(game_area_details)
	game_modes,game_features=[],[]
	for item in filtered_game_area_details:
		if item in game_modes_list:
			game_modes.append(item)
		if item in game_features_list:
			game_features.append(item)
	proc = MapCompose(filter)
	if game_modes:
		if len(game_modes)==1:
			loader.add_value('game_modes',game_modes[0])
		else:
			loader.add_value('game_modes',", ".join(item for item in game_modes))
	if game_features:
		if len(game_features)==1:
			loader.add_value('game_features',game_features[0])
		else:
			loader.add_value('game_features',", ".join(item for item in game_features))
	if not game_modes:
		loader.add_value('game_modes',"NA")
	if not game_features:
		loader.add_value('game_features',"NA")

	loader.add_css('tags', 'a.app_tag::text')

	price = response.css('.game_purchase_price ::text').extract_first()
	if not price:
		price = response.css('.discount_original_price ::text').extract_first()
		loader.add_css('discount_price', '.discount_final_price ::text')
	loader.add_value('price', price)

	sentiment = response.css('.game_review_summary').xpath('../*[@itemprop="description"]/text()').extract()
	loader.add_value('sentiment', sentiment)

	loader.add_xpath('metascore','//div[@id="game_area_metascore"]/div[contains(@class, "score")]/text()')

	early_access = response.css('.early_access_header')
	if early_access:
		loader.add_value('early_access', True)
	else:
		loader.add_value('early_access', False)

	overall_reviews = response.xpath('//meta[@itemprop="reviewCount"]/@content').extract()
	overall_reviews = '0' if len(overall_reviews) == 0 else overall_reviews[0]
	loader.add_value('n_reviews', overall_reviews)

	user_reviews_info = extract_user_reviews_counts(response)
	loader.add_value('user_reviews_info',user_reviews_info)
	return loader.load_item()


class ProductSpider(CrawlSpider):
	## test_urls -> [old,latest,most_reviews,least_reviews,lowest_price,highest_price]. Not in order as written.
	name = 'products'
	start_urls=['https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998%2C994%2C21%2C10&supportedlang=schinese%2Cenglish']

	#start_urls = ['https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998&supportedlang=english'] ##game

	#start_urls=['https://store.steampowered.com/app/1106800/Infinitely_up_Skip_Figure/','https://store.steampowered.com/app/282010/Carmageddon_Max_Pack/','https://store.steampowered.com/app/570/Dota_2/','https://store.steampowered.com/app/821800/ADRLabelling_Game/?snr=1_7_7_230_150_1','https://store.steampowered.com/app/888790/Sabbat_of_the_Witch/','https://store.steampowered.com/app/267600/Airport_Simulator_2014/'] #game_test_urls

	#start_urls = ['https://store.steampowered.com/search/?sort_by=Reviews_DESC&category1=994&supportedlang=english'] #software

	#start_urls = ['https://store.steampowered.com/app/1080890/PUM/','https://store.steampowered.com/app/1840/Source_Filmmaker/','https://store.steampowered.com/app/479130/ESEA/','https://store.steampowered.com/app/502570/Houdini_Indie/','https://store.steampowered.com/app/431730/Aseprite/','https://store.steampowered.com/app/967170/Drum_Simulator/'] #software_test_urls

	#start_urls = ['https://store.steampowered.com/search/?sort_by=Reviews_DESC&category1=992&supportedlang=english'] #video (TODO: code to scrape video related content)

	#start_urls = ['https://store.steampowered.com/app/1059440/RWBY_Volume_6/','https://store.steampowered.com/app/245550/Free_to_Play/','https://store.steampowered.com/app/633030/Oats_Studios__Volume_1/','https://store.steampowered.com/app/812690/ULTIMATE_Career_Guide_3D_Artist/','https://store.steampowered.com/app/374570/Kung_Fury/','https://store.steampowered.com/app/743060/FreeFall_4K_VR/'] #video_test_urls

	#start_urls = ['https://store.steampowered.com/search/?sort_by=Reviews_DESC&category1=21&supportedlang=english'] #dlc

	#start_urls = ['https://store.steampowered.com/app/355880/The_Witcher_3_Wild_Hunt__Expansion_Pass/','https://store.steampowered.com/app/512032/Civilization_VI__Vikings_Scenario_Pack/','https://store.steampowered.com/sub/15148/','https://store.steampowered.com/app/373170/Freestyle_2___Naughty_Kitties_Pro_Pack/','https://store.steampowered.com/app/1106440/Lady_Jaster_for_Boobs_em_up__Wallpaper/','https://store.steampowered.com/app/9070/DOOM_3_Resurrection_of_Evil/'] #dlc_test_urls

	#start_urls = ['https://store.steampowered.com/search/?sort_by=Price_DESC&category1=10&supportedlang=english'] #demo_game

	#start_urls = ['https://store.steampowered.com/app/373960/Audiosurf_2_Demo/','https://store.steampowered.com/app/1055020/InfinityVR/','https://store.steampowered.com/app/220/HalfLife_2/','https://store.steampowered.com/app/41014/Serious_Sam_HD_The_Second_Encounter/','https://store.steampowered.com/app/589120/Danganronpa_V3_Killing_Harmony_Demo_Ver/'] #demo_game_test_urls. they are free so we have only 5 test urls

	allowed_domains = ['steampowered.com']
	rules = [
		Rule(LinkExtractor(
			 allow='/app/(.+)/',
			 restrict_css='#search_result_container'),
			 callback='parse_product'),
		Rule(LinkExtractor(
			 allow='page=(\d+)',
			 restrict_css='.search_pagination_right'))
	]

	def __init__(self, steam_id=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.steam_id = steam_id

	def start_requests(self):
		#for url in self.start_urls:
			#yield Request(url,callback=self.parse_product)
		if self.steam_id:
			yield Request(f'http://store.steampowered.com/app/{self.steam_id}/',callback=self.parse_product)
		else:
			yield from super().start_requests()

	def print_details(self,response):
		details = response.css('.details_block').extract_first()
		logger.info({details})

	def parse_product(self, response):
		cookies = {'wants_mature_content':'1','birthtime':'189302401','lastagecheckage': '1-January-1976'}
		if '/agecheck/app' in response.url:
			logger.info(f'Button-type age check triggered for {response.url}.')
			yield Request(response.url,cookies=cookies,meta={'dont_cache': True},callback=self.parse_product)
		else:
			yield load_product(response)
