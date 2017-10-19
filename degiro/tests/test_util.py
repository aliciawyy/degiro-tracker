import os
from unittest import TestCase
import mock
from parameterized import parameterized

from .. import util


class UtilsTest(TestCase):

    @parameterized.expand([("nt", "driver.exe"), ("posix", "driver")])
    def test_get_chrome_driver_path(self, name, expected_end):
        with mock.patch('os.name', name):
            filename = util.get_chrome_driver_path()
        self.assertTrue(filename.endswith(expected_end), msg=filename)
        self.assertTrue(os.path.exists(filename), msg=filename)
