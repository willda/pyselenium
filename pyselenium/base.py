import collections
import urllib.parse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC

from . import config


# Экспортируем только Page и Element
__all__ = 'Page', 'Element', 'By'


class Page:
    url = None
    # Относительный адрес страницы
    address = None

    def __init__(self, driver):
        self.driver = driver
        self._visit_child_elements()

    @property
    def title(self):
        return self.driver.title

    def _visit_child_elements(self, parent_el=None):
        """
        Рекурсивно обходит все дочерние элементы и сохраняет их иерархию
        """
        if parent_el is None:
            parent_el = self
        for child_el in vars(type(parent_el)).values():
            if not isinstance(child_el, Element):
                continue
            child_el.parent_el = parent_el
            child_el.page = self
            self._visit_child_elements(child_el)

    def open(self):
        url = urllib.parse.urljoin(self.url or config.HOSTNAME, self.address or '')
        try:
            self.driver.get(url)
        except WebDriverException:
            raise RuntimeError('Cannot open {}'.format(url))


class Element(collections.Sequence):

    locator = None

    def __init__(self, locator=None, by=By.XPATH):
        if locator is None:
            if self.locator is None:
                raise ValueError(
                    'locator must be either defined as a class attribute, or passed to __init__')
            elif isinstance(self.locator, str):
                self.locator = by, self.locator
        else:
            self.locator = by, locator

        # Ссылка на родительский элемент
        self.parent_el = None
        self.page = None

        self._index = 0
        self._slice = None

        for k, v in vars(type(self)).items():
            if isinstance(v, Element):
                el = v.clone()
                el.parent_el = self
                vars(self)[k] = el

    def clone(self):
        new_el = type(self)(*reversed(self.locator))
        new_el.page = self.page
        new_el.parent_el = self.parent_el
        return new_el

    @property
    def _root(self):
        page = self.page
        if isinstance(self.parent_el, Element):
            self.parent_el.raise_if_not_found()
            root = self.parent_el.element
        else:
            root = page.driver
        return root

    @property
    def _elements_list(self):
        elements = self.wait_elements()
        return elements[self._slice] if self._slice is not None else elements

    def wait(self, condition=None, timeout=None):
        rv = self.wait_elements(condition, timeout)
        if rv is None:
            raise TimeoutException(f'{self}, timeout: {timeout}')
        return self

    def wait_elements(self, condition=None, timeout=None):
        page = self.page
        while not isinstance(page, Page):
            page = page.parent_el
        if isinstance(self.parent_el, Element):
            self.parent_el.raise_if_not_found()
            root = self.parent_el.element
        else:
            root = page.driver

        if condition is None:
            condition = EC.presence_of_all_elements_located(self.locator)
        if timeout is None:
            timeout = config.WAIT_TIMEOUT
        try:
            return WebDriverWait(root, timeout).until(condition)
        except TimeoutException:
            return None

    def raise_if_not_found(self):
        if not self.element:
            raise RuntimeError(f'{self} is not found')

    @property
    def element(self):
        try:
            return self._elements_list[self._index]
        except IndexError:
            return None

    def __getattr__(self, item):
        """
        Проксирует обращения к атрибутам selenium.webdriver.remote.webelement.WebElement
        т.о. у объектов Element доступны методы элементов selenium:
        ```
        button = Element('button[@attr="name"]')
        button.click()```
        """
        if not item.startswith('_'):
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

    def hover(self):
        self.raise_if_not_found()
        return ActionChains(self.page.driver).move_to_element(self.element).perform()

    def __len__(self):
        return len(self._elements_list)

    def __getitem__(self, item):
        el = self.clone()
        if isinstance(item, slice):
            el._slice = item
        elif isinstance(item, int):
            if item >= len(self):
                raise IndexError('index out of range')
            el._index = item
        else:
            raise TypeError(f'indices must be integers or slices, not {type(item)}')
        return el

    def __repr__(self):
        return (
            f'{type(self).__name__}{[self._index] if self._index else ""} '
            f'[{self.locator[0]}={self.locator[1]}]'
        )
