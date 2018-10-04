import requests
import json
import os
import re
from bs4 import BeautifulSoup
from time import sleep

data_dir = 'data/'
dir_files = os.listdir(data_dir)

with open('state_city_dict.json', 'r', encoding='utf-8') as f:
	state_city_dict = json.load(f)

def make_dirs():
	# Initialize directorys and subdirectories for data storage
	pattern = re.compile('[\W_]+')
	for state in state_city_dict:
		cities = state_city_dict[state]
		state = state.replace(' ', '')
		for city in cities:
			city = city.replace(' ', '')
			city = pattern.sub('', city)
			path = data_dir + state + '/' + city + '/'
			if not os.path.exists(os.path.dirname(path)):
				os.makedirs(os.path.dirname(path))

def load_link(search_link, state, city):
	'''Give this a CL search link, state and city name, will
	download and return html text, or load if already in cache'''
	pattern = re.compile('[\W_]+')
	fn = pattern.sub('', search_link) + '.html'
	
	state = state.replace(' ', '')
	city = city.replace(' ', '')
	city = pattern.sub('', city)
	dir_path = data_dir + state + '/' + city + '/'
	dir_list = os.listdir(dir_path)

	if fn in dir_list:
		print('Loading html for: ' + fn)
		with open(dir_path + fn, 'r', encoding='utf-8') as f:
			html = f.read()
	else:
		print('Downloading html for: ' + fn)
		print(search_link)

		# Catching some buggy links
		if search_link == '//newyork.craigslist.org/fct//search/sso?sort=rel&bundleDuplicates=1&auto_make_model=prius&min_price=1000':
			return ''

		res = requests.get(search_link)
		if res.status_code == 200:
			html = res.text
			with open(dir_path + fn, 'w', encoding='utf-8') as f:
				f.write(html)
		else:
			html = ''
			print('Error in downloading ' + search_link)
	return html

def return_totalcounts(html):
	# Find # items, we only need to generate new pages to scrape if
	# page counts is more than 120. This module does double duty and also
	# chops up html if search yields nothing or has exlusions
	exclude = 'Few local results found. Here are some from nearby areas.'
	nothing = 'Nothing found for that search.'

	if not html:
		totalitems = 0
		return html, totalitems
	if nothing in html:
		totalitems = 0
		print('No items found in search')
		html = ''
	elif exclude in html:
		# If there are too few results, exclude the suggested nearby items
		# (limit to our area of interest)
		e_indx = (html.find(exclude))
		html = html[:e_indx-45]
		totalitems = 0
		print('Too few results')
	else:
		items = BeautifulSoup(html, 'lxml')
		items = items.find_all('span', class_='totalcount')
		# Something's wrong if there are no item totalcounts on webpage
		if not len(items) >= 1:
			print("Total count doesn't exist on page")
			totalitems = 0
			return html, totalitems
		totalitems = int(items[0].text)
	return html, totalitems

def find_item_links(html):
	item_links = []		
	soup = BeautifulSoup(html, 'lxml')

	# CL will group duplicates and nest them/hide them away, so we have to remove
	duplicates = soup.find_all('ul', class_='duplicate-rows')
	for d in duplicates:
		d.decompose()
	soup = soup.find_all('li', class_='result-row')

	for s in soup:
		link = s.find_all('a', href=True, class_='result-image')
		link = link[0]['href']
		item_links.append(link)
	return item_links

def get_state_searches(state, sso=True):
	'''Given a state, we will download searches for each of the city in the state'''

	# sso means sale by owner search, else search for sale by dealer
	if sso:
		search_params = 'search/sso?sort=rel&bundleDuplicates=1&auto_make_model=prius&min_price=1000'
	else:
		search_params = 'search/ssq?sort=rel&bundleDuplicates=1&auto_make_model=prius&min_price=1000'
	
	state_cities = state_city_dict[state]
	cars_links = {}

	for city in state_cities:
		link = state_cities[city]
		link += '/' + search_params
		html = load_link(link, state, city)
		html, totalitems = return_totalcounts(html)

		next_page = []
		# If there's more than 1 search page, lets create a list of additional pages to scrape
		for i in range(120, totalitems, 120):
			page = link + '&s=' + str(i)
			next_page.append(page)

		links_in_city = []
		# Save our current page's results
		links_in_city += find_item_links(html)

		for link in next_page:
			html = load_link(link, state, city)
			links_in_city += find_item_links(html)

		cars_links[city] = links_in_city

	# Lets cache it to file
	state = state.replace(' ', '')
	print('Dumping ' + state + ' cars_links.json to file')
	with open(data_dir + state + '/' +\
		'cars_links.json', 'w', encoding='utf-8') as f:
		json.dump(cars_links, f)


def get_car_info(state):
	global subtotal
	pattern = re.compile('[\W_]+')
	state = state.replace(' ', '')
	fn = 'cars_links.json'
	fp = data_dir + state + '/' + fn
	
	with open(fp, 'r') as f:
		state_car_links = json.load(f)
	
	# Counter for VPN break time
	counter = 0
	data_count = 0

	for city in state_car_links:
		print('Looking at search data for ' + city + ', ' + state)
		links = state_car_links[city]
		city = city.replace(' ', '')
		city = pattern.sub('', city)
		dir_path = data_dir + state + '/' + city + '/'
		dir_content = os.listdir(dir_path)

		# Start with last link, then pop out of links list
		while links:
			link = links[-1]
			links.pop()
			data_count += 1
			save_name = pattern.sub('', link)[:-4] + '.html'

			# If we've already cached file, then read cache, dl otherwise
			if save_name in dir_content:
				subtotal += 1
				print('Loading ' + link)
				with open(dir_path + save_name, 'r', encoding='utf-8') as f:
					html = f.read()
			else:
				print(counter, 'Downloading ' + link)
				# Sleep here so we can switch VPNs
				if counter/700 == 1:
					print('SWITCH VPNS NOW!!')
					sleep(10)
					counter = 0

				res = requests.get(link)
				if res.status_code == 200:
					html = res.text
					with open(dir_path + save_name, 'w', encoding='utf-8') as f:
						f.write(html)
					counter += 1
				else:
					print('Cannot download search for ' + link)
					continue
	print('Total data for ' + state + ' : ' + str(data_count))

subtotal = 0
for state in state_city_dict:
	print('GETTING READY TO SCRAPE FOR ' + state)
	get_state_searches(state)
	get_car_info(state)
	print('Subtotal CL listings in US: ', subtotal)