# -*- coding: utf-8 -*-
# by digiteng...07.2020 - 11.2020 - 11.2021
# FOR INFO
# <widget source="session.Event_Now" render="Label" position="50,545" size="930,400" font="Regular; 32" halign="left" transparent="1" zPosition="2" backgroundColor="background">
  	# <convert type="xtraInfo">Title,Year,Description</convert>
# </widget>
# 
# FOR IMDB RATING STAR...
# <ePixmap pixmap="xtra/star_b.png" position="990,278" size="200,20" alphatest="blend" zPosition="2" transparent="1" />
# <widget source="ServiceEvent" render="Progress" pixmap="xtra/star.png" position="990,278" size="200,20" alphatest="blend" transparent="1" zPosition="2" backgroundColor="background">
	# <convert type="xtraInfo">imdbRatingValue</convert>
# </widget>

from __future__ import absolute_import
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.config import config
from Components.Converter.xtrafmEventGenre import getGenreStringSub
import re
import json
import os

try:
	pathLoc = config.plugins.xtrafmEvent.loc.value
except:
	pass

REGEX = re.compile(
		r'([\(\[]).*?([\)\]])|'
		r'(: odc.\d+)|'
		r'(\d+: odc.\d+)|'
		r'(\d+ odc.\d+)|(:)|'
		
		r'!|'
		r'/.*|'
		r'\|\s[0-9]+\+|'
		r'[0-9]+\+|'
		r'\s\d{4}\Z|'
		r'([\(\[\|].*?[\)\]\|])|'
		r'(\"|\"\.|\"\,|\.)\s.+|'
		r'\"|:|'
		r'\*|'
		r'Премьера\.\s|'
		r'(х|Х|м|М|т|Т|д|Д)/ф\s|'
		r'(х|Х|м|М|т|Т|д|Д)/с\s|'
		r'\s(с|С)(езон|ерия|-н|-я)\s.+|'
		r'\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\.\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\s(ч|ч\.|с\.|с)\s\d{1,3}.+|'
		r'\d{1,3}(-я|-й|\sс-н).+|', re.DOTALL)
		
