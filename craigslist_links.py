import requests
import os
from bs4 import BeautifulSoup
import re
import pickle

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
		with open(data_dir + fn, 'rb') as f:
			html = f.read()
	else:
		print("Downloading: " + fn)
		res = requests.get(start)
		if res.status_code == 200:
			html = res.text
			html = html.encode('utf-8')
			with open(data_dir+fn, 'wb') as f:
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
		with open(data_dir + fn, 'rb') as f:
			html = f.read()
	else:
		print("Downloading: " + fn)
		res = requests.get(link)
		if res.status_code:
			html = res.text
			html = html.encode('utf-8')
			with open(data_dir+fn, 'wb') as f:
				f.write(html)

	city_link = {}

	soup = BeautifulSoup(html, 'lxml')
	
	# Sometimes websites redirect from the geo.craiglist.org page which lists cities
	# for the state to just the direct state page
	try:
		cities = soup.find_all('ul', class_='geo-site-list')
		cities = cities[0].find_all('a', href=True)
		for city in cities:
			c_name = city.text.encode('utf-8')
			c_link = city['href']
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
			c_name = city.text.encode('utf-8')
			c_link = 'http:' + city['href']
			city_link[c_name] = c_link

	return city_link

def pickle_dic(overwrite=False):
	state_city_dict = {}

	state_dict = link_state(overwrite=overwrite)
	for state in state_dict:
		cities = link_city(state, state_dict, overwrite=overwrite)
		state_city_dict[state] = cities

	with open('state_city_dict.pickle', 'wb') as f:
		pickle.dump(state_city_dict, f,  protocol=pickle.HIGHEST_PROTOCOL)

pickle_dic()