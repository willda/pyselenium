## Coming soon...
### Пример использования

```python
from pages import SearchPage, SearchResultPage


def test_search_selenium(driver):
    page = SearchPage(driver)
    page.open()
    page.search_form.input_field = 'selenium'
    page.search_form.find_button.click()

    result_page = SearchResultPage(driver)
    assert result_page.result_link.text == 'docs.seleniumhq.org', 'Ссылка не найдена'
```
