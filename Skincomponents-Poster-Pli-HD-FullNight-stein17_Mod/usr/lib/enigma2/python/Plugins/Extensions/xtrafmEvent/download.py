# -*- coding: utf-8 -*-
# by digiteng...06.2020, 11.2020, 11.2021
# Only posters and backdrops, fixed and minimized! (by stein17), 06.2024
# Special thanks go to@Villak from the OpenSpa team, who has fixed and improved many things.
# I have adapted his version here again to my needs.
from __future__ import absolute_import
from Components.AVSwitch import AVSwitch
from Screens.Screen import Screen
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ActionMap import ActionMap
from enigma import eEPGCache, eTimer, getDesktop, ePixmap, ePoint, eSize, loadJPG
from Components.config import config
from ServiceReference import ServiceReference
from Screens.MessageBox import MessageBox
import Tools.Notifications
import requests
from requests.utils import quote
import urllib3
urllib3.disable_warnings()
import os
import re
import json
from PIL import Image
import socket
from . import xtra
from datetime import datetime
import time
import threading
from Components.ProgressBar import ProgressBar
import io
from Plugins.Extensions.xtrafmEvent.skins.xtrafmSkins import *

if config.plugins.xtrafmEvent.tmdbAPI.value != "":
	tmdb_api = config.plugins.xtrafmEvent.tmdbAPI.value
else:
	tmdb_api = "3c3efcf47c3577558812bb9d64019d65"
if config.plugins.xtrafmEvent.tvdbAPI.value != "":
	tvdb_api = config.plugins.xtrafmEvent.tvdbAPI.value
else:
	tvdb_api = "a99d487bb3426e5f3a60dea6d3d3c7ef"
if config.plugins.xtrafmEvent.fanartAPI.value != "":
	fanart_api = config.plugins.xtrafmEvent.fanartAPI.value
else:
	fanart_api = "6d231536dea4318a88cb2520ce89473b"

try:
	import sys
	PY3 = sys.version_info[0]
	if PY3 == 3:
		from builtins import str
		from builtins import range
		from builtins import object
		from configparser import ConfigParser
		from _thread import start_new_thread
	else:
		from ConfigParser import ConfigParser
		from thread import start_new_thread
except:
	pass

try:
	from Components.Language import language
	lang = language.getLanguage()
	lang = lang[:2]
except:
	try:
		lang = config.osd.language.value[:-3]
	except:
		lang = "en"

lang_path = r"/usr/lib/enigma2/python/Plugins/Extensions/xtrafmEvent/languages"
try:
	lng = ConfigParser()
	if PY3 == 3:
		lng.read(lang_path,  encoding='utf8')
	else:
		lng.read(lang_path)
	lng.get(lang, "0")
except:
	try:
		lang="en"
		lng = ConfigParser()
		if PY3 == 3:
			lng.read(lang_path,  encoding='utf8')
		else:
			lng.read(lang_path)
	except:
		pass

epgcache = eEPGCache.getInstance()
pathLoc =  "{}xtrafmEvent/".format(config.plugins.xtrafmEvent.loc.value)
desktop_size = getDesktop(0).size().width()
headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
REGEX = re.compile(
		r'([\(\[]).*?([\)\]])|'
		r'(: odc.\d+)|'
		r'(\d+: odc.\d+)|'
		r'(\d+ odc.\d+)|(:)|'
		r'( -(.*?).*)|(,)|'
		r'!|'
		r'[^\w\s.-]'
		r'/.*|'
		r'\|\s[0-9]+\+|'
		r'[0-9]+\+|'
		r'\s\d{4}\Z|'
		r'([\(\[\|].*?[\)\]\|])|'
		r'(\"|\"\.|\"\,|\.)\s.+|'
		r'\"|:|'
		r'\*|'
		r'[\(\[\|\?¿\]\]\|]'
		r'Премьера\.\s|'
		r'(х|Х|м|М|т|Т|д|Д)/ф\s|'
		r'(х|Х|м|М|т|Т|д|Д)/с\s|'
		r'\s(с|С)(езон|ерия|-н|-я)\s.+|'
		r'\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\.\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\s(ч|ч\.|с\.|с)\s\d{1,3}.+|'
		r'\d{1,3}(-я|-й|\sс-н).+|', re.DOTALL)

