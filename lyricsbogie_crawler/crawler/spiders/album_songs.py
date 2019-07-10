# -*- coding: utf-8 -*-
import scrapy
import string
from dateutil import parser
import logging

logger = logging.getLogger(__name__)
def str_to_comma_separated(x):
		if len(x)==1:
			temp = x[0].split(",")
			if len(temp)>1:
				return [i.strip() for i in temp]
			else:
				return temp
		elif len(x)==0:
			return ["N/A"]
		else:
			return x

class AlbumSongsSpider(scrapy.Spider):
	name = 'album_songs'
	#allowed_domains = ['www.lyricsbgie.com']
	#start_urls = ['http://www.lyricsbgie.com/']
	def start_requests(self):
		urls =[]
		base_url = 'https://www.lyricsbogie.com/category/albums/'
		indexes = list(string.ascii_lowercase)
		for index in indexes:
			urls.append(base_url+index)
		for url in urls:
			yield scrapy.Request(url=url, callback=self.parse_albums)

	def parse_albums(self, response):
		albums = response.xpath("//*[@class='cat_list']/li/a/@title").extract()
		album_names = [album.split("(")[0].strip() for album in albums]
		album_release_years=[]
		for album in albums:
			try:
				year = album.split("(")[1].split(")")[0].strip()
				album_release_years.append(year)
			except IndexError:
				if "tv" in album.lower():
					album_release_years.append("flagged")
				else:
					logger.info(f'IndexError in parsing {album}')
		songs_links = response.xpath("//*[@class='cat_list']/li/a/@href").extract()
		album_data=[]
		if len(album_names)==len(album_release_years)==len(songs_links):
			for name,year,url in zip(album_names,album_release_years,songs_links):
				temp={}
				if year!="flagged":
					temp['album_name'] = name
					temp['album_release_year'] = year
					temp['album_songs_url'] = url
					album_data.append(temp)
			for album_info in album_data:
				yield scrapy.Request(url=album_info['album_songs_url'],callback=self.parse_songs,meta={"album_info":album_info})
		else:
			logger.info(f"Failed to parse album in {response.url}.")


	def parse_songs(self,response):
		album_info = response.meta.get("album_info")

		album_cover_image_url = response.xpath('//*[@class="album_detail"]/div[@class="album_image"]/img/@data-lazy-src').extract()
		if album_cover_image_url:
			album_cover_image_url = album_cover_image_url[0]
		else:
			album_cover_image_url = "N/A"

		ps = response.xpath('//*[@class="album_detail"]/p')
		album_starring, album_producer, album_director, album_songs_director, album_songs_lyricist, album_songs_composer, album_release_date = ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"]
		for p in ps:
			item_name = p.xpath('./span/text()').extract_first()
			items = p.xpath('./a/text()').extract()
			if not items:
				items = p.xpath('./text()').extract()
			if "Starring" in item_name:
				album_starring= str_to_comma_separated(items)
			elif "Producer" in item_name:
				album_producer = str_to_comma_separated(items)
			elif "Director" in item_name and "Music" not in item_name:
				album_director = str_to_comma_separated(items)
			elif "Music Director" in item_name:
				album_songs_director = str_to_comma_separated(items)
			elif "Lyricist" in item_name:
				album_songs_lyricist = str_to_comma_separated(items)
			elif "Composer" in item_name:
				album_songs_composer = str_to_comma_separated(items)
			elif "Release on" in item_name:
				try:
					date = parser.parse(items[0]).strftime("%Y-%m-%d")
				except IndexError:
					data="N/A"
				album_release_date =str_to_comma_separated([date])
		album_info["album_cover_image_url"]=album_cover_image_url
		album_info["album_release_date"]=album_release_date
		album_info["album_starring"]=album_starring
		album_info["album_director"]=album_director
		album_info["album_producer"]=album_producer
		album_info["album_songs_director"]=album_songs_director
		album_info["album_songs_lyricist"]=album_songs_lyricist
		album_info["album_songs_composer"]=album_songs_composer

		lyrics_links = response.xpath('//*[@class="song-detail"]/h3/a/@href').extract()
		song_names = response.xpath('//*[@class="song-detail"]/h3/a/text()').extract()
		song_data=[]
		if len(lyrics_links)==len(song_names):
			for name,url in zip(song_names,lyrics_links):
				temp={}
				temp['song_name'] = name
				temp['song_lyrics_url'] = url
				song_data.append(temp)
			album_info["album_songs"] = song_data
			for song_info in album_info["album_songs"]:
				yield scrapy.Request(url=song_info['song_lyrics_url'],callback=self.parse_lyrics,meta={'album_and_songs_info':album_info,'song_info':song_info})
		else:
			logger.info(f'Failed to parse song in {response.url}.')


	def parse_lyrics(self,response):
		song_type = response.url.split("/")[3] ## whether a song is from album,album,tv-shows
		song_lyrics = response.css("div#lyricsDiv.left blockquote p::text").extract()
		#dont want 'song with no lyrics' and 'any "tv-show" song'
		if song_lyrics is not None and song_type!="tv-shows":
			album_and_songs_info = response.meta.get("album_and_songs_info")
			song_info = response.meta.get('song_info')
			ps = response.xpath('//*[contains(@class,"album_detail")]/p')
			song_singer, song_lyricist, song_composer, song_director, song_label, song_release_date, song_starring = ["N/A"] ,["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"]
			for p in ps:
				item_name = p.xpath('./span/text()').extract_first()
				items = p.xpath('./a/text()').extract()
				if not items:
					items = p.xpath('./text()').extract()
				if "Singers" in item_name:
					song_singer = str_to_comma_separated(items)
				elif "Song Lyricists" in item_name:
					song_lyricist = str_to_comma_separated(items)
				elif "Music Composer" in item_name:
					song_composer = str_to_comma_separated(items)
				elif "Music Director" in item_name:
					song_director = str_to_comma_separated(items)
				elif "Music Label" in item_name:
					song_label = str_to_comma_separated(items)
				elif "Release on" in item_name:
					try:
						date = parser.parse(items[0]).strftime("%Y-%m-%d")
					except IndexError:
						data="N/A"
					song_release_date =str_to_comma_separated([date])
				elif "Starring" in item_name:
					song_starring = str_to_comma_separated(items)

			song_scores =  response.xpath('//*[@class="post-ratings" and @id="post-ratings-18491"]/strong/text()').extract()
			if song_scores:
				try:
					song_votes = int(song_scores[0]) ## vote count (people who voted or gives their rating our of 5)
				except (IndexError,ValueError) as e:
					song_votes=0
				try:
					song_rating = song_scores[1] ## Average rating out of 5 (star rating) [sum of ratings by users/ total users]
				except (IndexError,ValueError) as e:
					song_rating=0
			else:
				song_votes,song_rating=0,0

			for j in range(len(album_and_songs_info["album_songs"])):
				if album_and_songs_info["album_songs"][j]==song_info:
					album_and_songs_info["album_songs"][j]["song_singer"] = song_singer
					album_and_songs_info["album_songs"][j]["song_lyricist"] = song_lyricist
					album_and_songs_info["album_songs"][j]["song_composer"] = song_composer
					album_and_songs_info["album_songs"][j]["song_director"] = song_director
					album_and_songs_info["album_songs"][j]["song_label"] = song_label
					album_and_songs_info["album_songs"][j]["song_release_date"] =song_release_date
					album_and_songs_info["album_songs"][j]["song_starring"] = song_starring
					album_and_songs_info["album_songs"][j]["song_votes"] = song_votes
					album_and_songs_info["album_songs"][j]["song_rating"] = song_rating
					album_and_songs_info["album_songs"][j]["song_lyrics"]=song_lyrics
			return album_and_songs_info
		else:
			logger.info(f'Failed to parse song lyrics in {response.url}.')
