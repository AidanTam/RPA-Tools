# coding: utf-8

# pip install requests==2.26.0 bs4=0.0.1
import requests
from bs4 import BeautifulSoup


def get_hot_from_baidu():
    url_hot = 'http://top.baidu.com/buzz.php?p=top10'

    response = requests.get(url=url_hot).content.decode('gbk')

    soup = BeautifulSoup(response, 'html.parser')

    tag_table = soup.find('table', {'class': 'list-table'})

    tag_tr = tag_table.find_all('td', {'class': 'keyword'})

    result = []
    for i in tag_tr:
        text_list = i.get_text().strip().split('\n')
        for text in text_list:
            if 'search' not in text:
                result.append(text)

    return result