class downloads(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		if desktop_size <= 1280:
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_1':
				self.skin = download_720
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_2':
				self.skin = download_720_2
		else:
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_1':
				self.skin = download_1080
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_2':
				self.skin = download_1080_2
		self.titles = ""
		self['status'] = Label()
		self['info'] = Label()
		self['info2'] = Label()
		self['Picture'] = Pixmap()
		self['Picture2'] = Pixmap()
		self['int_statu'] = Label()
		self['key_red'] = Label(_('Back'))
		self['key_green'] = Label(_('Download'))
		# self['key_yellow'] = Label(_('Show'))
		self['key_blue'] = Label(_(lng.get(lang, '66')))
		self['actions'] = ActionMap(['xtrafmEventAction'], 
		{
		'cancel': self.close, 
		'red': self.close, 
		'ok':self.save,
		'green':self.save,
		# 'yellow':self.ir,
		'blue':self.showhide
		}, -2)
		self['progress'] = ProgressBar()
		self['progress'].setRange((0, 100))
		self['progress'].setValue(0)
		self.setTitle(_("░ {}".format(lng.get(lang, '45'))))
		self.screen_hide = False
		self.onLayoutFinish.append(self.showFilm)
		self.onLayoutFinish.append(self.intCheck)

	def intCheck(self):
		try:
			socket.setdefaulttimeout(2)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
			self['int_statu'].setText("☻")
			return True
		except:
			self['int_statu'].hide()
			self['status'].setText(lng.get(lang, '68'))
			return False

	def searchLanguage(self):
		try:
			from Components.Language import language
			lang = language.getLanguage()
			lang = lang[:2]
		except:
			try:
				lang = config.osd.language.value[:-3]
			except:
				lang = "en"
		return lang
		
	def showhide(self):
		if self.screen_hide:
			Screen.show(self)
		else:
			Screen.hide(self)
		self.screen_hide = not (self.screen_hide)

	def save(self):
		if config.plugins.xtrafmEvent.searchMOD.value == lng.get(lang, '14'):
			self.currentChEpgs()
		if config.plugins.xtrafmEvent.searchMOD.value == lng.get(lang, '13'):
			self.selBouquets()

	def currentChEpgs(self):
		events = None
		import NavigationInstance
		ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference().toString()
		events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
		if events:
			try:
				n = config.plugins.xtrafmEvent.searchNUMBER.value
				titles = []
				for i in range(int(n)):
					try:
						title = events[i][4]
						title = REGEX.sub('', title).strip()
						titles.append(title)
					except:
						continue
					if i == n:
						break
				self.titles = list(dict.fromkeys(titles))
				start_new_thread(self.downloadEvents, ())
			except Exception as err:
				with open("/tmp/xtrafmEvent.log", "a+") as f:
					f.write("currentChEpgs, %s\n"%(err))

	def selBouquets(self):
		if os.path.exists("{}bqts".format(pathLoc)):
			with open("{}bqts".format(pathLoc), "r") as f:
				refs = f.readlines()
			nl = len(refs)
			eventlist=[]
			for i in range(nl):
				ref = refs[i]
				try:
					events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
					n = config.plugins.xtrafmEvent.searchNUMBER.value
					for i in range(int(n)):
						title = events[i][4]
						title = REGEX.sub('', title).strip()
						eventlist.append(title)
				except:
					pass
			self.titles = list(dict.fromkeys(eventlist))
			start_new_thread(self.downloadEvents, ())


####################################################
	def downloadEvents(self):
		dwnldFile=""
		self.title = ""
		self['progress'].setValue(0)
		lang = None
		now = datetime.now()
		st = now.strftime("%d/%m/%Y %H:%M:%S ")
		tmdb_poster_downloaded = 0
		tvdb_poster_downloaded = 0
		maze_poster_downloaded = 0
		fanart_poster_downloaded = 0
		tmdb_backdrop_downloaded = 0
		tvdb_backdrop_downloaded = 0
		fanart_backdrop_downloaded = 0
		banner_downloaded = 0
		extra_downloaded = 0
		extra2_downloaded = 0
		extra3_poster_downloaded = 0
		extra3_info_downloaded = 0
		info_downloaded = 0
		title_search = 0
		title = ""
		infs = {}
		imdb_id = None
		Year = ""
		Rating=""
		Rated=""
		glist=""
		Duration=""
		description=""
		Type=""
		if config.plugins.xtrafmEvent.onoff.value:
# elcinema(en) #################################################################
			if config.plugins.xtrafmEvent.extra3.value == True:
				Type = ""
				Genre = ""
				Language = ""
				Country = ""
				imdbRating = ""
				Rated = ""
				Duration = ""
				Year = ""
				Director = ""
				Writer = ""
				Actors = ""
				Plot = ""
				setime = ""
				try:
					
					if not os.path.exists("/tmp/urlo.html"):
						url = "https://elcinema.com/en/tvguide/"
						urlo = requests.get(url)
						urlo = urlo.text.replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', 'and').replace('(', '').replace(')', '')
						with io.open("/tmp/urlo.html", "w", encoding="utf-8") as f:
							f.write(urlo)
					if os.path.exists("/tmp/urlo.html"):
						with io.open("/tmp/urlo.html", "r", encoding="utf-8") as f:
							urlor = f.read()
						titles = re.findall('<li><a title="(.*?)" href="/en/work', urlor)
					n = len(titles)
				except Exception as err:
					with open("/tmp/xtrafmEvent.log", "a+") as f:
						f.write("elcinema urlo, %s, %s\n"%(title, err))
				for title in titles:
					
					try:
						title = REGEX.sub('', title).strip()
						dwnldFile = "{}poster/{}.jpg".format(pathLoc, title)
						info_files = "{}infos/{}.json".format(pathLoc, title)
						tid = re.findall('title="%s" href="/en/work/(.*?)/"'%title, urlor)[0]
						self.setTitle(_("{}".format(title)))
						if not os.path.exists(dwnldFile):
							turl =	"https://elcinema.com/en/work/{}/".format(tid)
							jurlo = requests.get(turl.strip(), stream=True, allow_redirects=True, headers=headers)
							jurlo = jurlo.text.replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', 'and').replace('(', '').replace(')', '')
							# poster elcinema
							img = re.findall('<img src="(.*?).jpg" alt=""', jurlo)[0]
							open(dwnldFile, "wb").write(requests.get("{}.jpg".format(img), stream=True, allow_redirects=True).content)
							self['info'].setText("► {}, EXTRA3, POSTER".format(title.upper()))
							extra3_poster_downloaded += 1
							downloaded = extra3_poster_downloaded
							self.prgrs(downloaded, n)
							self.showPoster(dwnldFile)
					except Exception as err:
						with open("/tmp/xtrafmEvent.log", "a+") as f:
							f.write("elcinema poster, %s, %s\n"%(title, err))
					#info elcinema,
					if not os.path.exists(info_files):
						turl =	"https://elcinema.com/en/work/{}/".format(tid)
						jurlo = requests.get(turl.strip(), stream=True, allow_redirects=True, headers=headers)
						jurlo = jurlo.text.replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', 'and').replace('(', '').replace(')', '')
						try:
							setime = urlor.partition('title="%s"'%title)[2].partition('</ul>')[0].strip()
							setime = re.findall("(\d\d\:\d\d) (.*?) - (\d\d\:\d\d) (.*?)</li>", setime)
							setime = setime[0][0]+setime[0][1]+" - "+setime[0][2]+setime[0][3]
						except:
							pass
						try:
							Category = jurlo.partition('<li>Category:</li>')[2].partition('</ul>')[0].strip()
							Category = Category.partition('<li>')[2].partition('</li>')[0].strip()
						except:
							pass
						try:
							glist=[]
							Genre = (jurlo.partition('<li>Genre:</li>')[2].partition('</ul>')[0]).strip().split("</a> </li>")
							for i in range(len(Genre)-1):
								Genre = (jurlo.partition('<li>Genre:</li>')[2].partition('</ul>')[0]).strip().split("</a> </li>")[i]
								Genre = Genre.partition('">')[2].strip()
								glist.append(Genre)
						except:
							pass
						try:
							llist=[]
							Language = (jurlo.partition('<li>Language:</li>')[2].partition('</ul>')[0]).strip().split("</a> </li>")
							for i in range(len(Language)-1):
								Language = (jurlo.partition('<li>Language:</li>')[2].partition('</ul>')[0]).strip().split("</a> </li>")[i]
								Language = Language.partition('">')[2].strip()
								llist.append(Language)
						except:
							pass
						try:
							clist=[]
							Country = (jurlo.partition('<li>Country:</li>')[2].partition('</ul>')[0]).strip().split("</a> </li>")
							for i in range(len(Country)-1):
								Country = (jurlo.partition('<li>Country:</li>')[2].partition('</ul>')[0]).strip().split("</a> </li>")[i]
								Country = Country.partition('">')[2].strip()
								clist.append(Country)
						except:
							pass
						try:
							Rating = re.findall("class='fa fa-star'></i> (.*?) </span><div", jurlo)[0]
							Rated = jurlo.partition('<li>MPAA</li><li>')[2].partition('</li></ul></li>')[0].strip()
							if Rated =="":
								Rated = jurlo.partition('class="censorship purple" title="Censorship:')[2].partition('"><li>')[0].strip()
						except:
							pass					
						try:	
							Year = jurlo.partition('href="/en/index/work/release_year/')[2].partition('/"')[0].strip()
						except:
							pass
						try:
							Duration = re.findall("<li>(.*?) minutes</li>", jurlo)[0]
						except:
							pass
						try:
							dlist=[]
							Director = (jurlo.partition('<li>Director:</li>')[2].partition('</ul>')[0]).strip().split('</a>')
							for i in range(len(Director)-1):
								Director = (jurlo.partition('<li>Director:</li>')[2].partition('</ul>')[0]).strip().split('</a>')[i]
								Director = Director.partition('/">')[2].strip()
								dlist.append(Director)
						except:
							pass
						try:
							wlist=[]
							Writer = (jurlo.partition('<li>Writer:</li>')[2].partition('</ul>')[0]).strip().split('</a>')
							for i in range(len(Writer)-1):
								Writer = (jurlo.partition('<li>Writer:</li>')[2].partition('</ul>')[0]).strip().split('</a>')[i]
								Writer = Writer.partition('/">')[2].strip()
								wlist.append(Writer)
						except:
							pass
						try:
							calist=[]
							Cast = (jurlo.partition('<li>Cast:</li>')[2].partition('</ul>')[0]).strip().split("</a> </li>")
							for i in range(len(Cast)-1):
								Cast = (jurlo.partition('<li>Cast:</li>')[2].partition('</ul>')[0]).strip().split("</a> </li>")[i]
								Cast = Cast.partition('">')[2].strip()
								calist.append(Cast)
						except:
							pass
						try:
							Description1 = re.findall("<p>(.*?)<a href='#' id='read-more'>...Read more</a><span class='hide'>", jurlo)[0]
							Description2 = re.findall("<a href='#' id='read-more'>...Read more</a><span class='hide'>(.*?)\.", jurlo)[0]
							Description = "{}{}".format(Description1, Description2)
						except:
							try:
								Description = re.findall("<p>(.*?)</p>", jurlo)[0]
							except:
								pass
						try:
							ej = {
							"Title": "%s"%title, 
							"Start-End Time": "%s"%setime,
							"Type": "%s"%Category,
							"Year": "%s"%Year,
							"imdbRating": "%s"%Rating, 
							"Rated": "%s"%Rated,
							"Genre": "%s"%(', '.join(glist)), 
							"Duration": "%s min."%Duration,
							"Language": "%s"%(', '.join(llist)),
							"Country": "%s"%(', '.join(clist)),
							"Director": "%s"%(', '.join(dlist)),
							"Writer": "%s"%(', '.join(wlist)),
							"Actors": "%s"%(', '.join(calist)),
							"Plot": "%s"%Description,
							}
							open(info_files, "w").write(json.dumps(ej))

							if os.path.exists(info_files):
								extra3_info_downloaded += 1
								downloaded = extra3_info_downloaded
								self.prgrs(downloaded, n)
								self['info'].setText("► {}, EXTRA3, INFO".format(title.upper()))
							if os.path.exists(dwnldFile):
								self.showPoster(dwnldFile)

						except Exception as err:
							with open("/tmp/xtrafmEvent.log", "a+") as f:
								f.write("elcinema ej, %s, %s\n"%(title, err))
					time.sleep(5)

			n = len(self.titles)
			for i in range(n):
				title = self.titles[i]
				title = title.strip()
				self.setTitle(_("{}".format(title)))
	# tmdb_Poster() #################################################################
				if config.plugins.xtrafmEvent.poster.value == True:
					dwnldFile = "{}poster/{}.jpg".format(pathLoc, title)
					if config.plugins.xtrafmEvent.tmdb.value == True:
						if not os.path.exists(dwnldFile):
							try:
								srch = config.plugins.xtrafmEvent.searchType.value
								 
								url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(srch, tmdb_api, quote(title))
								if config.plugins.xtrafmEvent.searchLang.value == True:
									url_tmdb += "&language={}".format(self.searchLanguage())
								poster = ""
								poster = requests.get(url_tmdb).json()['results'][0]['poster_path']
								p_size = config.plugins.xtrafmEvent.TMDBpostersize.value
								url = "https://image.tmdb.org/t/p/{}{}".format(p_size, poster)
								if poster != "":
									open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
								if os.path.exists(dwnldFile):
									self['info'].setText("►  {}, TMDB, POSTER".format(title.upper()))
									tmdb_poster_downloaded += 1
									downloaded = tmdb_poster_downloaded
									self.prgrs(downloaded, n)
									self.showPoster(dwnldFile)
									#continue
									try:
										img = Image.open(dwnldFile)
										img.verify()
									except Exception as err:
										with open("/tmp/xtrafmEvent.log", "a+") as f:
											f.write("deleted tmdb poster: %s.jpg\n"%title)
										try:
											os.remove(dwnldFile)
										except:
											pass
							except Exception as err:
								with open("/tmp/xtrafmEvent.log", "a+") as f:
									f.write("tmdb poster, %s, %s\n"%(title, err))
		# tvdb_Poster() #################################################################
					if config.plugins.xtrafmEvent.tvdb.value == True:
						try:
							img = Image.open(dwnldFile)
							img.verify()
						except Exception as err:
							with open("/tmp/xtrafmEvent.log", "a+") as f:
								f.write("deleted : %s.jpg\n"%title)
							try:
								os.remove(dwnldFile)
							except:
								pass
						if not os.path.exists(dwnldFile):
							try:
								url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(quote(title))
								url_read = requests.get(url_tvdb).text
								series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
								if series_id:
									url_tvdb = "https://thetvdb.com/api/{}/series/{}/{}".format(tvdb_api, series_id, self.searchLanguage())
									url_read = requests.get(url_tvdb).text
									poster = ""
									poster = re.findall('<poster>(.*?)</poster>', url_read)[0]
									if poster != '':
										url = "https://artworks.thetvdb.com/banners/{}".format(poster)
										if config.plugins.xtrafmEvent.TVDBpostersize.value == "thumbnail":
											url = url.replace(".jpg", "_t.jpg")
										open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
										if os.path.exists(dwnldFile):
											self['info'].setText("►  {}, TVDB, POSTER".format(title.upper()))
											tvdb_poster_downloaded += 1
											downloaded = tvdb_poster_downloaded
											self.prgrs(downloaded, n)
											self.showPoster(dwnldFile)
											#continue
											try:
												img = Image.open(dwnldFile)
												img.verify()
											except Exception as err:
												with open("/tmp/xtrafmEvent.log", "a+") as f:
													f.write("deleted tvdb poster: %s.jpg\n"%title)
												try:
													os.remove(dwnldFile)
												except:
													pass
							except Exception as err:
								with open("/tmp/xtrafmEvent.log", "a+") as f:
									f.write("tvdb poster, %s, %s\n"%(title, err))

	# backdrop() #################################################################
				if config.plugins.xtrafmEvent.backdrop.value == True:
					dwnldFile = "{}backdrop/{}.jpg".format(pathLoc, title)
					if config.plugins.xtrafmEvent.extra.value == True:
						if not os.path.exists(dwnldFile):
							try:
								url = "http://capi.tvmovie.de/v1/broadcasts/search?q={}&page=1&rows=1".format(title.replace(" ", "+"))
								try:
									url = requests.get(url).json()['results'][0]['images'][0]['filepath']['android-image-320-180']
								except:
									pass
								open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
								if os.path.exists(dwnldFile):
									self['info'].setText("►  {}, EXTRA, BACKDROP".format(title.upper()))
									extra_downloaded += 1
									downloaded = extra_downloaded
									self.prgrs(downloaded, n)
									self.showBackdrop(dwnldFile)
									try:
										img = Image.open(dwnldFile)
										img.verify()
									except Exception as err:
										with open("/tmp/xtrafmEvent.log", "a+") as f:
											f.write("deleted extra poster: %s.jpg\n"%title)
										try:
											os.remove(dwnldFile)
										except:
											pass
							except Exception as err:
								with open("/tmp/xtrafmEvent.log", "a+") as f:
									f.write("extra, %s, %s\n"%(title, err))
					if config.plugins.xtrafmEvent.tmdb.value == True:
						try:
							img = Image.open(dwnldFile)
							img.verify()
						except Exception as err:
							with open("/tmp/xtrafmEvent.log", "a+") as f:
								f.write("deleted : %s.jpg\n"%title)
							try:
								os.remove(dwnldFile)
							except:
								pass
						if not os.path.exists(dwnldFile):	
							srch = "multi"
							url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(srch, tmdb_api, quote(title))
							if config.plugins.xtrafmEvent.searchLang.value:
								url_tmdb += "&language={}".format(self.searchLanguage())
							try:
								backdrop = requests.get(url_tmdb).json()['results'][0]['backdrop_path']
								if backdrop:
									backdrop_size = config.plugins.xtrafmEvent.TMDBbackdropsize.value
									# backdrop_size = "w300"
									url = "https://image.tmdb.org/t/p/{}{}".format(backdrop_size, backdrop)
									open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
									if os.path.exists(dwnldFile):
										self['info'].setText("►  {}, TMDB, BACKDROP".format(title.upper()))
										tmdb_backdrop_downloaded += 1
										downloaded = tmdb_backdrop_downloaded
										self.prgrs(downloaded, n)
										self.showBackdrop(dwnldFile)
										try:
											img = Image.open(dwnldFile)
											img.verify()
										except Exception as err:
											with open("/tmp/xtrafmEvent.log", "a+") as f:
												f.write("deleted tmdb backdrop: %s.jpg\n"%title)
											try:
												os.remove(dwnldFile)
											except:
												pass
							except Exception as err:
								with open("/tmp/xtrafmEvent.log", "a+") as f:
									f.write("tmdb-backdrop, %s, %s\n"%(title, err))
					if config.plugins.xtrafmEvent.tvdb.value == True:
						try:
							img = Image.open(dwnldFile)
							img.verify()
						except Exception as err:
							with open("/tmp/xtrafmEvent.log", "a+") as f:
								f.write("deleted : %s.jpg\n"%title)
							try:
								os.remove(dwnldFile)
							except:
								pass
						if not os.path.exists(dwnldFile):
							try:
								url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(quote(title))
								url_read = requests.get(url_tvdb).text
								series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
								if series_id:
									url_tvdb = "https://thetvdb.com/api/{}/series/{}/{}.xml".format(tvdb_api, series_id, self.searchLanguage())
									url_read = requests.get(url_tvdb).text
									backdrop = re.findall('<fanart>(.*?)</fanart>', url_read)[0]
									if backdrop:
										url = "https://artworks.thetvdb.com/banners/{}".format(backdrop)
										if config.plugins.xtrafmEvent.TVDBbackdropsize.value == "thumbnail":
											url = url.replace(".jpg", "_t.jpg")
										open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
										if os.path.exists(dwnldFile):
											self['info'].setText("►  {}, TVDB, BACKDROP".format(title.upper()))
											tvdb_backdrop_downloaded += 1
											downloaded = tvdb_backdrop_downloaded
											self.prgrs(downloaded, n)
											self.showBackdrop(dwnldFile)
											try:
												img = Image.open(dwnldFile)
												img.verify()
											except Exception as err:
												with open("/tmp/xtrafmEvent.log", "a+") as f:
													f.write("deleted tvdb backdrop: %s.jpg\n"%title)
												try:
													os.remove(dwnldFile)
												except:
													pass
							except Exception as err:
								with open("/tmp/xtrafmEvent.log", "a+") as f:
									f.write("tvdb-backdrop, %s, %s\n"%(title, err))
					if config.plugins.xtrafmEvent.extra2.value == True:
						try:
							img = Image.open(dwnldFile)
							img.verify()
						except Exception as err:
							with open("/tmp/xtrafmEvent.log", "a+") as f:
								f.write("deleted : %s.jpg\n"%title)
							try:
								os.remove(dwnldFile)
							except:
								pass
						if not os.path.exists(dwnldFile):
							try:
								url = "https://www.bing.com/images/search?q={}".format(title.replace(" ", "+"))
								if config.plugins.xtrafmEvent.PB.value == "posters":
									url += "+poster"
								else:
									url += "+backdrop"
								ff = requests.get(url, stream=True, headers=headers).text
								p = ',&quot;murl&quot;:&quot;(.*?)&'
								url = re.findall(p, ff)[0]
							except Exception as err:
								with open("/tmp/xtrafmEvent.log", "a+") as f:
									f.write("bing-backdrop, %s, %s\n"%(title, err))
								try:
									url = "https://www.google.com/search?q={}&tbm=isch&tbs=sbd:0".format(title.replace(" ", "+"))
									if config.plugins.xtrafmEvent.PB.value == "posters":
										url += "+poster"
									else:
										url += "+backdrop"
									ff = requests.get(url, stream=True, headers=headers).text
									p = re.findall('\],\["https://(.*?)",\d+,\d+]', ff)[0]
									url = "https://{}".format(p)
								except Exception as err:
									with open("/tmp/xtrafmEvent.log", "a+") as f:
										f.write("google-backdrop, %s, %s\n"%(title, err))
							try:
								open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
								if os.path.exists(dwnldFile):
									self['info'].setText("►  {}, BING, BACKDROP".format(title.upper()))
									extra2_downloaded += 1
									downloaded = extra2_downloaded
									self.prgrs(downloaded, n)
									self.showBackdrop(dwnldFile)
									try:
										img = Image.open(dwnldFile)
										img.verify()
									except Exception as err:
										with open("/tmp/xtrafmEvent.log", "a+") as f:
											f.write("deleted Bing backdrop: %s.jpg\n"%title)
										try:
											os.remove(dwnldFile)
										except:
											pass
							except Exception as err:
								with open("/tmp/xtrafmEvent.log", "a+") as f:
									f.write("bing backdrop, %s, %s\n"%(title, err))							
	
# infos #################################################################
				if config.plugins.xtrafmEvent.info.value == True:
					Title=None
					Type = None
					Genre = None
					Language = None
					Country = None
					imdbRating = None
					imdbID = None
					Rated = None
					Duration = None
					Year = None
					Released=None
					Director = None
					Writer = None
					Actors = None
					Awards=None
					Plot = ""
					Description = None
					Rating = ""
					glist=[]
					data = {}

					info_files = "{}infos/{}.json".format(pathLoc, title)
					if config.plugins.xtrafmEvent.omdbAPI.value:
						omdb_apis = config.plugins.xtrafmEvent.omdbAPI.value
						if not isinstance(omdb_apis, list):
							omdb_apis = [omdb_apis]
					else:
						omdb_apis = ["42d86ce4", "550a7c40", "5a7216eb", "8ec53e6b"]
					if not os.path.exists(info_files):
						try:
							print("omdb_apis antes for:", omdb_apis)
							for omdb_api in omdb_apis:
								try:
									print("omdb API value after for" , omdb_api)
									url = "http://www.omdbapi.com/?apikey={}&t={}".format(omdb_api, title)
									print(url)
									info_omdb = requests.get(url, timeout=5)
									if info_omdb.status_code == 200:
										Title = info_omdb.json()["Title"]
										Year = info_omdb.json()["Year"]
										Rated = info_omdb.json()["Rated"]
										Duration = info_omdb.json()["Runtime"]
										Released = info_omdb.json()["Released"]
										Genre = info_omdb.json()["Genre"]
										Director = info_omdb.json()["Director"]
										Writer = info_omdb.json()["Writer"]
										Actors = info_omdb.json()["Actors"]
										if not config.plugins.xtrafmEvent.searchLang.value:
											Plot = info_omdb.json()["Plot"]
										Country = info_omdb.json()["Country"]
										Awards = info_omdb.json()["Awards"]
										imdbRating = info_omdb.json()["imdbRating"]
										imdbID = info_omdb.json()["imdbID"]
										Type = info_omdb.json()["Type"]
								except Exception as e:
									print(f"Error obtaining information from IMDb: {str(e)}")
									print(f"Content of the OMDB response: {info_omdb.text}")

							url_find = 'https://m.imdb.com/find?q={}'.format(title)
							ff = requests.get(url_find).text
							rc = re.compile('<a href="/title/(.*?)/"', re.DOTALL)
							imdbID = rc.search(ff).group(1)
							url= "https://m.imdb.com/title/{}/?ref_=fn_al_tt_0".format(imdbID)
							ff = requests.get(url).text
						except Exception as err:
							with open("/tmp/xtrafmEvent.log", "a+") as f:
								f.write("infos, %s, %s\n" % (title, err))
							try:
								rtng = re.findall('"aggregateRating":{(.*?)}',ff)[0] #ratingValue":8.4
								imdbRating = rtng.partition('ratingValue":')[2].partition('}')[0].strip()
								if Rated == None:
									Rated = ff.partition('contentRating":"')[2].partition('","')[0].replace("+", "").strip() # "contentRating":"18+","genre":["Crime","Drama","Thriller"],"datePublished":"2019-10-04"
								glist=[]
								genre = ff.partition('genre":[')[2].partition('],')[0].strip().split(",")
								for i in genre:
									genre=(i.replace('"',''))
									glist.append(genre)
								if Genre == None:
									Genre = ", ".join(glist)
								if Year == None:
									Year = ff.partition('datePublished":"')[2].partition('"')[0].strip()
								if Type == None:
									Type = ff.partition('class="ipc-inline-list__item">')[2].partition('</li>')[0].strip().split(" ")
									if Type[0].lower() == "tv":
										Type = "Tv Series"
									else:
										Type = "Movie"
							except:
								pass
							try:
								if Duration == None:
									Duration = re.findall('\d+h \d+min', ff)[0]
							except:
								try:
									if Duration == None:	
										Duration = re.findall('\d+min', ff)[0]
								except:
									pass
							try:
								if config.plugins.xtrafmEvent.searchLang.value == True:
									srch = "multi"
									srch = config.plugins.xtrafmEvent.searchType.value
									url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}&language={}".format(srch, tmdb_api, quote(title), self.searchLanguage())
									Plot = requests.get(url_tmdb).json()['results'][0]['overview']
									if Plot == "":
										url_tvdb = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(title)
										url_read = requests.get(url_tvdb).text
										series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
										if series_id:
											url_tvdb = "https://thetvdb.com/api/{}/series/{}/{}".format(tvdb_api, series_id, self.searchLanguage())
											url_read = requests.get(url_tvdb).text
											Plot = re.findall('<Overview>(.*?)</Overview>', url_read)[0]
							except:
								pass
							data = {
							"Title": Title, 
							"Year": Year,
							"imdbRating": imdbRating, 
							"Rated": Rated,
							"Released":Released,
							"Genre": Genre,
							"Duration": Duration,
							"Country": Country,
							"Director": Director,
							"Writer": Writer,
							"Actors": Actors,
							"Awards": Awards,
							"Type": Type,
							"Plot": Plot,
							"imdbID": imdbID,
							}
							js = json.dumps(data, ensure_ascii=False)
							try:
								with open(info_files, "w") as f:
									f.write(js)
							except:
								pass

							if os.path.exists(info_files):
								info_downloaded += 1
								downloaded = info_downloaded
								self.prgrs(downloaded, n)
								self['info'].setText("►  {}, IMDB, INFO".format(title.upper()))
							continue
						except Exception as err:
							with open("/tmp/xtrafmEvent.log", "a+") as f:
								f.write("infos, %s, %s\n"%(title, err))
			now = datetime.now()
			dt = now.strftime("%d/%m/%Y %H:%M:%S")
			report = "\n\nSTART : {}\nEND : {}\
				\nPOSTER; Tmdb :{}, Tvdb :{}, Maze :{}, Fanart :{}\
				\nBACKDROP; Tmdb :{}, Tvdb :{}, Fanart :{}, Extra :{}, Bing :{}\
				\nBANNER :{}\
				\nINFOS :{}".format(st, dt, 
				str(tmdb_poster_downloaded), str(tvdb_poster_downloaded), str(maze_poster_downloaded), str(fanart_poster_downloaded), 
				str(tmdb_backdrop_downloaded), str(tvdb_backdrop_downloaded), str(fanart_backdrop_downloaded), 
				str(extra_downloaded), str(extra2_downloaded),
				str(banner_downloaded), 
				str(info_downloaded)) 
