import json
import re
import sys
import os
import pandas as pd

from loguru import logger

import parsing
from settings.settings import FILE_PARSING, FILE_RECOVERY, DIR_PARSING, DIR_LOGS, DIR_RECOVERY, \
    RECOVERY_MODE, FILE_RESULT_CSV, DIR_PICKLE


def get_article_from_file(name_file):
    """
    Получение артикулов для парсинга из файла
    :param name_file: имя файла с артикулами
    :return: список артикулов товара для парсинга
    """
    artickle_numbers = []
    with open(name_file, mode='r', encoding='utf-8') as file:
        artickle_numbers = file.read().splitlines()
        # artickle_numbers = [number for number in (line.rstrip() for line in file.readlines())]
    return artickle_numbers


def save_result_to_csv_file(result):
    """
    Форматирование результата парсинга и сохранение в json и csv файлы
    :param result: результаты парсинга в json формате
    :return: сохраненные файлы result.json и result.csv
    """

    result_list = []

    for key, product in result.items():
        product_dict = {
            'ID': 'fl' + key[-1::-1].replace('-', ''),  # "переворачиваем значение и добавляем fl"
            'Наименование': product['product_name'].replace('\n', ''),
            'Цена': product['price'],

            'Наличие': 'onbackorder' if not re.search('\d+', product['stock']) else 'instock',

            'Остаток': '0' if not re.search('\d+', product['stock']) else re.search('\d+', product['stock']).group(0),

            'Изображения': ';'.join(product['images']),  # преобразование списка в строку
            'Документы': ';'.join(product['documents']),
            'Title': product['title'].replace('\n', ''),
            'Description': product['description'].replace('\n', ''),
            'Keywords': product['keywords'].replace('\n', ''),
        }

        for n, group in enumerate(product['groups']):
            product_dict['Раздел_' + str(n+1)] = group.replace('\n', '')

        for prop, value in product['properties'].items():
            product_dict[prop] = value.replace('\n', '')

        result_list.append(product_dict)

    # сохранение результата в json файл
    path_result_file_json = os.getcwd() + DIR_PICKLE + 'result.json'
    with open(path_result_file_json, 'w', encoding='utf-8') as file:
        json.dump(result_list, file, ensure_ascii=False, indent=4)
        logger.success(f'Успешно сохранили результаты парсинга в json-файл result.json')

    # сохранение результата в csv-файл
    df = pd.DataFrame(result_list)
    path_result_file_csv = os.getcwd() + DIR_PARSING + FILE_RESULT_CSV
    df.to_csv(path_result_file_csv, encoding='utf-8', sep=';', index=False)
    logger.success(f'Успешно сохранили результаты парсинга в csv-файл result.csv')

    # return result_list


if __name__ == '__main__':
    path_log = os.getcwd() + DIR_LOGS + 'debug.log'
    logger.add(path_log, level='DEBUG', compression="zip", rotation="9:00", retention="3 days", encoding='utf-8')
    logger.info(f'Запуск скрипта')

    # проверяем режим работы (стандартный или восстановление) и определяем имя файла для парсинга
    if not RECOVERY_MODE:
        file_work = os.getcwd() + DIR_PARSING + FILE_PARSING
    else:
        logger.warning(f'Запущен режим восстановления (допарсинга) из файла {FILE_RECOVERY}')
        file_work = os.getcwd() + DIR_RECOVERY + FILE_RECOVERY

    logger.info(f'Получаем из файла {file_work} данные для парсинга')
    try:
        article_numbers = get_article_from_file(file_work)
        if article_numbers:
            logger.success(f'Успешно получены данные. Общее кол-во арктикулов {len(article_numbers)}')
        else:
            logger.warning(f'Файл {file_work} пустой. Завершаем работу скрипта')
            sys.exit(1)
    except Exception as ex:
        logger.error(f'Ошибка при получении данных из файла {ex}')
        logger.warning(f'Завершаем работу скрипта с ошибкой')
        sys.exit(1)

    try:
        # основной парсинг товаров
        result_parsing = parsing.parsing(article_numbers=article_numbers)
        # сохранение результатов парсинга в файл
        save_result_to_csv_file(result=result_parsing)
        logger.success(f'Скрипт успешно завершен')
    except Exception as ex:
        logger.critical(f'Выполнение скрипта завершено с ошибкой. См. лог-файлы или обратитесь к разработчику {ex}')
