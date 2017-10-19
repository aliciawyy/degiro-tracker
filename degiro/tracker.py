from time import sleep, time

import logging
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium import webdriver
import sqlite3

from . import util

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


options = webdriver.ChromeOptions()
# options.add_argument('headless')
driver = webdriver.Chrome(util.get_chrome_driver_path(),
                          chrome_options=options)

account = util.DgAccount()
account.login(driver)

WebDriverWait(driver, 20).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'wrapper')))
logging.info("Navigating to favourites page")

driver.get("https://trader.degiro.nl/trader/#!/favourites")

WebDriverWait(driver, 20).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'favourites')))
for i in range(100):

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

driver.close()
