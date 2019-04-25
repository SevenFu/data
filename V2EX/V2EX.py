import re
import time
import requests
from lxml import etree
from bs4 import BeautifulSoup


headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"}


def GetLoginData():
    login_ls = []
    init_url = "https://www.v2ex.com/signin"
    r = requests.get(init_url, headers=headers, timeout=30)
    r.encoding = "utf-8"
    html = r.text

    soup = BeautifulSoup(html, "html.parser")
    input_ls = soup.find_all("input")
    new_input_ls = input_ls[1:5]
    for input_item in new_input_ls[:-1]:
        info_items = input_item.attrs['name']
        login_ls.append(info_items)
    info_once = new_input_ls[-1].attrs['value']
    login_ls.append(info_once)
    return login_ls


def GetSession(captche, page):
    info_ls = []
    login_ls = GetLoginData()
    data = {
            login_ls[0]: "zhu31",
            login_ls[1]: "vzhan123",
            login_ls[2]: captche,
            "once": login_ls[3]
           }
    s = requests.Session()
    s.get("https://www.v2ex.com/signin", headers=headers, data=data)
    url_list = ["https://www.v2ex.com/go/linux?p={}".format(i) for i in range(1, page)]

    for url in url_list:
        response = s.get(url, headers=headers)
        html = response.text
        cont = etree.HTML(html)
        info_url = cont.xpath("//table/tr/td[3]/span[@class='item_title']/a/@href")
        info_ls.extend(info_url)  # info urls we could need data

    def GetData():
        count = 1
        r = s.get("https://www.v2ex.com/t/496068#reply16", headers=headers)
        for item_url in info_ls:
            print('------------------------------->fetching the {} data---------------------------------'.format(count))
            time.sleep(0.5)
            target_url = "https://www.v2ex.com" + item_url
            r = s.get(target_url, headers=headers)
            r.encoding = "utf-8"
            htmls = r.text
            title_ls = re.findall(r'<h1>(.*?)</h1>', htmls, re.S)
            title = ''.join(title_ls)
            body_ls = re.findall(r'<div class="markdown_body">(.*?)</div>', htmls, re.S)
            body = ''.join(body_ls)
            dic_item = {title: {body: target_url}}
            print(dic_item)
            count += 1
    return GetData


if __name__ == '__main__':
    fun = GetSession("HQSUSN", 70)  # first argument just open login page input it second is page
    fun()
