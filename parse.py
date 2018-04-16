from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException,WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
import time
import requests
from bs4 import BeautifulSoup
from config import *
import pymongo

client = pymongo.MongoClient(HORT,PORT)
db = client[DATABASE]
col = db[KEYWORD]
# driver, wait 放在外面，是全局变量，每个函数都会用到
# driver = webdriver.PhantomJS(service_args=SERVICE_ARGS) PhantomJS现在selenium新版本不推荐支持
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
driver = webdriver.Chrome(chrome_options=chrome_options)
# driver.set_window_size(1440,900)
wait = WebDriverWait(driver,10)
def get_total_num(times=0):
    '''
    获取商品一共多少页
    :param times: 默认参数为0
    :return:
    '''
    if times == 3:
        return
    try:
        driver.get('https://www.jd.com/')
        input_tag = wait.until(EC.presence_of_element_located((By.ID,'key')))
        submit_tag = wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'button')))
        input_tag.send_keys(KEYWORD)
        submit_tag.click()

        total_tag = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_bottomPage > span.p-skip > em:nth-child(1) > b')))
        get_detail_info()
        return int(total_tag.text)
    except TimeoutException:
        return get_total_num(times+1)

def next_page(num):
    '''
    单纯的执行翻页操作
    :param num:
    :return:
    '''
    print('第{}页开始爬取'.format(num))
    try:
        input_tag = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_bottomPage > span.p-skip > input')))
        submit_tag = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_bottomPage > span.p-skip > a')))
        input_tag.clear()
        input_tag.send_keys(num)

        submit_tag.click()
        time.sleep(1)
        get_detail_info()
        # 下面这行代码很重要，如果没有，会经常报错，改bug改了4个小时，虽然最后还是不明白！text_to_be_present_in_element,返回值是True或者False。
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#J_bottomPage > span.p-num > a.pn-next > em'),'下一页'))

    except TimeoutException:
        return next_page(num)

def get_detail_info():
    '''
    获取每个卖家商品的信息
    :return:
    '''
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_goodsList > ul')))
    soup = BeautifulSoup(driver.page_source,'lxml')
    titles =[i.get_text() for i in soup.select('#J_goodsList > ul > li > div > div.p-name.p-name-type-2 > a > em')]
    prices =[i.get_text() for i in soup.select('#J_goodsList > ul > li > div > div.p-price > strong > i') ]
    shops = [i.get_text() for i in soup.select('#J_goodsList > ul > li > div > div.p-shop > span > a')]
    for title,price,shop in zip(titles,prices,shops):
        data = {
            'title':title,
            'price':price,
            'shop':shop
        }
        save(data)

def save(dic,times=0):
    '''
    保存到数据库
    :param dic:
    :param times:
    :return:
    '''
    if times == 3:
        return
    try:
        col.insert_one(dic)
    except:
        return save(dic,times+1)


def main():
    print('开始爬取')
    try:
        total_num = get_total_num()
        for num in range(2,total_num+1):
            # print('要跳转的',num)
            next_page(num)
    except WebDriverException:
        return main()
    finally:
        driver.close()
if __name__ == '__main__':
    main()