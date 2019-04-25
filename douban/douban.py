import requests
import queue
import threading
import time
import random
import json
from lxml import etree


q = queue.Queue()
Q = queue.Queue()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'}
base_url_list = ["https://movie.douban.com/j/search_subjects?type=movie&tag=%E8%B1%86%E7%93%A3%E9%AB%98%E5%88%86&sort=recommend&page_limit=20&page_start={}".format(i) for i in range(0,40,20)]
for item_url in base_url_list:
    print(item_url)
    q.put(item_url)


def GetHtml(url, xpath):
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.encoding = 'utf-8'
        html = r.text
        content = etree.HTML(html)
        target_date_list = content.xpath(xpath)

        return target_date_list
    except:
        return ""


def FetchUrl():
    while 1:
        if not q.empty():
            child_url = q.get()
            try:
                time.sleep(random.random())
                r = requests.get(child_url, headers=headers, timeout=30)
                r.encoding = 'utf-8'
                html = r.text
                print(html)
                text_dict = json.loads(html)
                text_list = text_dict["subjects"]
                count = 1
                for list_item in text_list:
                    url = list_item["url"]
                    Q.put(url)
                    if not Q.empty():

                        target_url = Q.get()
                        print(
                            "----------------------------------正在爬取第{}部电影信息----------------------------------".format(count))
                        time.sleep(0.5)
                        title_list = GetHtml(target_url, "//div[@id='content']/h1/span[1]/text()")
                        print('title is ------------------------------>', title_list)
                        actors_list = GetHtml(target_url,
                                              "//div[@id='info']/span[@class='actor']/span[@class='attrs']/a/text()")
                        print("actors are ---------------------------->", actors_list)
                        type1_list = GetHtml(target_url, "//div[@id='info']/span[5]/text()")
                        type2_list = GetHtml(target_url, "//div[@id='info']/span[6]/text()")
                        type_list = [type1_list[0] + "/" + type2_list[0]]
                        show_info1_list = GetHtml(target_url, "//div[@id='info']/span[11]/text()")
                        show_info2_list = GetHtml(target_url, "//div[@id='info']/span[12]/text()")
                        show_info_list = [show_info1_list[0] + "/" + show_info2_list[0]]
                        running_time_list = GetHtml(target_url, "//div[@id='info']/span[14]/text()")
                        coment_score_list = GetHtml(target_url, "//strong[@class='ll rating_num']/text()")

                        count += 1

                    elif Q.empty():
                        break
            except Exception as e:
                print(e)
        elif q.empty():
            break

def main():
    FetchUrl()


if __name__  == '__main__':
    main()



# def FetchData():
#
#     while 1:
#         count = 1
#         if not Q.empty():
#             try:
#                 target_url = Q.get()
#                 print("----------------------------------正在爬取第{}部电影信息----------------------------------".format(count))
#                 time.sleep(0.5)
#                 title_list = GetHtml(target_url, "//div[@id='content']/h1/span[1]/text()")
#                 print('title is ------------------------------>', title_list)
#                 actors_list = GetHtml(target_url, "//div[@id='info']/span[@class='actor']/span[@class='attrs']/a/text()")
#                 print("actors are ---------------------------->", actors_list)
#                 type1_list = GetHtml(target_url, "//div[@id='info']/span[5]/text()")
#                 type2_list = GetHtml(target_url, "//div[@id='info']/span[6]/text()")
#                 type_list = [type1_list[0] + "/" + type2_list[0]]
#                 show_info1_list = GetHtml(target_url, "//div[@id='info']/span[11]/text()")
#                 show_info2_list = GetHtml(target_url, "//div[@id='info']/span[12]/text()")
#                 show_info_list = [show_info1_list[0] + "/" + show_info2_list[0]]
#                 running_time_list = GetHtml(target_url, "//div[@id='info']/span[14]/text()")
#                 coment_score_list = GetHtml(target_url, "//strong[@class='ll rating_num']/text()")
#
#                 count += 1
#             except Exception as e:
#                 print(e)
#         elif Q.empty():
#             break


#
# def Run():
#     init = time.time()
#     threads_list = []
#     thread_num = 3
#     for i in range(0,thread_num):
#         t = threading.Thread(target=FetchUrl)
#         threads_list.append(t)
#     for t in threads_list:
#         t.start()
#     for t in threads_list:
#         t.join()
#     end = time.time()
#     print("RunFetchUrl used time is %s"%(end-init))