#!/usr/bin/env python
# coding: utf-8

# In[85]:


import bs4
from collections import defaultdict
from pprint import pprint
import glob
import os
import pandas as pd

page_dir = os.path.join('.','ItemPages','html')
pages = glob.glob(os.path.join(page_dir,'*.html'))

df_list = []

# In[126]:

for page in pages:
    print('>>>',page)
    with open(page,'r') as f:
        html = f.read()
    soup = bs4.BeautifulSoup(html,'lxml')

    # Breaks screw up some parsing, and don't think I need them, so just replace
    for br in soup('br'):
        br.replace_with('\n')
    
    # Italics screw up parsing of references, so getting rid of them for now
    for ii in soup('i'):
        ii.replace_with(ii.get_text())


    # ### Remove some tags so it's easier to see the rest

    # In[127]:


    [x.extract() for x in soup.findAll('script')]
    [x.extract() for x in soup.findAll('noscript')]
    [x.extract() for x in soup.findAll('iframe')]
    [x.extract() for x in soup.findAll('svg')]
    [x.extract() for x in soup.findAll('style')]
    [x.extract() for x in soup.select('#nas-footer')]
    [x.extract() for x in soup.select('.nas')]
    [x.extract() for x in soup.select('.artwork__interaction')];



    # ### Set up dictionary to hold data for this page
    # 
    # Using `defaultdict` so can default to a string and append any data that we run across under the same field name, or on separate lines in the accordions

    # In[129]:


    data = defaultdict(str)


    # #### Title

    # In[130]:


    current_key = 'Title'
    data[current_key] += soup.select_one('.artwork__title--text').get_text().strip()


    # #### Date

    # In[131]:


    current_key = 'Date'
    data[current_key] += soup.select_one('.artwork__date time').get_text().strip()


    # #### Name (can be artist or designer...)
    # 
    # If there's a modifier it's in text with newline in between?

    # In[132]:


    current_key = 'Name'
    data[current_key] += soup.select_one('.artwork__artist__name').get_text().strip()


    # #### Artist region

    # In[133]:


    current_key = 'Artist_region'
    data[current_key] += soup.select_one('.artwork__artist__region').get_text().strip()


    # #### Description

    # In[134]:


    current_key = 'Description'
    data[current_key] += soup.select_one('.artwork__intro__desc').get_text().strip()


    # #### Location

    # In[135]:


    current_key = 'Location'
    if soup.select_one('.artwork__location--message'):
        data[current_key] += soup.select_one('.artwork__location--message').get_text().strip()
        data[current_key] += "|"
        data[current_key] += soup.select_one('.artwork__location--gallery').get_text().strip()
    else:
        data[current_key] += soup.select_one('.artwork__location').get_text().strip()


    # #### Object details

    # In[136]:


    for ss in soup.select('.artwork-info .artwork__tombstone--row'):
        label = 'unlabeled'
        value = ''
        if ss.select_one('.artwork__tombstone--label'):
            label = ss.select_one('.artwork__tombstone--label').get_text().rstrip(':')
        if ss.select_one('.artwork__tombstone--value'):
            value = ss.select_one('.artwork__tombstone--value').get_text().strip().replace('\n','|')
        current_key = label
        if data[current_key]: data[current_key] += "|"
        data[current_key] += value
        # print(current_key, ':', data[current_key])

    # #### Component accordions

    # In[137]:


    current_key = 'none'
    def content_breakout(content,current_key):
        for cc in content.children:
            if isinstance(cc, bs4.element.Tag):
                # print('(tag)', cc)
                if cc.name == 'strong':
                    current_key = cc.get_text().strip(':')
                    # print('(strong)', cc.get_text())
                elif cc.name == 'br':
                    # print('break')
                    continue
                elif cc.name == 'a':
                    if data[current_key]: data[current_key] += "|"
                    data[current_key] += cc['href'] + '–' + cc.get_text()
                    # print(cc['href'], '|', cc.get_text())
                elif cc.has_attr('class') and any([xx.endswith('list') for xx in cc['class']]):
                    # print('LIST')
                    content_breakout(cc.p,current_key)
            elif isinstance(cc, bs4.element.NavigableString):
                if len(cc.strip())>0:
                    if data[current_key]: data[current_key] += "|"
                    data[current_key] += cc.strip()
                    # print('(--)', cc.strip())
            else:
                continue
        # print('---------------\n')

    for ss in soup.select('.component__accordions .accordion'):
        title = ss.select_one('.accordion__title').get_text()
        current_key = title
        # print('>>', title)
        content = ss.select_one('.accordion__content')
        content_breakout(content,current_key)


    # #### Related objects

    # In[138]:


    current_key = 'Related_objects'
    for aa in soup.select('a.gtm__relatedartwork:not(:has(> img))'):
        # print(aa['href'].split('/')[-1], ':', aa.get_text())
        if data[current_key]: data[current_key] += "|"
        data[current_key] += aa['href'].split('/')[-1] + '–' + aa.get_text()


    # In[139]:

    # Remove all newline characters before creating DataFrame
    for k,v in data.items():
        data[k] = v.replace('\n',' ')

    # pprint(data)


    # In[ ]:
    df_list.append(pd.DataFrame(data,index=[os.path.basename(page)]))

df_all = pd.concat(df_list)
df_all.to_csv('test_parse.tsv',sep='\t',encoding='utf-8')