#				str(extra3_poster_downloaded), str(extra3_info_downloaded))
			self['info2'].setText(report)
			self.report = report
			try:
				if os.path.exists("/tmp/urlo.html"):
					os.remove("/tmp/urlo.html")
			except:
				pass			
			with open("/tmp/xtrafm_report", "a+") as f:
				f.write("%s"%report)
			Screen.show(self)
			self.brokenImageRemove()
			self.brokenInfoRemove()
			self.cleanRam()
			return
####################################################################################################################################
	def prgrs(self, downloaded, n):
		self['status'].setText("Download : {} / {}".format(downloaded, n))
		self['progress'].setValue(int(100*downloaded//n))

	def showPoster(self, dwnldFile):
		if config.plugins.xtrafmEvent.onoff.value:
			if not config.plugins.xtrafmEvent.timerMod.value:
				self["Picture2"].hide()
				self["Picture"].setPixmap(loadJPG(dwnldFile))
				self["Picture"].setScale(1)
				self["Picture"].show()
				if desktop_size <= 1280:
					self["Picture"].resize(eSize(185,278))
					self["Picture"].move(ePoint(955,235))
					self["Picture"].setScale(1)
				else:
					self["Picture"].setScale(1)
					self["Picture"].resize(eSize(185,278))
					self["Picture"].move(ePoint(1450,400))

	def showBackdrop(self, dwnldFile):
		if config.plugins.xtrafmEvent.onoff.value:
			if not config.plugins.xtrafmEvent.timerMod.value:
				self["Picture2"].hide()
				self["Picture"].setPixmap(loadJPG(dwnldFile))
				if desktop_size <= 1280:
					self["Picture"].resize(eSize(300,170))
					self["Picture"].move(ePoint(895,280))
					self["Picture"].setScale(1)
				else:
					self["Picture"].setScale(1)
					self["Picture"].resize(eSize(300,170))
					self["Picture"].move(ePoint(1400,400))

	def showBanner(self, dwnldFile):
		if config.plugins.xtrafmEvent.onoff.value:
			if not config.plugins.xtrafmEvent.timerMod.value:
				self["Picture2"].hide()
				self["Picture"].setPixmap(loadJPG(dwnldFile))
				if desktop_size <= 1280:
					self["Picture"].resize(eSize(400,80))
					self["Picture"].move(ePoint(845,320))
					self["Picture"].setScale(1)
					self["Picture"].setZPosition(10)
				else:
					self["Picture"].setScale(1)
					self["Picture"].resize(eSize(400,90))
					self["Picture"].move(ePoint(1400,400))

	def showFilm(self):
		self["Picture2"].instance.setPixmapFromFile("/usr/lib/enigma2/python/Plugins/Extensions/xtrafmEvent/pic/film2.png")
		self["Picture2"].instance.setScale(1)
		self["Picture2"].show()

	def brokenImageRemove(self):
		b = os.listdir(pathLoc)
		rmvd = 0
		try:
			for i in b:
				bb = "{}{}/".format(pathLoc, i)
				fc = os.path.isdir(bb)
				if fc != False:	
					for f in os.listdir(bb):
						if f.endswith('.jpg'):
							try:
								img = Image.open("{}{}".format(bb, f))
								img.verify()
							except:
								try:
									os.remove("{}{}".format(bb, f))
									rmvd += 1
								except:
									pass
		except:
			pass

	def brokenInfoRemove(self):
		try:
			infs = os.listdir("{}infos".format(pathLoc))
			for i in infs:
				with open("{}infos/{}".format(pathLoc, i)) as f:
					rj = json.load(f)
				if rj["Response"] == "False":
					os.remove("{}infos/{}".format(pathLoc, i))
		except:
			pass
			
	def cleanRam(self):
		os.system("echo 1 > /proc/sys/vm/drop_caches")
		os.system("echo 2 > /proc/sys/vm/drop_caches")
		os.system("echo 3 > /proc/sys/vm/drop_caches")
