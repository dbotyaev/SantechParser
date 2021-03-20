import os, sys


if __name__ == '__main__':
    """
    Скрипт замены фотографий заглушки товаров
    """

    source_img = 'blue_logo_banner.png'  # файл источник картинки
    file_script = sys.argv[0].split('/')[-1]  # файл скрипта
    file_script_bat = sys.argv[0].split('/')[-1].split('.')[0] + '.bat'  # исполняемый файл bat
    files_extension = [source_img, file_script, file_script_bat, 'readme.txt']  # список файлов исключений
    list_dir = os.listdir(os.getcwd())  # список файлов в текущей директории

    for file in list_dir:
        if file not in files_extension:
            command_copy_file = f'copy {source_img} {file}'
            print(command_copy_file)
            os.popen(command_copy_file)

            # break