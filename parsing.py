import json
import os
import pickle
import random
import time
import requests

from bs4 import BeautifulSoup
from loguru import logger

from settings.settings import MAIN_URL, HEADERS, DIR_PICKLE, SEARCH_REQUEST, LIMIT_ERROR_REQUEST, \
    PAUSE_PARSING_PRODUCT, FILE_TMP_RESULT, FILE_RECOVERY, DIR_RECOVERY, RECOVERY_MODE

request_counter = 0  # счетчик request запросов
error_count = 0  # счетчик ошибок request запросов, идущих подряд


def save_session(session):
    with open(os.getcwd() + DIR_PICKLE + 'session.pickle', 'wb') as file_session:
        pickle.dump(session, file_session)
        # logger.debug(f'Сохранили успешную сессию в файл session.pickle')


def get_url_product(session, number):
    """
    Получаем ссылку на товар из поискового запроса SEARCH_REQUEST
    :param session: текущая сессия
    :param number: артикул товара
    :return: url ссылка на товар
    """
    global request_counter, error_count
    url = None

    logger.info(f'Открываем страницу поиска товара {SEARCH_REQUEST + number}')
    try:
        response = session.get(SEARCH_REQUEST + number, headers=HEADERS)
        request_counter += 1

        if response.status_code == 200:
            save_session(session=session)
            soup = BeautifulSoup(response.text, 'lxml')
            url = soup.find('li', class_='search-item').find('a').get('href')

            if url:
                error_count = 0  # обнуляем счетчик ошибок
                url = MAIN_URL + url
                logger.success(f'Успешно получена ссылка на товар {url}')
            else:
                logger.error(f'Не удалось получить ссылку на товаров при успешном ответе сервера')
                error_count += 1

        else:
            logger.error(f'Получить ссылку на товар невозможно. Ответ сервера {response.status_code}')
            error_count += 1

    except Exception as ex:
        logger.error(f'Ошибка открытия страницы. Ссылка на товар не получена. {ex}')
        error_count += 1
        logger.debug(f'Счетчик request запросов {request_counter}, счетчик ошибок {error_count}')

    return url


def get_parsing_product(session, url_product):
    """
    Парсинг страницы товара
    :param session: текущая сессия
    :param url_product: url страницы товара
    :return: result_parsing_product словарь результата парсинга одного товара
    """

    global request_counter, error_count

    result_parsing_product = {}  # результат парсинга страницы

    product_name = ''  # наименование товара
    title, description, keywords = '', '', ''  # seo данные
    groups = []  # список разделов
    images = []  # список ссылок на изображения
    properties = {}  # словарь характеристик товара и их значений
    price = ''  # цена товара
    stock = ''  # наличие на складе
    documents = []  # документы

    try:
        response = session.get(url=url_product, headers=HEADERS)
        request_counter += 1
    except Exception as ex:  # ответ от сервера не получен
        logger.error(f'Ошибка открытия страницы товара. Парсинг невозможен. {ex}')
        error_count += 1
        logger.debug(f'Счетчик request запросов {request_counter}, счетчик ошибок {error_count}')
        raise ConnectionError  # выходим из функции с ошибкой

    if response.status_code == 200:
        save_session(session=session)

        # with open(os.getcwd() + DIR_PICKLE + 'response.pickle', 'wb') as file_session:
        #     pickle.dump(response, file_session)

        soup = BeautifulSoup(response.text, 'lxml')

        # парсим наименование товара
        try:
            product_name = soup.find('h1').text.strip()
        except Exception as ex:
            logger.error(f'Ошибка при получении названия товара из тега h1 {ex}')
            error_count += 1
            raise AttributeError  # выходим из функции с ошибкой

        # парсим seo данные
        try:
            title = soup.find('title').text.strip()
            description = soup.find('meta', attrs={'name': 'Description'}).get('content').strip()
            keywords = soup.find('meta', attrs={'name': 'Keywords'}).get('content').strip()
        except Exception as ex:
            logger.warning(f'Ошибка при парсинге SEO-данных {ex}')  # продолжаем парсинг

        # парсим разделы
        try:
            groups_soup = soup.find('nav', class_='breadcrumbs').findChild('ul'). \
                find_all('li', class_='breadcrumbs__dropdown')

            for group in groups_soup:
                if group.find('a').text.strip() == 'Сантехкомплект' or \
                        group.find('a').text.strip() == 'Каталог товаров':
                    continue
                else:
                    groups.append(group.find('a').text.strip())

        except Exception as ex:
            logger.warning(f'Ошибка при парсинге разделов {ex}')  # продолжаем парсинг

        # парсим изображения
        try:
            images_soup = soup.select('div.gallery__item-ul.swiper-wrapper.js-item-ul.gal-images')[-1].\
                find_all('img')
            for image in images_soup:
                images.append(MAIN_URL + image['src'][:image['src'].find('?')])
        except Exception as ex:
            logger.warning(f'Ошибка при парсинге изображений {ex}')  # продолжаем парсинг

        # парсим характеристики
        try:
            properties_soup = soup.find_all('tr', class_='property__table-tr')
            for pr in properties_soup:
                key = pr.find('td', class_='property__table-name').text.strip().split('\n')[0]
                value = pr.find('td', class_='property__table-value').text.strip()
                properties[key] = value
        except Exception as ex:
            logger.warning(f'Ошибка при парсинге характеристик {ex}')  # продолжаем парсинг

        # парсим цену
        try:
            price = soup.find('span', class_='js-price-inner').text.replace(' ', '').replace('Р', '').strip()
        except Exception as ex:
            logger.warning(f'Ошибка при парсинге цены {ex}')  # продолжаем парсинг

        # парсим наличие на складе
        try:
            stock = soup.find('div', class_='variants__price-availability').text.strip()
        except Exception as ex:
            logger.warning(f'Ошибка при парсинге наличия на складе {ex}')  # продолжаем парсинг

        # парсим документы
        try:
            documents_soup = soup.find_all('div', class_='product__document-item')
            for doc in documents_soup:
                documents.append(MAIN_URL + doc.find('a').get('href').replace('&convert', ''))
        except Exception as ex:
            logger.warning(f'Ошибка при парсинге документов {ex}')  # продолжаем парсинг

        result_parsing_product = {
            'product_name': product_name,
            'groups': groups,
            'price': price,
            'stock': stock,
            'images': images,
            'properties': properties,
            'documents': documents,
            'title': title,
            'description': description,
            'keywords': keywords,
        }

    else:
        # сервер вернул код ответа не равный 200
        logger.error(f'Спарсить инф-цию о товаре невозможно. Ответ сервера {response.status_code}')
        error_count += 1

    return result_parsing_product


