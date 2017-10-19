import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

log = logging.getLogger(__name__)
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class DgAccount(object):
    _t_user = "DG_USERNAME"
    _t_pwd = "DG_PASSWORD"

    def __init__(self, user=None, pwd=None):
        self.user = user or os.environ.get(self._t_user)
        self._pwd = pwd or os.environ.get(self._t_pwd)
        if not (self.user and self._pwd):
            raise ValueError("User and password cannot be none!")

        self.url_login = "https://trader.degiro.nl/login/uk?#/login"

    def login(self, driver):
        driver.get(self.url_login)
        for tag, v in [("username", self.user), ("password", self._pwd)]:
            field = WebDriverWait(driver, 20).until(
                expected_conditions.presence_of_element_located(
                    (By.ID, tag)
                )
            )
            field.send_keys(v)
        time.sleep(2)
        driver.find_element_by_name('loginButtonUniversal').click()
        log.info("Login as user {}".format(self.user))
        time.sleep(5)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.user)


def get_chrome_driver_path():
    ext_map = {"nt": ".exe"}
    driver_name = "chromedriver" + ext_map.get(os.name, "")
    return os.path.join(PROJECT_DIR, "drivers", driver_name)
