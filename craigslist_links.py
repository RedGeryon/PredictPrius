import requests
import os
from bs4 import BeautifulSoup
import re
import pickle
import json

def link_state(overwrite=False):
	# Set initial directory and files info
	data_dir = "data/"
	dir_files = os.listdir(data_dir)
	start = 'https://sfbay.craigslist.org/'
	pattern = re.compile('[\W_]+')
	fn = pattern.sub('', start) + '.html'

	# Download if not already downloaded, otherwise pull from cache
	if fn in dir_files and not overwrite:
		print("Loading file: " + fn)
		with open(data_dir + fn, 'r', encoding='utf-8') as f:
			html = f.read()
	else:
		print("Downloading: " + fn)
		print(start)
		res = requests.get(start)
		if res.status_code == 200:
			html = res.text
			with open('test', 'w', encoding='utf-8') as f:
				f.write(html)

		else:
			print("Couldn't grab, error:", res.status_code)

	soup = BeautifulSoup(html, 'lxml')
	state_link = {}

	for element in soup.select('ul.acitem'):
		if 'alabama' in element.text:
			states = element
			tags = states.find_all('a', href=True)
			for t in tags:
				link = 'https:' + t['href']
				state = str(t.text)
				if 'more' in state:
					continue
				state_link[state] = link

	return state_link

def link_city(state, state_dic, overwrite=False):
	'''Given a state, and a dict that links state name to CL link, find all city links'''
	
	# Set initial directory and files info
	data_dir = "data/"
	dir_files = os.listdir(data_dir)
	pattern = re.compile('[\W_]+')

	# Download if not already downloaded, otherwise pull from cache
	link = state_dic[state]
	fn = pattern.sub('', link) + '.html'

	if fn in dir_files and not overwrite:
		print("Loading file: " + fn)
		with open(data_dir + fn, 'r', encoding='utf-8') as f:
			html = f.read()
	else:
		print("Downloading: " + fn)
		res = requests.get(link)
		if res.status_code:
			html = res.text
			html = html
			with open(data_dir+fn, 'w', encoding='utf-8') as f:
				f.write(html)

	city_link = {}

	soup = BeautifulSoup(html, 'lxml')
	
	# Sometimes websites redirect from the geo.craiglist.org page which lists cities
	# for the state to just the direct state page
	try:
		cities = soup.find_all('ul', class_='geo-site-list')
		cities = cities[0].find_all('a', href=True)
		for city in cities:
			c_name = city.text
			c_link = city['href']
			# Sometimes link adds slashes at end
			if c_link[-1] == '/':
				c_link = c_link[:-1]
			# Sometimes link has no http: in front
			if c_link[0] == '/':
				c_link = 'http:' + c_link[:-1]
			city_link[c_name] = c_link
	except:
		print("Webpage for " + state + "redirected. Trying something else.")
		# print(soup)
		cities = soup.find_all('li', class_='expand')

		# If there are no cities in state (https://micronesia.craigslist.org/)
		if len(cities) == 0:
			return {}

		cities = cities[0].find_all('a', href=True)
		for city in cities:
			c_name = city.text
			c_link = 'http:' + city['href']
			# Some links have extra slashes which will cause trouble
			# Sometimes link adds slashes at end
			if c_link[-1] == '/':
				c_link = c_link[:-1]
			# Sometimes link has no http: in front
			if c_link[0] == '/':
				c_link = 'http:' + c_link[:-1]
			city_link[c_name] = c_link

	return city_link

def dict_to_json(overwrite=False):
	state_city_dict = {}

	state_dict = link_state(overwrite=overwrite)
	for state in state_dict:
		cities = link_city(state, state_dict, overwrite=overwrite)
		state_city_dict[state] = cities
	
	# Delete problematic entries in dict
	del state_city_dict['guam']
	del state_city_dict['hawaii']

	with open('state_city_dict.json', 'w', encoding='utf-8') as f:
		json.dump(state_city_dict, f)

# inspect links
def open_dict():
	with open('state_city_dict.json', 'r', encoding='utf-8') as f:
		data = json.load(f)
		for state in data:
			cities = data[state]
			for city in cities:
				print(cities[city])

# dict_to_json(overwrite=False)
# open_dict()