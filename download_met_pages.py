from selenium import webdriver
# This part loads the path for the chrome driver binary
import chromedriver_binary
from selenium.webdriver.chrome.options import Options
import os
import time
import random
import json
import tarfile
import io

json_dir = '.'
json_file_name = 'MetAPI_Dept13_Qstar.json'
tar_file_name = 'MetWeb_Dept13.tar'

# Department 11 is European Paintings – 2288 items
# Department 15 is The Robert Lehman Collection - 2268 items
# European Sculpture and Decorative Arts: dept 12: 31731
# Medieval Art: dept 17: 6842
# Greek and Roman Art: dept 13: 29624
# Arts of Africa, Oceania, and the Americas: dept 5: 6254

# Trying to add files directly to tar archive so don't end up with thousands
# of individual files in directory, and easier to transfer
# https://stackoverflow.com/a/52724508

with open(os.path.join(json_dir, json_file_name),'r') as f:
    items_json = json.load(f)

item_count = items_json['total']
item_list = items_json['objectIDs']

chrome_options = Options()
chrome_options.add_argument("--headless")

ff = webdriver.Chrome(options=chrome_options)

with tarfile.TarFile(tar_file_name, 'a') as tar:
    tar_mem = tar.getmembers()
    if len(tar_mem) > 0:
        tar_list = [x.name for x in tar.getmembers()]
    else:
        tar_list = []
    for ii,item in enumerate(item_list):
        print(ii, '/', item_count, ':', item)
        # Check if file has already been downloaded
        page_name = str(item)+'.html'
        if not page_name in tar_list:
            # 152 minutes for 4s avg between calls
            time.sleep(1+2*random.random())
            ff.get('https://www.metmuseum.org/art/collection/search/' + str(item))
            data = ff.page_source.encode('utf-8')
            info = tarfile.TarInfo(name=page_name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
