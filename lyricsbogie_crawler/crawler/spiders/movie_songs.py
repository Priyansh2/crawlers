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

class MovieSongsSpider(scrapy.Spider):
	name = 'movie_songs'
	#allowed_domains = ['www.lyricsbogie.com']
	#start_urls = ['http://www.lyricsbogie.com/']
	def start_requests(self):
		urls = [
			'https://www.lyricsbogie.com/category/movies/'
		]
		base_url = urls[0]
		indexes = list(string.ascii_lowercase)
		for index in indexes:
			urls.append(base_url+index)
		for url in urls:
			yield scrapy.Request(url=url, callback=self.parse_movies)


	def parse_movies(self, response):
		movies = response.xpath("//*[@class='cat_list']/li/a/@title").extract()
		movie_names = [movie.split("(")[0].strip() for movie in movies ]
		movie_release_years=[]
		for movie in movies:
			try:
				year = movie.split("(")[1].split(")")[0].strip()
			except IndexError:
				logger.info(f'IndexError in parsing {movie}')
			movie_release_years.append(year)
		songs_links = response.xpath("//*[@class='cat_list']/li/a/@href").extract()
		movie_data=[]
		if len(movie_names)==len(movie_release_years)==len(songs_links):
			for name,year,url in zip(movie_names,movie_release_years,songs_links):
				temp={}
				temp['movie_name'] = name
				temp['movie_release_year'] = year
				temp['movie_songs_url'] = url
				movie_data.append(temp)
			for movie_info in movie_data:
				yield scrapy.Request(url=movie_info['movie_songs_url'],callback=self.parse_songs,meta={"movie_info":movie_info})
		else:
			logger.info(f"Failed to parse movie in {response.url}.")


	def parse_songs(self,response):
		movie_info = response.meta.get("movie_info")
		movie_cover_image_url = response.xpath('//*[@class="movie_detail"]/div[@class="movie_image"]/img/@data-lazy-src').extract()
		if movie_cover_image_url:
			movie_cover_image_url = movie_cover_image_url[0]
		else:
			movie_cover_image_url = "N/A"
		ps = response.xpath('//*[@class="movie_detail"]/p')
		movie_starring, movie_producer, movie_director, movie_songs_director, movie_songs_lyricist, movie_songs_composer, movie_release_date = ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"], ["N/A"]
		for p in ps:
			item_name = p.xpath('./span/text()').extract_first()
			items = p.xpath('./a/text()').extract()
			if not items:
				items = p.xpath('./text()').extract()
			if "Starring" in item_name:
				movie_starring= str_to_comma_separated(items)
			elif "Producer" in item_name:
				movie_producer = str_to_comma_separated(items)
			elif "Director" in item_name and "Music" not in item_name:
				movie_director = str_to_comma_separated(items)
			elif "Music Director" in item_name:
				movie_songs_director = str_to_comma_separated(items)
			elif "Lyricist" in item_name:
				movie_songs_lyricist = str_to_comma_separated(items)
			elif "Composer" in item_name:
				movie_songs_composer = str_to_comma_separated(items)
			elif "Release on" in item_name:
				try:
					date = parser.parse(items[0]).strftime("%Y-%m-%d")
				except IndexError:
					data="N/A"
				movie_release_date =str_to_comma_separated([date])

		movie_info["movie_cover_image_url"]=movie_cover_image_url
		movie_info["movie_release_date"]=movie_release_date
		movie_info["movie_starring"]=movie_starring
		movie_info["movie_director"]=movie_director
		movie_info["movie_producer"]=movie_producer
		movie_info["movie_songs_director"]=movie_songs_director
		movie_info["movie_songs_lyricist"]=movie_songs_lyricist
		movie_info["movie_songs_composer"]=movie_songs_composer

		lyrics_links = response.xpath('//*[@class="song-detail"]/h3/a/@href').extract()
		song_names = response.xpath('//*[@class="song-detail"]/h3/a/text()').extract()
		song_data=[]
		if len(lyrics_links)==len(song_names):
			for name,url in zip(song_names,lyrics_links):
				temp={}
				temp['song_name'] = name
				temp['song_lyrics_url'] = url
				song_data.append(temp)
			movie_info["movie_songs"] = song_data
			for song_info in movie_info["movie_songs"]:
				yield scrapy.Request(url=song_info['song_lyrics_url'],callback=self.parse_lyrics,meta={'movie_and_songs_info':movie_info,'song_info':song_info})
		else:
			logger.info(f'Failed to parse song in {response.url}.')


	def parse_lyrics(self,response):
		movie_and_songs_info = response.meta.get("movie_and_songs_info")
		song_info = response.meta.get('song_info')
		## will extract music singers
		ps = response.xpath('//*[contains(@class,"movie_detail")]/p')
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

		song_type = response.url.split("/")[3] ## whether a song is from album,movie,tv-shows
		song_lyrics = response.css("div#lyricsDiv.left blockquote p::text").extract()
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

		if song_lyrics is not None and song_type!="tv-shows": ## dont want song with no lyrics and any "tv-show" song
			for j in range(len(movie_and_songs_info["movie_songs"])):
				if movie_and_songs_info["movie_songs"][j]==song_info:
					movie_and_songs_info["movie_songs"][j]["song_singer"] = song_singer
					movie_and_songs_info["movie_songs"][j]["song_lyricist"] = song_lyricist
					movie_and_songs_info["movie_songs"][j]["song_composer"] = song_composer
					movie_and_songs_info["movie_songs"][j]["song_director"] = song_director
					movie_and_songs_info["movie_songs"][j]["song_label"] = song_label
					movie_and_songs_info["movie_songs"][j]["song_release_date"] =song_release_date
					movie_and_songs_info["movie_songs"][j]["song_starring"] = song_starring
					movie_and_songs_info["movie_songs"][j]["song_votes"] = song_votes
					movie_and_songs_info["movie_songs"][j]["song_rating"] = song_rating
					movie_and_songs_info["movie_songs"][j]["song_lyrics"]=song_lyrics
			return movie_and_songs_info
		else:
			logger.info(f'Failed to parse song lyrics in {response.url}.')