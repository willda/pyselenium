import urllib.parse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException

from cian_tests import config


# Экспортируем только Page и Element
__all__ = 'Page', 'Element'


class Page:
    # Относительный адрес страницы
    address = ''

    def __init__(self, driver):
        self.driver = driver
        self._visit_child_elements()

    def _visit_child_elements(self, parent_el=None):
        """
        Рекурсивно обходит все дочерние элементы и сохраняет их иерархию
        """
        if parent_el is None:
            parent_el = self
        for child_el in vars(parent_el.__class__).values():
            if not isinstance(child_el, Element):
                continue
            child_el.parent_el = parent_el
            self._visit_child_elements(child_el)

    def open(self):
        url = urllib.parse.urljoin(config.HOSTNAME, self.address)
        try:
            self.driver.get(url)
        except WebDriverException:
            raise RuntimeError('Cannot open {}'.format(url))


class Element:

    def __init__(self, locator, by=By.XPATH):
        self.locator = (by, locator)
        # Ссылка на родительский элемент
        self.parent_el = None

    @property
    def element(self):
        """
        Ищет и возвращает объект WebElement по `self.locator`
        если он существует, иначе None. В случае если элемент имеет родительский элемент,
        поиск выполняется от родительского элемента.
        """
        page = self.parent_el
        while not isinstance(page, Page):
            page = page.parent_el
        if isinstance(self.parent_el, Element):
            self.raise_if_not_found(self.parent_el)
            find_root = self.parent_el.element
        else:
            find_root = page.driver
        try:
            return WebDriverWait(page.driver, config.WAIT_TIMEOUT).until(
                lambda _: find_root.find_element(*self.locator))
        except TimeoutException:
            pass

    def __getattr__(self, item):
        """
        Проксирует обращения к атрибутам selenium.webdriver.remote.webelement.WebElement
        т.о. у объектов Element доступны методы элементов selenium:
        ```
        button = Element('button[@attr="name"]')
        button.click()```
        """
        self.raise_if_not_found()
        return getattr(self.element, item)

    def __set__(self, instance, value):
        """
        Позволяет заполнять поля через присваивание 
        `page.some_form.some_field = 'some_value'`
        """
        self.element.send_keys(value)

    def __bool__(self):
        """
        Позволяет писать:
        `assert page.some_element, 'Элемент some_element не найден'`
        `assert not page.some_element, 'Элемент some_element найден, а его не должно быть'`
        """
        return bool(self.element)

    def raise_if_not_found(self, elem=None):
        elem = self if elem is None else elem
        if not elem.element:
            raise RuntimeError('Element not found by {}: {}'.format(*elem.locator))

    def hover(self):
        self.raise_if_not_found()
        return ActionChains(self.driver).move_to_element(self.element).perform()