def save_tmp_result(result_parsing, recovery):
    """
    Запись предварительного результата парсинга в случае ошибки
    :param recovery: список артикулов для восстановаления (продолжения парсинга)
    :param result_parsing: промежуточный результат парсинга
    :return: файлы FILE_TMP_RESULT, FILE_RECOVERY в папке DIR_RECOVERY
    """
    path_file_save = os.getcwd() + DIR_RECOVERY + FILE_TMP_RESULT
    with open(path_file_save, 'w', encoding='utf-8') as file_json:
        json.dump(result_parsing, file_json, ensure_ascii=False, indent=4)
        logger.debug(f'Сохранили промежуточный результат в файл {path_file_save}')

    path_file_recovery = os.getcwd() + DIR_RECOVERY + FILE_RECOVERY
    with open(path_file_recovery, 'w', encoding='utf-8') as file_txt:
        file_txt.write("\n".join(map(str, recovery)))
        logger.debug(f'Сохранили файл для восстановления (продолжения) парсинга {path_file_recovery}')


def parsing(article_numbers: list):
    """
    Основная функция парсинга товаров
    :param article_numbers: список артикулов товара для парсинга
    :return: результат парсинга всех товаров в формате json
    """
    global request_counter, error_count

    if not RECOVERY_MODE:
        result_parsing_all = {}  # словарь всего результата парсинга
    else:
        # если включен режим допарсинга, получаем предварительные результаты прерванного парсинга
        path_file_save = os.getcwd() + DIR_RECOVERY + FILE_TMP_RESULT
        with open(path_file_save, 'r', encoding='utf-8') as file_json:
            data = file_json.read()
            result_parsing_all = json.loads(data)

    logger.info(f'Открываем главную страницу {MAIN_URL}')
    session = requests.Session()
    response = session.get(url=MAIN_URL, headers=HEADERS)
    request_counter += 1
    logger.debug(f'Код ответа {response.status_code}')

    if response.status_code == 200:
        save_session(session=session)
    else:
        logger.error(f'Ошибка открытия главной страницы. Ответ сервера {response.status_code}')
        logger.debug(f'Счетчик request запросов {request_counter}')
        raise ConnectionError  # выходим из функции

    count_numbers = len(article_numbers)   # счетчик кол-ва спарсенных товаров
    article_recovery = article_numbers.copy()  # создаем копию списка артикулов для режима восстановления
    for number in article_numbers:
        # пауза между парсингом товаров
        time.sleep(random.randrange(PAUSE_PARSING_PRODUCT[0], PAUSE_PARSING_PRODUCT[1]))
        logger.debug(f'Осталось парсить товаров {count_numbers}')
        count_numbers -= 1

        if error_count > LIMIT_ERROR_REQUEST:
            logger.critical(f'Превышен лимит ошибок {error_count}')
            # сохраняем промежуточный результат и данные для восстановления (продолжения) парсинга
            save_tmp_result(result_parsing=result_parsing_all, recovery=article_recovery)
            raise ConnectionError  # выходим из цикла и функции из-за превышения лимита request запросов

        logger.info(f'Получаем ссылку товара с артикулом {number}')
        url_product = get_url_product(session=session, number=number)
        if not url_product:
            logger.warning(f'Не удалось получить ссылку на товар {number}. Пропускаем товар')
            continue  # продолжаем цикл и делаем проверку на лимит ошибок

        logger.info(f'Переходим на страницу товара и парсим информацию')
        try:
            result_parsing_product = get_parsing_product(session=session, url_product=url_product)
            if not result_parsing_product:  # ответ сервера был не 200
                logger.warning(f'Пропускаем товар')
                continue  # продолжаем цикл и делаем проверку на лимит ошибок
            logger.success(f'Успешно получена информация о товаре c артикулом {number}')
        except Exception as ex:  # не было ответа от сервера или не получено наименование товара
            logger.warning(f'Пропускаем товар {ex}')
            continue  # продолжаем цикл и делаем проверку на лимит ошибок

        # сохраняем инф-цию парсинга очередного товара
        result_parsing_all[number] = result_parsing_product
        # удаляем элемент из списка для восстановления
        article_recovery.remove(number)

    # сохраняем результаты в папку DIR_RECOVERY
    # при успешном завершении файл FILE_RECOVERY должен быть пустой
    save_tmp_result(result_parsing=result_parsing_all, recovery=article_recovery)

    if len(article_recovery) > 0:
        logger.warning(f'Не удалось получить информацию по {len(article_recovery)} товарам')

    return result_parsing_all


if __name__ == '__main__':
    pass
