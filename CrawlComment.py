# -*- coding:utf-8 -*-
"""
@author: Wang Hao
@software: PyCharm
@file: getcooment.py
@time: 2019/3/6 15:47
"""
import time
import os
import re
import time
import datetime
import pymysql
from scrapy.http import HtmlResponse, request
from GetComments.items import GetcommentsItem
from scrapy.spider import Spider
from selenium import webdriver
from selenium.webdriver import ActionChains
from bs4 import BeautifulSoup
#删除文件首行
def deleteFirstRow(file):
    size = os.path.getsize('url.txt')
    if size == 0:
        print("文件删除成功")
        return
    try:
        file = open('url.txt', 'r+')
    except:
        pass
    l4 = file.readlines()
    l4[0] = ''
    file.close()
    file = open('url.txt', 'w+')
    l4 = file.writelines(l4)
    file.close()
#判断阅读更多链接是否存在
def isElementExist(driver):
    flag = True
    browser = driver
    try:
        browser.find_element_by_xpath("//span[@class='RveJvd snByac']")
        return flag
    except:
        flag = False
        return flag
#选择爬取策略 按照时间爬取
def choosePageRule(driver):
    try:
        #展开下拉框
        driver.find_element_by_xpath("//div[@class='jgvuAb Eic1df']").click()
        #找到Newest的位置
        ele = driver.find_element_by_xpath("//div[@class='OA0qNb ncFHed']")
        ActionChains(driver).move_to_element_with_offset(ele, 0, 49.6).click().perform()
    except:
        print("默认评价策略")
    time.sleep(2)
    pass
#判断评论长度
def commentLength(str):
    str1 = str.strip()
    index = 0
    count = 0
    while index < len(str1):
        while str1[index] != " ": # 当不是空格是，下标加1
            index += 1
            if index == len(str1): # 当下标大小跟字符串长度一样时结束当前循环
                break
        count += 1  # 遇到空格加1
        if index == len(str1): # 当下标大小跟字符串长度一样时结束当前循环
            break
        while str1[index] == " ": # 当有两个空格时，下标加1，防止以一个空格算一个单词
            index += 1
    if(count<=5):
        return True
    return False
#加载页面
def loadWebPage(driver):
    flag = 0
    count = 0
    while 1:
        count = count + 1
        # 对于评论太多的设置爬取10000条
        if count >= 250:
            print("窗口滑动250次")
            break;
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            loadMore = driver.find_element_by_xpath("//*[contains(@class,'U26fgb O0WRkf oG5Srb C0oVfc n9lfJ')]").click()
        except:
            time.sleep(1)
            flag = flag + 1
            if flag >= 10:
                print("当前App评论全部获取")
                break
        else:
            flag = 0
#解析网页
def fetchWebPage(driver,url,db,cursor):
    item = GetcommentsItem()
    # app名称
    try:
        item['name'] = driver.find_element_by_xpath("//h1[@class='AHFaub']/span").text
        reviews = driver.find_elements_by_xpath("//*[@jsname='fk8dgd']//div[@class='d15Mdf bAhLNe']")
        print("There are " + str(len(reviews)) + " reviews avaliable")
        print("数据正在写入数据库")
        for review in reviews:
            try:
                soup = BeautifulSoup(review.get_attribute("innerHTML"), "html.parser")
                star = soup.find('div', role='img').get('aria-label').strip("Rated ")[0]
                item['time'] = soup.find(class_="p2TkOb").text
                time_format = datetime.datetime.strptime(item['time'], '%B %d, %Y')
                time_format = time_format.strftime('%Y-%m-%d')
                item['favour'] = soup.find(class_="jUL89d y92BAb").text
                try:
                    favour = int(item['favour'])
                except:
                    favour = 0
                comment = soup.find('span', jsname='fbQN7e').text
                if not comment:
                    comment = soup.find('span', jsname='bN97Pc').text
                if(commentLength(comment)):
                    #评论过短不需要
                    pass
                else:
                    item['comments'] = comment
                    #数据入库
                    try:
                        # 避免插入重复数据
                        cursor.execute('insert ignore into comment(name,time,star,comment,favour) values(%s,%s,%s,%s,%s)',(item['name'], time_format,star,item['comments'],favour))
                        db.commit()
                    except:
                        print("数据库插入出错")
                        db.rollback()
            except:
                print("评论信息出错")
    except:
        print("网页错误")
        pass

class GetComment(Spider):
    name = "comment"
    # 打开数据库
    try:
        db = pymysql.connect(host="localhost", user="root", password="wanghao0116", db="scrapy", port=3306)
        cursor = db.cursor()
        print("数据库打开成功")
    except:
        print("数据库打开失败")
        print("正在退出程序")
        exit(0)
    driver = webdriver.Firefox()
    print("正在爬取网页信息")
    f  = open('url.txt', 'r+')
    line = f.readline()
    num = 1
    while line:
        size = os.path.getsize('url.txt')
        if size == 0:
             break;
        print("爬取app数目：" + str(num))
        try:
            f = open('url.txt', 'r+')
        except:
            pass
        u = line
        deleteFirstRow(f)
        driver.get(u)
        #评价策略默认
        #choosePageRule(driver)
        loadWebPage(driver)
        time.sleep(2)
        fetchWebPage(driver,u,db,cursor)
        line = f.readline()
        num = num+1
    print("程序任务结束")
    driver.close()