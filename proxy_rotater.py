import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import csv
import random
import os

def proxy_list(overwrite=False):
	data_dir = "data/"
	fn = 'proxies.csv'
	dir_files = os.listdir(data_dir)
	proxies = []

	if fn not in dir_files or overwrite:
		# Request url simulating user agent
		ua = UserAgent()
		headers = {'User-Agent': ua.random}
		res = requests.get('https://www.sslproxies.org/', headers=headers)
		print("Grabbing proxies list")
		
		# Grab html
		html = res.text
		soup = BeautifulSoup(html, 'lxml')
		soup = soup.find(id='proxylisttable')

		# Save our proxies
		for item in soup.tbody.find_all('tr'):
			ip = item.find_all('td')[0].string
			port = item.find_all('td')[1].string
			proxies.append([ip, port])

		with open(data_dir + fn, 'w') as f:
			writer = csv.writer(f)
			writer.writerows(proxies)
			print("Writing to " + fn)
	else:
		with open(data_dir + fn, 'r') as f:
			reader = csv.reader(f)
			proxies = list(reader)
			print("Loading " + fn)

	return proxies