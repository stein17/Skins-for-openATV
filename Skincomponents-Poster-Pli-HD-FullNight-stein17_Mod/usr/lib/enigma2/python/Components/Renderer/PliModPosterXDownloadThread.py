# -*- coding: utf-8 -*-
import os
import sys
import re
import requests
import threading
from PIL import Image

PY3 = (sys.version_info[0] == 3)
try:
	if PY3:
		from urllib.parse import quote
		import html
		html_parser = html
	else:
		from urllib2 import quote
		from HTMLParser import HTMLParser
		html_parser = HTMLParser()
except:
	pass

try:
	from Components.config import config
	lng = config.osd.language.value
except:
	lng = None
	pass


tmdb_api = "3c3efcf47c3577558812bb9d64019d65"
tvdb_api = "a99d487bb3426e5f3a60dea6d3d3c7ef"

isz="185,278"

class PliModPosterXDownloadThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.checkMovie = ["film", "movie", "фильм", "кино", "ταινία", "película", "cinéma", "cine", "cinema", "filma"]
		self.checkTV = [ "serial", "series", "serie", "serien", "série", "séries", "serious",
			"folge", "episodio", "episode", "épisode", "l'épisode", "ep.", "animation",
			"staffel", "soap", "doku", "tv", "talk", "show", "news", "factual", "entertainment", "telenovela", 
			"dokumentation", "dokutainment", "documentary", "informercial", "information", "sitcom", "reality", 
			"program", "magazine", "mittagsmagazin", "т/с", "м/с", "сезон", "с-н", "эпизод", "сериал", "серия",
			"actualité", "discussion", "interview", "débat", "émission", "divertissement", "jeu", "magasine",
			"information", "météo", "journal", "sport", "culture", "infos", "feuilleton", "téléréalité",
			"société", "clips", "concert", "santé", "éducation", "variété" ]

	def search_tmdb(self,dwn_poster,title,shortdesc,fulldesc,channel=None):
		try:
			year = None
			url_tmdb = ""
			poster = None
			
			chkType, fd = self.checkType(shortdesc,fulldesc)
			if chkType=="":
				srch="multi"
			elif chkType.startswith("movie"):
				srch="movie"
			else:
				srch="tv"
			
			try:
				if re.findall('19\d{2}|20\d{2}', title):
					year = re.findall('19\d{2}|20\d{2}', fd)[1]
				else:
					year = re.findall('19\d{2}|20\d{2}', fd)[0]					
			except:
				year = ''
				pass
			
			url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(srch, tmdb_api, quote(title))
			if year:
				url_tmdb += "&year={}".format(year)
			if lng:
				url_tmdb += "&language={}".format(lng[:-3])
			
			
			poster = requests.get(url_tmdb).json()
			if poster and poster['results'] and poster['results'][0] and poster['results'][0]['poster_path']:
				url_poster = "https://image.tmdb.org/t/p/w{}{}".format(str(isz.split(",")[0]), poster['results'][0]['poster_path'])
				self.savePoster(dwn_poster, url_poster)
				return True, "[SUCCESS : tmdb] {} [{}-{}] => {} => {}".format(title,chkType,year,url_tmdb,url_poster)
			else:
				return False, "[SKIP : tmdb] {} [{}-{}] => {} (Not found)".format(title,chkType,year,url_tmdb)
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : tmdb] {} [{}-{}] => {} ({})".format(title,chkType,year,url_tmdb,str(e))
				
	def search_programmetv_google(self,dwn_poster,title,shortdesc,fulldesc,channel=None):
		try:
			url_ptv = ''
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
	
			chkType, fd = self.checkType(shortdesc,fulldesc)

			if chkType.startswith("movie"):
				return False, "[SKIP : programmetv-google] {} [{}] => Skip movie title".format(title,chkType)

			ptitle = self.UNAC(title)
			ptitle = ptitle.replace(' ','')
			
			url_ptv = "site:programme-tv.net+"+quote(title)
			if channel and title.find(channel.split()[0])<0:
				url_ptv += "+"+quote(channel)
				
			url_ptv = "https://www.google.com/search?q={}&tbm=isch&tbs=ift:jpg%2Cisz:m".format(url_ptv)
			ff = requests.get(url_ptv, stream=True, headers=headers, cookies = {'CONSENT' : 'YES+'}).text
			if not PY3:
				ff = ff.encode('utf-8')

			ptv_id=0
			plst = re.findall('\],\["https://www.programme-tv.net(.*?)",\d+,\d+]', ff)
			for  posterlst in plst:
				ptv_id += 1		
				url_poster = "https://www.programme-tv.net{}".format(posterlst)
				url_poster = re.sub(r"\\u003d", "=", url_poster)
				url_poster_size = re.findall(r'([\d]+)x([\d]+).*?([\w\.-]+).jpg',url_poster)
				if url_poster_size and url_poster_size[0]:
					get_title = self.UNAC(url_poster_size[0][2].replace('-',''))
					if ptitle==get_title:
						h_ori = float(url_poster_size[0][1])
						h_tar = float(re.findall('(\d+)',isz)[1])
						ratio = h_ori/h_tar
						w_ori = float(url_poster_size[0][0])
						w_tar = w_ori/ratio
						w_tar = int(w_tar)
						h_tar = int(h_tar)
						url_poster = re.sub('/\d+x\d+/',"/"+str(w_tar)+"x"+str(h_tar)+"/",url_poster)	
						url_poster = re.sub('crop-from/top/','',url_poster)
						self.savePoster(dwn_poster, url_poster)
						if self.verifyPoster(dwn_poster) and url_poster_size:
							return True, "[SUCCESS : programmetv-google] {} [{}] => Found title : '{}' => {} => {} (initial size: {}) [{}]".format(title,chkType,get_title,url_ptv,url_poster,url_poster_size,ptv_id)
						else:
							if os.path.exists(dwn_poster):
								os.remove(dwn_poster)	

			return False, "[SKIP : programmetv-google] {} [{}] => Not found [{}] => {}".format(title,chkType,ptv_id,url_ptv)

		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : programmetv-google] {} [{}] => {} ({})".format(title,chkType,url_ptv,str(e))
			
	def search_molotov_google(self,dwn_poster,title,shortdesc,fulldesc,channel=None):
		try:
			url_mgoo = ''
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}

			chkType, fd = self.checkType(shortdesc,fulldesc)
				
			ptitle = self.UNAC(title)
			if channel:
				pchannel = self.UNAC(channel).replace(' ','')
			else:
				pchannel = ''
			poster = None
			pltc=None
			imsg = ''
			
			url_mgoo = "site:molotov.tv+"+quote(title)
			if channel and title.find(channel.split()[0])<0:
				url_mgoo += "+"+quote(channel)
			url_mgoo = "https://www.google.com/search?q={}&tbm=isch".format(url_mgoo)
			ff = requests.get(url_mgoo, stream=True, headers=headers, cookies = {'CONSENT' : 'YES+'}).text
			if not PY3:
				ff = ff.encode('utf-8')
			plst = re.findall('https://www.molotov.tv/(.*?)"(?:.*?)?"(.*?)"', ff)
			len_plst = len(plst)
			molotov_id=0
			molotov_table=[0,0,None,None,0]
			molotov_final=False
			partialtitle=0
			partialchannel=0
			for pl in plst:
				get_path = "https://www.molotov.tv/"+pl[0]
				get_name = self.UNAC(pl[1])
				get_title = re.findall('(.*?)[ ]+en[ ]+streaming',get_name)
				if get_title:
					get_title = get_title[0]
				else:
					get_title = None
				get_channel = re.findall('(?:streaming|replay)?[ ]+sur[ ]+(.*?)[ ]+molotov.tv',get_name)
				if get_channel:
					get_channel = self.UNAC(get_channel[0]).replace(' ','')
				else:
					get_channel = re.findall('regarder[ ]+(.*?)[ ]+en',get_name)
					if get_channel:
						get_channel = self.UNAC(get_channel[0]).replace(' ','')
					else:
						get_channel = None
				partialchannel = self.PMATCH(pchannel,get_channel)
				partialtitle = self.PMATCH(ptitle,get_title)
				if partialtitle > molotov_table[0]:
					molotov_table = [partialtitle, partialchannel, get_name, get_path,molotov_id]
				if partialtitle == 100 and partialchannel == 100:
					molotov_final=True
					break
				molotov_id+=1
			
			if 	molotov_table[0]:
				ffm = requests.get(molotov_table[3], stream=True, headers=headers).text
				if not PY3:
					ffm = ffm.encode('utf-8')
				pltt = re.findall('"https://fusion.molotov.tv/(.*?)/jpg" alt="(.*?)"', ffm)
				if len(pltt)>0:	
					pltc = self.UNAC(pltt[0][1])
					plst = "https://fusion.molotov.tv/"+pltt[0][0]+"/jpg"
					imsg="Found title ({}%) & channel ({}%) : '{}' + '{}' [{}/{}]".format(molotov_table[0],molotov_table[1],molotov_table[2],pltc,molotov_table[4],len_plst)
			else:
				plst = re.findall('\],\["https://(.*?)",\d+,\d+].*?"https://.*?","(.*?)"', ff)
				len_plst = len(plst)
				if len_plst>0:
					for  pl in plst:
						if pl[1].startswith("Regarder") :
							pltc = self.UNAC(pl[1])
							partialtitle = self.PMATCH(ptitle,pltc)
							get_channel = re.findall('regarder[ ]+(.*?)[ ]+en',pltc)
							if get_channel:
								get_channel = self.UNAC(get_channel[0]).replace(' ','')
							else:
								get_channel = None
							partialchannel = self.PMATCH(pchannel,get_channel)	
							if partialchannel>0 and partialtitle<50:
								partialtitle=50
							plst = "https://"+pl[0]
							molotov_table = [partialtitle, partialchannel, pltc, plst,-1]				
							imsg="Fallback title ({}%) & channel ({}%) : '{}' [{}/{}]".format(molotov_table[0],molotov_table[1],pltc,-1,len_plst)
							break
			
			if molotov_table[0]==100 and molotov_table[1]==100:
				poster=plst
			elif chkType.startswith("movie"):
				imsg = "Skip movie type '{}' [{}%-{}%-{}]".format(pltc,molotov_table[0],molotov_table[1],len_plst)			
			elif molotov_table[0]==100:
				poster=plst
			elif molotov_table[0]>=50 and molotov_table[1]:
				poster=plst
			elif molotov_table[0]>=75:
				poster=plst
			elif chkType=='':
				imsg = "Skip unknown type '{}' [{}%-{}%-{}]".format(pltc,molotov_table[0],molotov_table[1],len_plst)
			elif molotov_table[0]>=25 and molotov_table[1]:
				poster=plst
			elif molotov_table[0]>=50:
				poster=plst
			else:
				imsg = "Not found '{}' [{}%-{}%-{}]".format(pltc,molotov_table[0],molotov_table[1],len_plst)
				
			if poster:
				url_poster = re.sub('/\d+x\d+/',"/"+re.sub(',','x',isz)+"/",poster)
				self.savePoster(dwn_poster, url_poster)
				if self.verifyPoster(dwn_poster):
					return True, "[SUCCESS : molotov-google] {} ({}) [{}] => {} => {} => {}".format(title,channel,chkType,imsg,url_mgoo,url_poster)
				else:
					if os.path.exists(dwn_poster):
						os.remove(dwn_poster)				
					return False, "[SKIP : molotov-google] {} ({}) [{}] => {} => {} => {} (jpeg error)".format(title,channel,chkType,imsg,url_mgoo,url_poster)
			else:
				return False, "[SKIP : molotov-google] {} ({}) [{}] => {} => {}".format(title,channel,chkType,imsg,url_mgoo)
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : molotov-google] {} [{}] => {} ({})".format(title,chkType,url_mgoo,str(e))

	def search_google(self,dwn_poster,title,shortdesc,fulldesc,channel=None):
		try:
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}

			chkType, fd = self.checkType(shortdesc,fulldesc)

			poster = None
			url_poster = ''
			year = None
			srch = None
			
			year = re.findall('19\d{2}|20\d{2}', fd)
			if len(year)>0:
				year = year[0]
			else:
				year = None

			if chkType.startswith("movie"):
				srch=chkType[6:]
			elif chkType.startswith("tv"):
				srch=chkType[3:]			
			
			#url_google = quote(title)
			url_google = '"'+quote(title)+'"'
			if channel and title.find(channel)<0:
				url_google += "+{}".format(quote(channel))
			if srch:
				url_google += "+{}".format(srch)
			if year:
				url_google += "+{}".format(year)

			#url_google = "https://www.google.com/search?q={}&tbm=isch&tbs=ift:jpg%2Cisz:m".format(url_google)
			url_google = "https://www.google.com/search?q={}&tbm=isch".format(url_google)
			ff = requests.get(url_google, stream=True, headers=headers, cookies = {'CONSENT' : 'YES+'}).text

			posterlst = re.findall('\],\["https://(.*?)",\d+,\d+]', ff)		
			if len(posterlst)==0:
				url_google = quote(title)
				url_google = "https://www.google.com/search?q={}&tbm=isch&tbs=ift:jpg%2Cisz:m".format(url_google)
				ff = requests.get(url_google, stream=True, headers=headers).text
				posterlst = re.findall('\],\["https://(.*?)",\d+,\d+]', ff)	
				
			for pl in posterlst:
				url_poster = "https://{}".format(pl)
				url_poster = re.sub(r"\\u003d", "=", url_poster)
				self.savePoster(dwn_poster, url_poster)
				if self.verifyPoster(dwn_poster):
					self.resizePoster(dwn_poster)
					poster = pl
					break

			if poster:
				return True, "[SUCCESS : google] {} [{}-{}] => {} => {}".format(title,chkType,year,url_google,url_poster)
			else:				
				if os.path.exists(dwn_poster):
					os.remove(dwn_poster)				
				return False, "[SKIP : google] {} [{}-{}] => {} => {} (Not found)".format(title,chkType,year,url_google,url_poster)
				
			
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)				
			return False, "[ERROR : google] {} [{}-{}] => {} => {} ({})".format(title,chkType,year,url_google,url_poster,str(e))

	def search_tvdb(self,dwn_poster,title,shortdesc,fulldesc,channel=None):
		try:
			series_nb = -1

			chkType, fd = self.checkType(shortdesc,fulldesc)

			ptitle = self.UNAC(title)
			
			year = re.findall('19\d{2}|20\d{2}', fd)
			if len(year)>0:
				year = year[0]
			else:
				year = ''

			url_tvdbg = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(quote(title))
			url_read = requests.get(url_tvdbg).text
			series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read) 
			series_name = re.findall('<SeriesName>(.*?)</SeriesName>', url_read)
			series_year = re.findall('<FirstAired>(19\d{2}|20\d{2})-\d{2}-\d{2}</FirstAired>', url_read)
			i = 0
			for iseries_year in series_year:
				if year=='':
					series_nb = 0
					break
				elif year==iseries_year:
					series_nb = i
					break
				i += 1

			poster = ""
			if series_nb>=0 and series_id and series_id[series_nb]:
				if series_name and series_name[series_nb]:
					series_name = self.UNAC(series_name[series_nb])
				else:
					series_name =''
				if self.PMATCH(ptitle,series_name):				
					url_tvdb = "https://thetvdb.com/api/{}/series/{}".format(tvdb_api, series_id[series_nb])
					if lng:
						url_tvdb += "/{}".format(lng[:-3])
					else:
						url_tvdb += "/en"
				
					url_read = requests.get(url_tvdb).text
					poster = re.findall('<poster>(.*?)</poster>', url_read)
				
			if poster and poster[0]:
				url_poster = "https://artworks.thetvdb.com/banners/{}".format(poster[0])
				self.savePoster(dwn_poster, url_poster)
				return True, "[SUCCESS : tvdb] {} [{}-{}] => {} => {} => {}".format(title,chkType,year,url_tvdbg,url_tvdb,url_poster)
			else:
				return False, "[SKIP : tvdb] {} [{}-{}] => {} (Not found)".format(title,chkType,year,url_tvdbg)
				
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : tvdb] {} => {} ({})".format(title,url_tvdbg,str(e))
			
	def search_imdb(self,dwn_poster,title,shortdesc,fulldesc,channel=None):
		try:
			url_poster = None

			chkType, fd = self.checkType(shortdesc,fulldesc)

			ptitle = self.UNAC(title)
			
			aka = re.findall('\((.*?)\)',fd)
			if len(aka)>1 and not aka[1].isdigit():
				aka = aka[1]
			elif len(aka)>0 and not aka[0].isdigit():
				aka = aka[0]
			else:
				aka = None
			if aka:
				paka = self.UNAC(aka)
			else:
				paka = ''
			
			year = re.findall('19\d{2}|20\d{2}', fd)
			if len(year)>0:
				year = year[0]
			else:
				year = ''

			imsg = ''
			url_mimdb =  ''
			url_imdb = ''
			
			if aka and aka!=title:
				url_mimdb = "https://m.imdb.com/find?q={}%20({})".format(quote(title),quote(aka))
			else:
				url_mimdb = "https://m.imdb.com/find?q={}".format(quote(title))
			url_read = requests.get(url_mimdb).text
			rc=re.compile('<img src="(.*?)".*?<span class="h3">\n(.*?)\n</span>.*?\((\d+)\)(\s\(.*?\))?(.*?)</a>',re.DOTALL)
			url_imdb = rc.findall(url_read)

			if len(url_imdb)==0 and aka:
				url_mimdb = "https://m.imdb.com/find?q={}".format(quote(title))
				url_read = requests.get(url_mimdb).text
				rc=re.compile('<img src="(.*?)".*?<span class="h3">\n(.*?)\n</span>.*?\((\d+)\)(\s\(.*?\))?(.*?)</a>',re.DOTALL)
				url_imdb = rc.findall(url_read)
				
			len_imdb = len(url_imdb)
			idx_imdb = 0
			pfound = False
			
			for imdb in url_imdb:
				imdb = list(imdb)
				imdb[1] = self.UNAC(imdb[1])
				tmp=re.findall('aka <i>"(.*?)"</i>',imdb[4])
				if tmp:
					imdb[4]=tmp[0]
				else:
					imdb[4]=''
				imdb[4] = self.UNAC(imdb[4])
				imdb_poster=re.search("(.*?)._V1_.*?.jpg",imdb[0])
				if imdb_poster:
					if imdb[3]=='':
						if year and year!='':
							if year==imdb[2]:
								url_poster = "{}._V1_UY278,1,185,278_AL_.jpg".format(imdb_poster.group(1))
								imsg = "Found title : '{}', aka : '{}', year : '{}'".format(imdb[1],imdb[4],imdb[2])
								if self.PMATCH(ptitle,imdb[1]) or self.PMATCH(ptitle,imdb[4]) or (paka!='' and self.PMATCH(paka,imdb[1])) or (paka!='' and self.PMATCH(paka,imdb[4])):
									pfound = True
									break
							elif not url_poster and (int(year)-1==int(imdb[2]) or int(year)+1==int(imdb[2])):
								url_poster = "{}._V1_UY278,1,185,278_AL_.jpg".format(imdb_poster.group(1))
								imsg = "Found title : '{}', aka : '{}', year : '+/-{}'".format(imdb[1],imdb[4],imdb[2])
								if ptitle==imdb[1] or ptitle==imdb[4] or (paka!='' and paka==imdb[1]) or (paka!='' and paka==imdb[4]):
									pfound = True
									break
						else:
							url_poster = "{}._V1_UY278,1,185,278_AL_.jpg".format(imdb_poster.group(1))
							imsg = "Found title : '{}', aka : '{}', year : ''".format(imdb[1],imdb[4])
							if ptitle==imdb[1] or ptitle==imdb[4] or (paka!='' and paka==imdb[1]) or (paka!='' and paka==imdb[4]):
								pfound = True
								break
				idx_imdb += 1
				
			if url_poster and pfound:
				self.savePoster(dwn_poster, url_poster)
				return True, "[SUCCESS : imdb] {} [{}-{}] => {} [{}/{}] => {} => {}".format(title,chkType,year,imsg,idx_imdb,len_imdb,url_mimdb,url_poster)
			else:
				return False, "[SKIP : imdb] {} [{}-{}] => {} (No Entry found [{}])".format(title,chkType,year,url_mimdb,len_imdb)
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : imdb] {} [{}-{}] => {} ({})".format(title,chkType,year,url_mimdb,str(e))

	def savePoster(self, dwn_poster, url_poster):
		with open(dwn_poster,'wb') as f:
			f.write(requests.get(url_poster, stream=True, allow_redirects=True, verify=False).content)
			f.close()

	def resizePoster(self, dwn_poster):
		try:
			img = Image.open(dwn_poster)
			width, height = img.size
			ratio = float(width) / float(height)
			new_height = int(isz.split(",")[1])
			new_width = int(ratio * new_height)
			rimg = img.resize((new_width, new_height), Image.ANTIALIAS)
			img.close()
			rimg.save(dwn_poster)
			rimg.close()
		except Exception as e:
			print("ERROR:{}".format(e))

	def verifyPoster(self, dwn_poster):
		try:
			img = Image.open(dwn_poster)
			img.verify()
			if img.format=="JPEG":
				pass
			else:
				try:
					os.remove(dwn_poster)
				except:
					pass
				return None
		except Exception as e:
			try:
				os.remove(dwn_poster)
			except:
				pass
			return None
		return True
		
	def checkType(self, shortdesc,fulldesc):
		if shortdesc and shortdesc!='':
			fd=shortdesc.splitlines()[0]
		elif fulldesc and fulldesc!='':
			fd=fulldesc.splitlines()[0]
		else:
			fd = ''
	
		srch = ""
		fds = fd[:60]
		for i in self.checkMovie:
			if i in fds.lower():
				srch = "movie:"+i
				break

		for i in self.checkTV:
			if i in fds.lower():
				srch = "tv:"+i
				break
	
		return srch, fd

	def UNAC(self,string):
		if not PY3:
			if type(string) is not unicode:
				string = unicode(string, encoding='utf-8')
		string = re.sub(u"u0026", "&", string)
		string = re.sub(u"u003d", "=", string)
		string = html_parser.unescape(string)
