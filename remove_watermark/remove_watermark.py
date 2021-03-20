import cv2
import os

from settings.settings import DIR_IMAGES


if __name__ == '__main__':
    """
    Скрипт удаления водяного знака по маске
    """

    current_dir = os.getcwd().replace('remove_watermark', '')

    files = os.listdir(current_dir + DIR_IMAGES)  # список файлов в директории DIR_IMAGES
    file_mask = 'maska.png'  # имя файла изображения с образцом водяного знака для удаления

    mask = cv2.imread(file_mask, 0)

    for file in files:
        try:
            img = cv2.imread(current_dir + DIR_IMAGES + file)
            dst = cv2.inpaint(img, mask, 1, cv2.INPAINT_TELEA)
            # dst = cv2.inpaint(img, mask, 3, cv2.INPAINT_NS)
            cv2.imwrite(current_dir + DIR_IMAGES + file, dst)
        except Exception as ex:
            print('Ошибка! Невозможно обработать файл', file)
            print(ex)

        # break
