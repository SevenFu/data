import time
import requests
import json
import random
from selenium import webdriver
from fake_useragent import UserAgent
from jsonpath import jsonpath


def login():
    cookies_dict = {}
    driver_obj = webdriver.Chrome()
    driver_obj.get('https://www.zhihu.com/')
    driver_obj.implicitly_wait(3)
    driver_obj.find_element_by_xpath(".//*[@class='SignContainer-switch']/span").click()
    driver_obj.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div/div[2]/div[1]/form/div[5]/span[5]/button').click()
    driver_obj.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div/div[2]/div[1]/form/div[5]/span[5]/span/button[3]').click()  # click QQ
    print('scan the QQ code please !')
    time.sleep(10)
    print('login successful !')

    def GetCookies():
        driver_obj.get('https://www.zhihu.com/')
        cookies_list = driver_obj.get_cookies()  # return class of list
        print(cookies_list,type(cookies_list))
        for cookies in cookies_list:
            cookies_dict[cookies['name']] = cookies['value']
        cookies_json = json.dumps(cookies_dict, ensure_ascii=False)  # cookies transform json type
        with open("zhihucookies.json", "w+") as f:  # read and write
            f.write(cookies_json)
        print('cookies data saved !')
    return GetCookies


def GetHash():
    try:
        hash_str = "1234567890abcdef"
        hash_id_ls = []
        for i in range(0, 32):
            hash_id_ls.append(random.choice(hash_str))  # Randomly generated 32 str
        hash_id = ''.join(hash_id_ls)

        def GetData(query, pages):
            UA = UserAgent(use_cache_server=False)
            headers = {"User-Agent": UA.random}
            with open("zhihucookies.json", "r") as f:  # only read of way
                data = f.read()
                cookies = json.loads(data)
            url_api = "https://www.zhihu.com/api/v4/search_v3?"
            for offset in range(5, pages, 10):  # 5 15 25 35 ...
                params = {
                          "t": "general",
                          "q": query,
                          "correction": "1",
                          "offset": offset,
                          "limit": "10",
                          "show_all_topics": "0",
                          "search_hash_id": hash_id
                         }
                try:
                    r = requests.get(url_api, headers=headers, cookies=cookies, params=params)
                    r.encoding = "utf-8"
                    print(r.status_code)
                    cont = r.json()  # return dict type data
                    info_list = jsonpath(cont, "$..highlight")
                    for info_item in info_list:
                        print(info_item)
                except Exception as e:
                    print(e)
        return GetData
    except Exception as e:
        print(e)


def main():
    fun = login()
    fun()
    fun1 = GetHash()
    fun1("旅游", 100)


if __name__ == '__main__':
    main()

