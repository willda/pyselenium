from selenium.webdriver.remote.webelement import By

from core import Page, Element


class SearchFrom(Element):
    input_field = Element('text', By.ID)
    find_button = Element('.//button[@type="submit"]')


class SearchPage(Page):
    search_form = SearchFrom('//form')


class SearchResultPage(Page):
    result_link = Element('//a/b[text()="docs.seleniumhq.org"]')
