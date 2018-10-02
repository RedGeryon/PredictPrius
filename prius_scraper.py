import pickle
import requests
import os
import re
from bs4 import BeautifulSoup

data_dir = "data/"
dir_files = os.listdir(data_dir)

with open('state_city_dict.pickle', 'rb') as f:
	state_city_dict = pickle.load(f)

def make_dirs():
	# Initialize directorys and subdirectories for data storage
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
	
	res = requests.get(search_link)
	if res.status_code == 200:
		state = state.replace(' ', '')
		city = city.replace(' ', '')
		city = pattern.sub('', city)
		
		dir_path = data_dir + state + '/' + city + '/'
		dir_list = os.listdir(dir_path)

		if fn in dir_list:
			print('Loading html for: ' + fn)
			with open(dir_path + fn, 'r') as f:
				html = f.read()
		else:
			print('Downloading html for: ' + fn)
			html = res.text
			html = html.encode('utf-8')
			with open(dir_path + fn, 'w') as f:
				f.write(html)
	return html

def return_totalcounts(html):
	# Find # items, we only need to generate new pages to scrape if
	# page counts is more than 120. This module does double duty and also
	# chops up html if search yields nothing or has exlusions
	exclude = "Few local results found. Here are some from nearby areas."
	nothing = "Nothing found for that search."

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
		print("Too few results")
	else:
		items = BeautifulSoup(html, 'lxml')
		items = items.find_all('span', class_='totalcount')
		# Something's wrong if there are no item totalcounts on webpage
		if not len(items) >= 1:
			print("Total count doesn't exist on page")
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

# # Set some initial params for testing
# mystate = 'california'
# mycity = 'SF bay area'
# ca_cities = state_city_dict[mystate]
# sf = ca_cities[mycity]
# link = sf + '/' + search_params
# html = load_link(link, mystate, mycity)
# html, totalitems = return_totalcounts(html)

def get_state_searches(state, sso=True):
	'''Given a state, we will download searches for each of the city in the state'''

	# sso means sale by owner search, else search for sale by dealer
	if sso:
		search_params = 'search/sso?sort=rel&bundleDuplicates=1&auto_make_model=prius&min_price=1000'
	else:
		search_params = 'search/ssq?sort=rel&bundleDuplicates=1&auto_make_model=prius&min_price=1000'
	
	state_cities = state_city_dict[state]
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

get_state_searches('california')