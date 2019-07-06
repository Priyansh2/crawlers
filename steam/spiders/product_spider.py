import logging
import re
from w3lib.url import canonicalize_url, url_query_cleaner
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ..items import ProductItem, ProductItemLoader
logger = logging.getLogger(__name__)

def extract_game_description(response):
    raw_info = response.xpath("//*[@id='game_area_description' and @class='game_area_description']/descendant::node()").extract()
    if not raw_info:
        return "NA"
    else:
        description=''
        for item in raw_info:
            item = re.sub('[\r\t\n]', '', item).strip()
            if not item: ## this means originally contains one or more of \r,\t,\n
                description=description.strip()+"\n"
            else:
                if re.findall('<\/?[^>]*>',item):
                    if item.strip()=="<br>":
                        description+=description.strip()+"\n"
                else:
                    description+=item.strip()+" "
        description=description.strip()
        description = description.replace('About This Game',"")
        return description


def extract_user_reviews_counts(response):
    user_reviews_counts = response.css("span.user_reviews_counts ::text").extract()
    user_reviews_info={"total_reviews":"("+str(0)+")",
    "positive_reviews":"("+str(0)+")",
    "negative_reviews":"("+str(0)+")",
    "steam_purchasers_reviews":"("+str(0)+")",
    "other_purchasers_reviews":"("+str(0)+")",
    "en_lang_reviews":"("+str(0)+")",
    "all_lang_reviews":"("+str(0)+")"}
    if len(user_reviews_counts)>0:
        #assert len(user_reviews_counts)==8
        try:
            user_reviews_info["total_reviews"]=user_reviews_counts[0].split("(")[1].split(")")[0].strip().replace(',','').strip()
        except:
            pass
        try:
            user_reviews_info["positive_reviews"] = user_reviews_counts[1].split("(")[1].split(")")[0].strip().replace(',','').strip()
        except:
            pass
        try:
            user_reviews_info["negative_reviews"] = user_reviews_counts[2].split("(")[1].split(")")[0].strip().replace(',','').strip()
        except:
            pass
        try:
            user_reviews_info["steam_purchasers_reviews"] = user_reviews_counts[4].split("(")[1].split(")")[0].strip().replace(',','').strip()
        except:
            pass
        try:
            user_reviews_info["other_purchasers_reviews"] = user_reviews_counts[5].split("(")[1].split(")")[0].strip().replace(',','').strip()
        except:
            pass
        try:
            user_reviews_info["en_lang_reviews"] = user_reviews_counts[7].split("(")[1].split(")")[0].strip().replace(',','').strip()
        except:
            pass
        try:
            user_reviews_info["all_lang_reviews"] = user_reviews_counts[6].split("(")[1].split(")")[0].strip().replace(',','').strip()
        except:
            pass

        #assert int(user_reviews_info["total_reviews"])==int(user_reviews_info["all_lang_reviews"])
    return user_reviews_info


def load_product(response):
    """Load a ProductItem from the product page response."""
    loader = ProductItemLoader(item=ProductItem(), response=response)
    url = url_query_cleaner(response.url, ['snr'], remove=True)
    url = canonicalize_url(url)
    loader.add_value('url', url)
    found_id = re.findall('/app/(.*?)/', response.url)
    if found_id:
        id = found_id[0]
        img_url = f'https://steamcdn-a.akamaihd.net/steam/apps/{id}/header.jpg'
        loader.add_value('img_url',img_url)
        reviews_url = f'http://steamcommunity.com/app/{id}/reviews/?browsefilter=mostrecent&p=1'
        loader.add_value('reviews_url', reviews_url)
        loader.add_value('id', id)

    user_reviews_info = extract_user_reviews_counts(response)
    #detail_game_description=extract_game_description(response)
    try:
        brief_game_description= response.css('div.game_description_snippet::text').extract_first().strip()
    except AttributeError:
        brief_game_description="NA"
    loader.add_value('short_game_description',brief_game_description)
    #loader.add_value('long_game_description',detail_game_description)

    details = response.css('.details_block').extract_first()
    items_list=["developer","franchise","release_date","publisher"]
    curr_items_list=[]
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
                        loader.add_value(name, item)
            else:
                line = line.split("\r\n\t\t\r\n\t\r\n\t\t\t\r\n\t\t\t")
                for i in range(len(line)):
                    item = line[i]
                    if i!=len(line)-1:
                        item = re.sub('[\r\t\n]', '', item).strip()
                        if item:
                            item_name = item.split(":")[0].strip().lower()
                            curr_items_list.append(item_name)
                            if item_name in items_list:
                                item = item.split(":")[1].strip()
                                loader.add_value(item_name,item)
                    else:
                        #items = item.split("\r\n\t\t\r\n\t\t\r\n\t\t\t")
                        item =re.sub('[\r\t\n]', '',item).strip()
                        if item:
                            items = item.split("Release Date")
                            item_name = items[0].split(":")[0].strip().lower()
                            curr_items_list.append(item_name)
                            if item_name in items_list:
                                item = items[0].split(":")[1].strip()
                                loader.add_value(item_name,item)
                            date  = items[-1].split(":")[1].strip()
                            curr_items_list.append(date)
                            loader.add_value("release_date",date)

        for item_name in items_list:
            if item_name not in curr_items_list:
                loader.add_value(item_name,"NA")
    except:  # noqa E722
        pass

    loader.add_css('app_name', '.apphub_AppName ::text')
    loader.add_css('specs', '.game_area_details_specs a ::text')
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

    loader.add_value('user_reviews_info',user_reviews_info)
    return loader.load_item()


class ProductSpider(CrawlSpider):
    name = 'products'
    #start_urls = ['https://store.steampowered.com/search/?term=rage']
    start_urls = ['https://store.steampowered.com/search/?sort_by=Released_DESC&supportedlang=english']
    #start_urls = ['https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998&supportedlang=english']
    #start_urls = ['https://store.steampowered.com/app/750920/Shadow_of_the_Tomb_Raider/?snr=1_4_600__629','https://store.steampowered.com/app/233860/Kenshi/?snr=1_4_600__629','https://store.steampowered.com/app/419476/GGXrd_System_Voice__MILLIA_RAGE/?snr=1_7_7_151_150_1','https://store.steampowered.com/app/9200/RAGE/?snr=1_7_7_151_150_1']

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
        cookies = {'wants_mature_content':'1','birthtime':'189302401','lastagecheckage': '1-January-1976',}
        if self.steam_id:
            yield Request(f'http://store.steampowered.com/app/{self.steam_id}/',callback=self.parse_product)
            #yield Request(f'http://store.steampowered.com/app/{self.steam_id}/',cookies=cookies,callback=self.parse_product)
        else:
            yield from super().start_requests()

    def print_details(self,response):
        details = response.css('.details_block').extract_first()
        logger.debug({details})

    def parse_product(self, response):
        cookies = {'wants_mature_content':'1','birthtime':'189302401','lastagecheckage': '1-January-1976',}
        # Circumvent age selection form.
        if '/agecheck/app' in response.url:
            logger.debug("llllllllllllloooooooooooooooooooooooooooooolllllllllllllll")
            print("LOSER")
            #yield Request(response.url,cookies=cookies,callback=self.print_details)
        else:
            yield load_product(response)
