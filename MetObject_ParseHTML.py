#!/usr/bin/env python
# coding: utf-8

import bs4
from collections import defaultdict
from pprint import pprint
import glob
import os
import pandas as pd
import tarfile

page_dir = os.path.join('.','html')
input_file = 'test_html.tar.gz'
output_file = 'test_parse_tgz.tsv'

df_list = []

with tarfile.open(os.path.join(page_dir,input_file), "r:gz") as tar:
    for tarinfo in tar:
        page = tarinfo.name
        if page.startswith('.'):
            continue
        print('>>>',page)
        with tar.extractfile(page) as f:
            html = f.read()
        soup = bs4.BeautifulSoup(html,'lxml')

        # Breaks screw up some parsing, and don't think I need them, so just replace
        for br in soup('br'):
            br.replace_with('\n')
    
        # Italics screw up parsing of references, so getting rid of them for now
        for ii in soup('i'):
            ii.replace_with(ii.get_text())

        # ### Remove some tags so it's easier to see the rest
        [x.extract() for x in soup.findAll('script')]
        [x.extract() for x in soup.findAll('noscript')]
        [x.extract() for x in soup.findAll('iframe')]
        [x.extract() for x in soup.findAll('svg')]
        [x.extract() for x in soup.findAll('style')]
        [x.extract() for x in soup.select('#nas-footer')]
        [x.extract() for x in soup.select('.nas')]
        [x.extract() for x in soup.select('.artwork__interaction')];

        # ### Set up dictionary to hold data for this page
        # Using `defaultdict` so can default to a string 
        # and append any data that we run across under the same field name, 
        # or on separate lines in the accordions
        data = defaultdict(str)

        # #### Title
        current_key = 'Title'
        data[current_key] += soup.select_one('.artwork__title--text').get_text().strip()

        # #### Date
        current_key = 'Date'
        data[current_key] += soup.select_one('.artwork__date time').get_text().strip()

        # #### Name (can be artist or designer...)
        # If there's a modifier it's in text with newline in between?
        current_key = 'Name'
        data[current_key] += soup.select_one('.artwork__artist__name').get_text().strip()

        # #### Artist region
        current_key = 'Artist_region'
        data[current_key] += soup.select_one('.artwork__artist__region').get_text().strip()

        # #### Description
        current_key = 'Description'
        data[current_key] += soup.select_one('.artwork__intro__desc').get_text().strip()

        # #### Location
        current_key = 'Location'
        if soup.select_one('.artwork__location--message'):
            data[current_key] += soup.select_one('.artwork__location--message').get_text().strip()
            data[current_key] += "|"
            data[current_key] += soup.select_one('.artwork__location--gallery').get_text().strip()
        else:
            data[current_key] += soup.select_one('.artwork__location').get_text().strip()

        # #### Object details
        for ss in soup.select('.artwork-info .artwork__tombstone--row'):
            label = 'unlabeled'
            value = ''
            if ss.select_one('.artwork__tombstone--label'):
                label = ss.select_one('.artwork__tombstone--label').get_text().rstrip(':')
            if ss.select_one('.artwork__tombstone--value'):
                value = ss.select_one('.artwork__tombstone--value').get_text().strip().replace('\n','|')
            current_key = label
            # There is often repetition between this section and earlier page displays
            if not (value == data[current_key]):
                if data[current_key]: data[current_key] += "|"
                data[current_key] += value
                # print(current_key, ':', data[current_key])

        # #### Component accordions
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
        current_key = 'Related_objects'
        for aa in soup.select('a.gtm__relatedartwork:not(:has(> img))'):
            # print(aa['href'].split('/')[-1], ':', aa.get_text())
            if data[current_key]: data[current_key] += "|"
            data[current_key] += aa['href'].split('/')[-1] + '–' + aa.get_text()

        # Remove all newline characters before creating DataFrame
        for k,v in data.items():
            data[k] = v.replace('\x0D\x0A', ' ').replace('\x0A',' ').replace('\x0D',' ')

        # pprint(data)

        df_list.append(pd.DataFrame(data,index=[os.path.basename(page)]))

df_all = pd.concat(df_list)
df_all.to_csv(output_file, sep='\t', encoding='utf-8')



