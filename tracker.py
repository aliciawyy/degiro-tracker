import os
from threading import Thread
from time import sleep, time

import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium import webdriver
import sqlite3

conn = sqlite3.connect('data.db', check_same_thread=False)

CREATE_TABLE_QUERY = '''
CREATE TABLE prices (
    isn       REAL,
    bid       TEXT,
    ask       REAL,
    cul_vol   TEXT,
    timestamp DATETIME

)'''

c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")

if not len(c.fetchall()) == 1:
    c.execute(CREATE_TABLE_QUERY)

base = os.path.dirname(os.path.realpath(__file__))
load_dotenv(os.path.join(base, '.env'))
USERNAME = os.environ.get("DG_USERNAME")
PASSWORD = os.environ.get("DG_PASSWORD")

INSERT_QUERY = '''
INSERT INTO prices (
       cul_vol,
       isn,
       ask,
       bid,
       timestamp
   )
   VALUES (
       {cul_vol},
       '{isn}',
       {ask},
       {bid},
       {timestamp}
    );

'''


def insert_worker(connection, **kwargs):
    while True:
        try:
            connection.execute(INSERT_QUERY.format(**kwargs))
            return True
        except Exception as e:
            print(e)
            pass


if os.name == 'posix':
    DRIVER_PATH = "drivers/chromedriver"
elif os.name == 'nt':
    DRIVER_PATH = 'drivers/chromedriver.exe'
else:
    logging.error("No chromedriver found for OS")
    exit(1)

options = webdriver.ChromeOptions()
# options.add_argument('headless')

driver = webdriver.Chrome(os.path.join(base, DRIVER_PATH), chrome_options=options)
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

            bid = content.find(name="span", attrs={"data-dg-watch-property": "BidPrice"}).text
            ask = content.find(name="span", attrs={"data-dg-watch-property": "AskPrice"}).text
            cul_vol = content.find(name="span", attrs={"data-dg-watch-property": "CumulativeVolume"}).text
            isn = content.find(name="td", attrs={"data-dg-product-symbol-isin": "product"}).text
            timestamp = time()

            try:
                bid = float(bid)
                ask = float(ask)
            except:
                continue

            try:
                cul_vol = float(cul_vol.strip(","))
            except:
                cul_vol = 0.0

            insert_worker(conn,
                          bid=bid,
                          ask=ask,
                          cul_vol=cul_vol,
                          isn=isn,
                          timestamp=timestamp)

            conn.commit()

            sleep(1)

        try:
            next_page = driver.find_element_by_class_name('table-pagination-item ng-scope')
            print("NEXT PAGE")
            next_page.click()
        except NoSuchElementException:
            last_page = True
