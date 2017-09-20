import os
from time import sleep, time

import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests import Session
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium import webdriver


class DegiroAPI(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def login(self):
        self.session = Session()


base = os.path.dirname(os.path.realpath(__file__))
load_dotenv(os.path.join(base, '.env'))
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")

options = webdriver.ChromeOptions()
# options.add_argument('headless')
driver = webdriver.Chrome(os.path.join(base, 'chromedriver'), chrome_options=options)
driver.get("https://trader.degiro.nl/login/uk?#/login")
username = WebDriverWait(driver, 20).until(expected_conditions.presence_of_element_located((By.ID, 'username')))
password = WebDriverWait(driver, 20).until(expected_conditions.presence_of_element_located((By.ID, 'password')))

username.send_keys(USERNAME)
password.send_keys(PASSWORD)

logging.info("Logging in user {}".format(USERNAME))
login = driver.find_element_by_name('loginButtonUniversal').click()

WebDriverWait(driver, 20).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'wrapper')))
logging.info("Navigating to favourites page")

driver.get("https://trader.degiro.nl/trader/#!/favourites")

WebDriverWait(driver, 20).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'favourites')))
# TODO: change to 100
while True:

    last_page = False
    while not last_page:
        page = driver.page_source

        soup = BeautifulSoup(page)
        stock_contents = soup.find_all(name='tr', attrs={"data-loop-item": "product"})
        for content in stock_contents:
            bid_price = content.find(name="span", attrs={"data-dg-watch-property": "BidPrice"}).text
            sell_price = content.find(name="span", attrs={"data-dg-watch-property": "AskPrice"}).text
            volume = content.find(name="span", attrs={"data-dg-watch-property": "CumulativeVolume"}).text
            isn = content.find(name="td", attrs={"data-dg-product-symbol-isin": "product"}).text
            timestamp = time()
            row = "{}\t{}\t{}\t{}\t{}\n".format(bid_price, sell_price, volume, isn, timestamp)
            print(row)
            with open("data.csv", "a") as f:
                f.write(row)

        try:
            next_page = driver.find_element_by_class_name('table-pagination-item ng-scope')
            print("NEXT PAGE")
            next_page.click()
        except NoSuchElementException:
            last_page = True

    sleep(1)
