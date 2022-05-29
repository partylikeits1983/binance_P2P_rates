import requests
import urllib.request
import time
from bs4 import BeautifulSoup
from selenium import webdriver

from time import time, sleep
from csv import writer


def scraperBUY():
    driver = webdriver.Chrome()
    driver.get('https://p2p.binance.com/en/trade/sell/USDT?fiat=RUB&payment=ALL')

    sleep(15) 

    prices = driver.find_elements_by_xpath("//div[@class='css-1m1f8hn']")

    for i in prices:
        print(i.text)
        a1.append(i.text)

    driver.close()
    
    
def scraperSELL():
    driver = webdriver.Chrome()
    driver.get('https://p2p.binance.com/en/trade/all-payments/USDT?fiat=RUB')

    sleep(15) 

    prices = driver.find_elements_by_xpath("//div[@class='css-1m1f8hn']")

    for i in prices:
        print(i.text)
        a2.append(i.text)

    driver.close()
    
    
def cbrates():
    data = requests.get(url="https://www.cbr-xml-daily.ru/daily_json.js").json()
    cbrate = float(data["Valute"]["USD"]["Value"])
    return cbrate
    
    
def clean(a1,a2):
    ratesBUY = []
    ratesSELL= []
    
    for i in a1:
        if i == '':
            break
        else:
            num = float(i)
            ratesBUY.append(num)
            
    for i in a2:
        if i == '':
            break
        else:
            num = float(i)
            ratesSELL.append(num)
                  
    rateBUY = sum(ratesBUY)/len(ratesBUY)
    rateSELL= sum(ratesSELL)/len(ratesSELL)
    
    rateBUY = round(rateBUY, 2)
    rateSELL= round(rateSELL, 2)
    
    return (rateBUY, rateSELL)



def append_list_as_row(file_name, list_of_elem):
    with open(file_name, 'a+', newline='') as write_obj:
        
        csv_writer = writer(write_obj)
        csv_writer.writerow(list_of_elem)


def handler():
    
    global a1
    a1 = []
    global a2
    a2 = []
    
    scraperBUY()
    scraperSELL()
    
    global rateBUY
    global rateSELL
    global cbrate
    
    rateBUY, rateSELL = clean(a1,a2)
    
    cbrate = cbrates()
    
    with open("rateBUY.txt", "w") as text_file:
        text_file.write(str(rateBUY))
        
    with open("rateSELL.txt", "w") as text_file:
        text_file.write(str(rateSELL))
        
    with open("cbrate.txt", "w") as text_file:
        text_file.write(str(cbrate))
        
    vals = [rateBUY,rateSELL,cbrate]
    append_list_as_row('values.csv', vals)
    
    
    
while True:
    handler()
    sleep(30 - time() % 30)