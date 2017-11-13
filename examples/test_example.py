import selenium.webdriver
from selenium.webdriver.common.keys import Keys

from pyselenium import Page, Element


class SearchPage(Page):
    url = 'https://google.com'
    search_field = Element('//input[@name="q"]')


class ResultItem(Element):
    link = Element('.//h3/a')
    links = Element('.//a')


class SearchResultPage(Page):
    results = ResultItem('.//div[@class="g"]')


def test_search():
    driver = selenium.webdriver.Firefox()
    page = SearchPage(driver)
    page.open()
    page.search_field = 'selenium'
    page.search_field.send_keys(Keys.ENTER)

    result_page = SearchResultPage(driver)
    results = result_page.results

    assert 'http://www.seleniumhq.org/' in [i.link.get_attribute('href') for i in results]
    assert results[0].link.text != results[1].link.text
    assert len(results) == len(list(results)) == len([_ for _ in results])
    assert all(len(i.link) == 1 for i in results)
    assert all(1 <= len(i.links) <= 100 for i in results)

    page.open()
    page.search_field = 'cats'
    page.search_field.send_keys(Keys.ENTER)
    assert len(result_page.results[:4]) == 4
    assert any('youtube' in i.link.get_attribute('href') for i in result_page.results[:10])

    driver.close()


if __name__ == '__main__':
    test_search()