class xtrafmInfo(Converter, object):

	Title = "Title"
	Year = "Year"
	Rated = "Rated"
	Released = "Released"
	Runtime = "Runtime"
	Genre = "Genre"
	Director = "Director"
	Writer = "Writer"
	Actors = "Actors"
	Plot = "Description"
	Language = "Language"
	Country = "Country"
	Awards = "Awards"
	imdbRating = "imdbRating"
	imdbRatingValue = "imdbRatingValue"
	imdbRatingSimple = "imdbRatingSimple"
	imdbVotes = "imdbVotes"
	Type = "Type"
	totalSeasons = "totalSeasons"
	SE = "SE"
	Duration = "Duration"
	Compact = "Compact"

	def __init__(self, type):
		Converter.__init__(self, type)
		self.types = str(type).split(",")

	@cached
	def getText(self):
		event = self.source.event
		if event:
			if self.types:
				evnt = event.getEventName()
				evntNm = REGEX.sub('', evnt).strip()
				rating_json = "{}xtrafmEvent/infos/{}.json".format(pathLoc, evntNm)
				fd = "{}\n{}\n{}".format(event.getEventName(), event.getShortDescription(), event.getExtendedDescription())
				evnt = []
				try:
					for type in self.types:
						type.strip()
						if os.path.exists(rating_json):
							with open(rating_json) as f:
								read_json = json.load(f)

						if type == self.Title:
							try:
								title = read_json['Title']
								if title:
									evnt.append("Title : {}".format(title))
							except:
								evnt.append("Title : {}".format(event.getEventName()))
						elif type == self.Year:
							try:
								year = read_json["Year"]
								if year:
									evnt.append("Year : {}".format(year))
							except:
								year = ''
								fd = fd.replace(',', '').replace('(', '').replace(')', '')
								fdl = ['\d{4} [A-Z]+', '[A-Z]+ \d{4}', '[A-Z][a-z]+\s\d{4}', '\+\d+\s\d{4}']
								for i in fdl:
									year = re.findall(i, fd)
									if year:
										year = re.sub(r'\(.*?\)|\.|\+\d+', ' ', year[0]).strip()
										evnt.append("Year : {}".format(year))
										break	
						elif type == self.Rated:
							try:
								Rated = read_json["Rated"]
								if Rated != "Not Rated":
									evnt.append("Rated : {}+".format(Rated))
								elif Rated == "Not Rated":
									parentName = ''
									prs = ['[aA]b ((\d+))', '[+]((\d+))', 'Od lat: ((\d+))', '(\d+)[+]', '(TP)', '[-](\d+)']
									for i in prs:
										prr = re.search(i, fd)
										if prr:
											parentName = prr.group(1)
											parentName = parentName.replace('7', '6').replace('10', '12').replace('TP', '0')
											evnt.append("Rated : {}+".format(parentName))
											break
								else:
									try:
										age = ''
										rating = event.getParentalData()
										if rating:
											age = rating.getRating()
											evnt.append("Rated : {}+".format(age))
									except:
										pass
							except:
								parentName = ''
								prs = ['[aA]b ((\d+))', '[+]((\d+))', 'Od lat: ((\d+))', '(\d+)[+]', '(TP)', '[-](\d+)']
								for i in prs:
									prr = re.search(i, fd)
									if prr:
										parentName = prr.group(1)
										parentName = parentName.replace('7', '6').replace('10', '12').replace('TP', '0')
										evnt.append("Rated : {}+".format(parentName))
										break
						elif type == self.Released:
							try:
								Released = read_json["Released"]
								if Released:
									evnt.append("Released : {}".format(Released))
							except:
								pass
						elif type == self.Runtime:
							try:
								Runtime = read_json["Runtime"]
								if Runtime:
									evnt.append("Runtime : {}".format(Runtime))
							except:
								pass
						elif type == self.Genre:
							try:
								Genre = read_json["Genre"]
								if Genre:
									evnt.append("Genre : {}".format(Genre))
							except:
								genres = event.getGenreDataList()
								if genres:
									genre = genres[0]
									evnt.append("Genre : {}".format(getGenreStringSub(genre[0], genre[1])))

						elif type == self.Director:
							try:
								Director = read_json["Director"]
								if Director:
									evnt.append("Director : {}".format(Director))
							except:
								pass
						elif type == self.Writer:
							try:
								Writer = read_json["Writer"]
								if Writer:
									evnt.append("Writer : {}".format(Writer))
							except:
								pass
						elif type == self.Actors:
							try:
								Actors = read_json["Actors"]
								if Actors:
									evnt.append("Actors : {}".format(Actors))
							except:
								pass
						elif type == self.Plot:
							try:
								Plot = read_json["Plot"]
								if Plot:
									evnt.append("Description : {}".format(Plot))
								else:
									evnt.append("Description : {}".format(fd))
							except:
								evnt.append("Description : {}".format(fd))
								
						elif type == self.Language:
							try:
								Language = read_json["Language"]
								if Language:
									evnt.append("Language : {}".format(Language))
							except:
								pass
						elif type == self.Country:
							try:
								Country = read_json["Country"]
								if Country:
									evnt.append("Country : {}".format(Country))
							except:
								pass

						elif type == self.Awards:
							try:
								Awards = read_json["Awards"]
								if Awards:
									evnt.append("Awards : {}".format(Awards))
							except:
								pass
						elif type == self.imdbRating:
							try:
								imdbRating = read_json["imdbRating"]
								if imdbRating:
									evnt.append("IMDB : {}".format(imdbRating))
							except:
								pass
						elif type == self.imdbRatingSimple:
							try:
								imdbRatingSimple = read_json["imdbRating"]
								if imdbRatingSimple:
									evnt.append("{}".format(imdbRatingSimple))
							except:
								pass
						elif type == self.imdbVotes:
							try:
								imdbVotes = read_json["imdbVotes"]
								if imdbVotes:
									evnt.append("imdbVotes : {}".format(imdbVotes))
							except:
								pass
						elif type == self.Type:
							try:
								Type = read_json["Type"]
								if Type:
									evnt.append("Type : {}".format(Type))
							except:
								pass
						elif type == self.totalSeasons:
							try:
								totalSeasons = read_json["totalSeasons"]
								if totalSeasons:
									evnt.append("TotalSeasons : {}".format(totalSeasons))
							except:
								pass
						elif type == self.Duration:
							try:
								Duration = read_json["Duration"]
								if totalSeasons:
									evnt.append("Duration : {}min".format(Duration))
							except:
								drtn = round(event.getDuration()// 60)
								if drtn > 0:
									evnt.append("Duration : {}min".format(drtn))
								else:
									prs = re.findall(r' \d+ Min', fd)
									if prs:
										drtn = round(prs[0])
										evnt.append("Duration : {}min".format(drtn))
						elif type == self.SE:
							""
							try:
								prs = ['(\d+). Staffel, Folge (\d+)', 'T(\d+) Ep.(\d+)', '"Episodio (\d+)" T(\d+)']
								for i in prs:
									seg = re.search(i, fd)
									if seg:
										s = seg.group(1).zfill(2)
										e = seg.group(2).zfill(2)
										evnt.append("SE : S{}E{}".format(s, e))
							except:
								pass
						# Compact
						elif type == self.Compact:

							try:
								Genre = read_json["Genre"]
								if Genre:
									Genre = Genre.split(",")
									evnt.append("{}".format(Genre[0]))
							except:
								try:
									genres = event.getGenreDataList()
									if genres:
										genre = genres[0]
										genre = getGenreStringSub(genre[0], genre[1])
										genre = genre.split(",")
										genre = genre[0]
										evnt.append("{}".format(genre))
								except:
									pass

							try:
								Country = read_json["Country"]
								Country = Country.replace("United States", "USA").replace("United Kingdom", "UK")
								if Country:
									evnt.append("{}".format(Country))
							except:
								pass
							try:
								imdbRating = read_json["imdbRating"]
								if imdbRating:
									evnt.append("IMDB:{}".format(imdbRating))
							except:
								pass
						
							try:
								Rated = read_json["Rated"]
								if Rated != "Not Rated":
									evnt.append("{}+".format(Rated))
								elif Rated == "Not Rated":
									parentName = ''
									prs = ['[aA]b ((\d+))', '[+]((\d+))', 'Od lat: ((\d+))', '(\d+)[+]', '(TP)', '[-](\d+)']
									for i in prs:
										prr = re.search(i, fd)
										if prr:
											parentName = prr.group(1)
											parentName = parentName.replace('7', '6').replace('10', '12').replace('TP', '0')
											evnt.append("{}+".format(parentName))
											break
								else:
									try:
										age = ''
										rating = event.getParentalData()
										if rating:
											age = rating.getRating()
											evnt.append("{}+".format(age))
									except:
										pass
							except:
								parentName = ''
								prs = ['[aA]b ((\d+))', '[+]((\d+))', 'Od lat: ((\d+))', '(\d+)[+]', '(TP)', '[-](\d+)']
								for i in prs:
									prr = re.search(i, fd)
									if prr:
										parentName = prr.group(1)
										parentName = parentName.replace('7', '6').replace('10', '12').replace('TP', '0')
										evnt.append("{}+".format(parentName))
										break						

							try:
								prs = ['(\d+). Staffel, Folge (\d+)', 'T(\d+) Ep.(\d+)', '"Episodio (\d+)" T(\d+)']
								for i in prs:
									seg = re.search(i, fd)
									if seg:
										s = seg.group(1).zfill(2)
										e = seg.group(2).zfill(2)
										evnt.append("S{}E{}".format(s, e))
							except:
								pass						
							
							try:
								year = ''
								fd = fd.replace(',', '').replace('(', '').replace(')', '')
								fdl = ['\d{4} [A-Z]+', '[A-Z]+ \d{4}', '[A-Z][a-z]+\s\d{4}', '\+\d+\s\d{4}']
								for i in fdl:
									year = re.findall(i, fd)
									if year:
										year = re.sub(r'\(.*?\)|\.|\+\d+', ' ', year[0]).strip()
										evnt.append("{}".format(year))
										break
							except:
								year = read_json["Year"]
								if year:
									evnt.append("{}".format(year))


						if type != self.Compact:
							tc = "\n".join(evnt)
						else:
							# tc = " | ".join(evnt)

							tc = '\\c0000??00 • '
							tc += '\\c00??????'
							tc = tc.join(evnt)

					return tc
				except:
					return ""
		else:
			return ""

	text = property(getText)

	@cached
	def getValue(self):
		event = self.source.event
		if event:
			if self.types:
				evnt = event.getEventName()
				evntNm = REGEX.sub('', evnt).strip()
				rating_json = "{}xtrafmEvent/infos/{}.json".format(pathLoc, evntNm)

				try:
					for type in self.types:
						type.strip()
						if type == self.imdbRatingValue:
							if os.path.exists(rating_json):
								with open(rating_json) as f:
									read_json = json.load(f)
								try:
									imdbRatingValue = read_json["imdbRating"]
									if imdbRatingValue:
										return int(10*(float(imdbRatingValue)))
									else:
										return 0
								except:
									return 0
				except:
					return 0
		else:
			return 0

	value = property(getValue)
	range = 100
	