#		string = re.sub(r"[-,!/\.\":']",' ',string)
		string = re.sub(r"[,!\.\"]",' ',string)
		string = re.sub(r"[-/:']",'',string)
		string = re.sub(u"[ÀÁÂÃÄàáâãäåª]", 'a', string)
		string = re.sub(u"[ÈÉÊËèéêë]", 'e', string)
		string = re.sub(u"[ÍÌÎÏìíîï]", 'i', string)
		string = re.sub(u"[ÒÓÔÕÖòóôõöº]", 'o', string)
		string = re.sub(u"[ÙÚÛÜùúûü]", 'u', string)
		string = re.sub(u"[Ññ]", 'n', string)
		string = re.sub(u"[Çç]", 'c', string)
		string = re.sub(u"[Ÿýÿ]", 'y', string)
		string = re.sub(r"[^a-zA-Z0-9 ]","", string)
		string = string.lower()
		string = re.sub(r'\s{1,}', ' ', string)
		string = string.strip()	
		return string

	def PMATCH(self,textA,textB):
		if not textB or textB=='' or not textA or textA=='':
			return 0
		if textA==textB:
			return 100
		if textA.replace(" ","")==textB.replace(" ",""):
			return 100
		if len(textA)>len(textB):
			lId = len(textA.replace(" ",""))
		else:
			lId = len(textB.replace(" ",""))
		textA=textA.split()
		cId = 0
		for id in textA:
			if id in textB:
				cId +=len(id)
		cId = 100*cId/lId
		return cId

