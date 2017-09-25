import pytest
import selenium.webdriver as webdriver

@pytest.fixture(scope='module')
def driver():
    driver = webdriver.Firefox()
    yield driver
    driver.close()