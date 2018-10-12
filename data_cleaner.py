from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import json
import csv
import re

data_dir = 'data/'

# Return list of state, city, html filename
def query_car_searches(sso=True):
	entries = []
	pattern = re.compile('[\W_]+')
	# fn = pattern.sub('', search_link) + '.html'

	with open('state_city_dict.json', 'r', encoding='utf-8') as f:
		state_city_dict = json.load(f)

	for state in state_city_dict:
		# Flatten state names
		state = pattern.sub('', state)

		# Get the html file names per state (dict contains results
		# from all cities in state)
		if sso:
			cars_links_fn = 'cars_links_sso.json'
		else:
			cars_links_fn = 'cars_links_ssq.json'
		with open(data_dir + state + '/' +\
			cars_links_fn, 'r', encoding='utf-8') as f:
			search_data = json.load(f)
		for city in search_data:
			c_name = pattern.sub('', city)
			links = search_data[city]
			links = map(lambda l: pattern.sub('', l)[:-4] + '.html', links)
			if links:
				links = list(map(lambda l: (state, c_name, l), links))
			entries += links
	return entries

def parse_attributes(search_entry, sso=True):
	'''Var search entry is a list containing tuples of (state, city, car url).
	The output is all of the scraped info from the cached url'''
	expired = 0
	errors = 0
	features = ['name', 'sso', 'condition', 'price', 'state', 'city',\
				'odometer', 'paint color', 'size', 'title status',\
				'type', 'nthumbs', 'postlen', 'year']
	all_data = []
	pattern = re.compile('[\W_]+')

	for url in search_entry:
		state = url[0]
		city = url[1]
		fn = url[2]
		fp = data_dir + state + '/' + city + '/' + fn

		try:
			with open(fp, 'r', encoding='utf-8') as f:
				html = f.read()
		except:
			errors += 1
			print('Error with: ', state, city, fn)
			continue

		soup = BeautifulSoup(html,'lxml')

		# Grab attributes
		attributes = soup.find_all('p', class_='attrgroup')

		# If there are no attributes, link has probably expired
		if len(attributes) < 2:
			print(expired, url[2], 'expired')
			expired += 1
			continue

		# Grab price
		price = soup.find('span', class_='price').text
		price = pattern.sub('', price)

		name = attributes[0].findChildren('span', recursive = False)
		name = name[0].text
		details = attributes[1].findChildren('span', recursive = False)
		details = list(map(lambda attr: str(attr.text).split(': '), details))
		if ['cryptocurrency ok'] in details:
			details.remove(['cryptocurrency ok'])
			details.append(['cryptocurrency', '1'])
		try:
			details = dict(details)
		except:
			print('Check error first to see if fixable, skip page')
			print(details)
			errors += 1
			continue

		# Grab how many images are provided via thumbnails
		thumbs = soup.find_all('a', class_='thumb')
		num_thumbs = len(thumbs)

		# Grab number of characters in the description
		# Strip spaces, newlines, and tabs
		posting = soup.find('section', {'id' : 'postingbody'}).text
		posting = posting.strip().replace(' ', '').replace('\t', '').replace('\n', '')
		post_len = len(posting)

		# Add these additional data to our details then append
		details['nthumbs'] = num_thumbs
		details['postlen'] = post_len
		details['name'] = name[5:]
		details['year'] = name[:4]
		details['sso'] = 1 if sso else 0
		details['price'] = price
		details['state'] = state
		details['city'] = city

		if 'État du titre' in details:
			details['title status'] = details['État du titre']

		# Write out to rows of data so we can  save
		temp_arr = []
		for f in features:
			try:
				data = details[f]
			except:
				if f == 'condition' or f == 'paint color' or f == 'title status' or f == 'type':
					data = 'unknown'
				else:
					data = 'None'
			temp_arr.append(data)
		all_data.append(temp_arr)

	print('Entries: ' + str(expired) + '/' + str(len(search_entry)) + ' has expired.' )
	print('and ' + str(errors) + ' unknown error')

	save_name = 'all_data_sso.csv' if sso else 'all_data_ssq.csv'
	with open(data_dir + save_name, 'w', encoding='utf-8') as f:
		writer = csv.writer(f, delimiter=',')
		writer.writerow(features)
		writer.writerows(all_data)

# Parse through all sso records (sale by owner)
search_entry = query_car_searches(sso=False)
parse_attributes(search_entry, sso=False)
# Parse through all ssq records (sale by dealer)
search_entry = query_car_searches(sso=True)
parse_attributes(search_entry, sso=True)