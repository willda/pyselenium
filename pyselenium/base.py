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
        url = urllib.parse.urljoin(self.url or config.HOSTNAME, self.address or '')
        try:
            self.driver.get(url)
        except WebDriverException:
            raise RuntimeError('Cannot open {}'.format(url))


class Element:

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

    @property
    def element(self):
        return self._wait_element()

    def _wait_element(self, condition=None, timeout=config.WAIT_TIMEOUT):
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
        if condition is None:
            condition = EC.presence_of_element_located(self.locator)
        try:
            return WebDriverWait(find_root, timeout).until(condition)
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

    def wait_until_clickable(self, timeout=config.WAIT_TIMEOUT):
        self._wait_element(EC.element_to_be_clickable, timeout)
        return self

    def wait_until_visible(self, timeout=config.WAIT_TIMEOUT):
        self._wait_element(EC.visibility_of_element_located, timeout)
        return self
