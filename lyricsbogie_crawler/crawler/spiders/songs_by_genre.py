# -*- coding: utf-8 -*-
import scrapy
import string
from dateutil import parser
import logging
import os,sys,re,json

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

class SongsByGenreSpider(scrapy.Spider):
	name = 'songs_by_genre'
	def start_requests(self):
		urls = [
			'https://www.lyricsbogie.com/'
		]
		for url in urls:
			yield scrapy.Request(url=url, callback=self.parse_genres)

	def parse_genres(self, response):
		genres = response.css("div.menu-moods-container ul#menu-moods.menu li a::text").extract()
		for x in range(len(genres)):
			if len(genres[x].split())>1:
				genres[x] = genres[x].split()[0].lower()+"-"+genres[x].split()[1].lower()
			else:
				genres[x]=genres[x].lower()
		genres = sorted(genres)
		base_url ='https://www.lyricsbogie.com/mood/'
		for genre in genres:
			url = base_url+genre
			yield scrapy.Request(url=base_url+genre,callback=self.parse_page,meta={"front_page_url":url})

	def parse_page(self,response):
		page_info = response.css("div#wp_page_numbers ul li.page_info::text").extract_first()
		total_pages = page_info.split()[3]
		base_page_url = response.meta.get("front_page_url")
		genre = base_page_url.split("/")[4]
		for page_num in range(1,int(total_pages)+1):
			page_url = base_page_url+"/page/"+str(page_num)
			yield scrapy.Request(url=page_url,callback=self.parse_songs,meta={"genre":genre},dont_filter=True)

	def parse_songs(self,response):
		song_genre = response.meta.get("genre")
		lyrics_links= response.xpath('//*[@class="entry-title"]/a/@href').extract()
		for link in lyrics_links:
			song_type = link.split("/")[3]
			if song_type!="tv-shows":
				data={}
				data["song_genre"] = song_genre
				data["song_lyrics_url"] = link
				data["song_type"] = song_type
				yield scrapy.Request(url = link,callback=self.parse_lyrics,meta={"data":data},dont_filter=True)

	def parse_lyrics(self,response):
		song_lyrics = response.css("div#lyricsDiv.left blockquote p::text").extract()
		if song_lyrics is not None:
			data = response.meta.get("data")
			ps = response.xpath('//*[contains(@class,"movie_detail")]/p')
			movie_or_album_name, movie_or_album_director, song_singer, song_lyricist, song_composer, song_director, song_label, song_release_date, song_starring = ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"]
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
				elif "Movie/album" in item_name: ##name is of movie or album, this can be find by song_type
					movie_or_album_name = str_to_comma_separated(items)
				elif "Director" in item_name: ##same as above.
					movie_or_album_director = str_to_comma_separated(items)
			cover_image_url =response.xpath('//*[contains(@class,"single-featured")]/@data-src').extract()
			if cover_image_url:
				cover_image_url = cover_image_url[0]
			else:
				cover_image_url = "N/A"
			movie_or_album_cover_image_url = cover_image_url
			song_name = response.css("h1.page-title::text").extract()[0].split("Lyrics -")[0].strip()
			song_scores =  response.xpath('//*[@class="post-ratings" and contains(@id,"post-ratings")]/strong/text()').extract()
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
			data["song_name"] = song_name
			data["movie_or_album_cover_image_url"]=movie_or_album_cover_image_url
			data["song_rating"]=song_rating
			data["song_votes"] = song_votes
			data["movie_or_album_director"]=movie_or_album_director
			data["movie_or_album_name"] = movie_or_album_name
			data["song_starring"]=song_starring
			data["song_release_date"]=song_release_date
			data["song_singer"]=song_singer
			data["song_lyricist"]=song_lyricist
			data["song_label"]=song_label
			data["song_composer"]=song_composer
			data["song_director"]=song_director
			data["song_lyrics"]=song_lyrics
			return data
		else:
			logger.info(f'Failed to parse song lyrics in {response.url}.')