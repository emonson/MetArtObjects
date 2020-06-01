from selenium import webdriver
# This part loads the path for the chrome driver binary
import chromedriver_binary
from selenium.webdriver.chrome.options import Options
import os
import time
import random
import json

json_dir = '.'
# Department 11 is European Paintings – 2288 items
json_file_name = 'MetAPI_Dept15_Qstar.json'

# https://collectionapi.metmuseum.org/public/collection/v1/search?isOnView=true&departmentId=6&q=provenance
# item_list = [38212,38634,49544,49543,49545,65556,39126,38237,38452,75201,37404]

with open(os.path.join(json_dir, json_file_name),'r') as f:
    items_json = json.load(f)

item_count = items_json['total']
item_list = items_json['objectIDs']

chrome_options = Options()
chrome_options.add_argument("--headless")

ff = webdriver.Chrome(options=chrome_options)

for ii,item in enumerate(item_list):
    print(ii, '/', item_count, ':', item)
    if not os.path.exists(os.path.join('html', str(item)+'.html')):
        # 152 minutes for 4s avg between calls
        time.sleep(2+4*random.random())
        ff.get('https://www.metmuseum.org/art/collection/search/' + str(item))
        with open(os.path.join('html', str(item)+'.html'), 'w', encoding='utf-8') as f:
            f.write(ff.page_source)
