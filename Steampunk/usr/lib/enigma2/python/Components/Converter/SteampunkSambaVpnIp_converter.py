from Components.Converter.Converter import Converter
from Components.Element import cached
from Poll import Poll
import process
import os
from time import time
import json, urllib
from Tools.LoadPixmap import LoadPixmap

myipdata = '/tmp/myipdata'
myipfile = '/tmp/myip.txt'
myflagfile = '/tmp/myflag.png'
novpnfile = '/tmp/SambaVpnIp/novpn.txt'
isvpnfile = '/usr/share/enigma2/Steampunk/skinparts/SambaVpnIp/isvpn.txt'
myipdataupdatepause = 300 #in seconds

def del_myipfiles(ip = 1, flag = 1, data = 1):
	if ip and os.path.exists(myipfile):
		os.remove(myipfile)
	if flag and os.path.exists(myflagfile):
		os.remove(myflagfile)
	if data and os.path.exists(myipdata):
		os.remove(myipdata)

def get_myipdata():
	try:
		if not os.path.exists(myipdata) or time() - os.path.getmtime(r"%s" %myipdata) > myipdataupdatepause:
			#os.system('wget -T 1 -O %s -q http://ip-api.com/json' %myipdata)
			#data = json.loads(open(myipdata,'r').read())
			data = urllib.urlopen('http://ip-api.com/json').read()
			f = open(myipdata,'w')
			f.write(data)
			f.close()
			data = json.loads(data)
		else:
			data = json.loads(open(myipdata,'r').read())
		country = data['countryCode'].encode('utf8')
		ip = data['query'].encode('utf8')
	except:
		country = ip = None
	return country, ip

del_myipfiles()

class SteampunkSambaVpnIp_converter(Poll, Converter, object):

	def __init__(self, type):
		Converter.__init__(self, type)
		self.type = type
		Poll.__init__(self)
		self.poll_interval = 60000
		self.poll_enabled = True

	@cached
	def getBoolean(self):
		p = process.ProcessList()
		name = ""
		if self.type == 'samba':
			name = str(p.named('smbd')).strip('[]')
		elif self.type == 'vpn':
			name = str(p.named('openvpn')).strip('[]')
			country, ip = get_myipdata()
			if name and country and ip:
				ip = ip.split('.')[0] + '.'
				if os.path.exists(novpnfile):
					novpn = open(novpnfile,'r').readlines()
					for line in novpn:
						if not line.startswith('#') and (country in line or line.startswith(ip)):
							name = ""
							break
				if os.path.exists(isvpnfile):
					isvpn = open(isvpnfile,'r').readlines()
					for line in isvpn:
						if not line.startswith('#') and (country in line or line.startswith(ip)):
							name = "ok"
							break
		if name:
			return True
		return False

	@cached
	def getText(self):
		ret = "---.---.---.---"
		if 'n+' in self.type:
			type = self.type[2:]
			name = type + ': '
		elif 'c+' in self.type:
			type = self.type[2:]
			name = ''
		else:
			type = self.type
			name = ''
		if type == 'myip':
			country, ip = get_myipdata()
			if country and ip:
				if 'c+' in self.type:
					ip = '(%s) ' %country + ip
				ip = ip + '|' + country
				if not os.path.exists(myipfile) or not os.path.exists(myflagfile) or not open(myipfile,'r').readline().replace('\n','').endswith(country):
					os.system('wget -T 1 -O %s -q http://flags.fmcdn.net/data/flags/small/%s.png' %(myflagfile,country.lower()))
				if not os.path.exists(myipfile) or not ip in open(myipfile,'r').readline():
					f = open(myipfile, 'w')
					f.write(ip)
					f.close()
			else:
				del_myipfiles(0,1,0)
				if not os.path.exists(myipfile) or time() - os.path.getmtime(r"%s" %myipfile) > myipdataupdatepause:
					p = os.system('wget -T 1 -O %s -q http://ipecho.net/plain' %myipfile)
					if p:
						p = os.system('wget -T 1 -O %s -q http://icanhazip.com' %myipfile)
					if p:
						del_myipfiles(1,0,0)
			if os.path.exists(myipfile):
				ret = name + open(myipfile,'r').readline().replace('\n','').split('|')[0]
			else:
				ret = 'ip server error'
		else:
			p = os.popen('ip address show').readlines()
			for line in p:
				if 'inet' in line and not 'inet6' in line and type in line:
					ret = name + line.split()[1].split('/')[0]
					break
		return ret

	@cached
	def getPixmap(self):
		if self.type == 'flag' and os.path.exists(myflagfile):
			return LoadPixmap(myflagfile)
		return None

	pixmap = property(getPixmap)
	boolean = property(getBoolean)
	text = property(getText)
