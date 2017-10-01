import selenium.webdriver
from pyselenium import Page, Element, By


class SearchFrom(Element):
    locator = '//form'

    input_field = Element('text', By.ID)
    find_button = Element('.//button[@type="submit"]')


class SearchPage(Page):
    url = 'https://ya.ru'
    search_form = SearchFrom()


class SearchResultPage(Page):
    result_link = Element('//a/b[text()="docs.seleniumhq.org"]')


def test_search_selenium():
    driver = selenium.webdriver.Firefox()
    page = SearchPage(driver)
    page.open()
    page.search_form.input_field = 'selenium'
    page.search_form.find_button.click()

    result_page = SearchResultPage(driver)
    assert result_page.result_link.text == 'docs.seleniumhq.org', 'Ссылка не найдена'
