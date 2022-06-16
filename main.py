import requests
import json
from random import sample
import datetime


class YaUploader:

    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.token}'
        }

    def _get_upload_link(self, disk_file_path):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": disk_file_path, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def create_folder(self, name='Uploaded_photos'):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = self.get_headers()
        params = {"path": name, "overwrite": "true"}
        requests.put(url, headers=headers, params=params)
        return name

    def upload(self, path, files):
        if files:
            print(datetime.datetime.now(), 'Начало загрузки на диск')
            for file in files:
                file_name = path + '/' + file['file_name']
                url = self._get_upload_link(disk_file_path=file_name).get('href', '')
                image = requests.get(file['url']).content
                response = requests.put(url, data=image)
                if response.status_code == 201:
                    print(datetime.datetime.now(), 'Успешно загружена фотография', file['file_name'])
            print(datetime.datetime.now(), 'Загрузка завершена')
            self.create_json_file(files)

    def create_json_file(self, files):
        photos_description = [{'file_name': photo['file_name'], 'size': photo['size']} for photo in files]
        with open('photos.json', 'w') as file:
            json.dump(photos_description, file)


class VkPhoto:

    def __init__(self, id):
        self.id = id
        f = open('VK_token.txt', 'r')
        self.token = f.read()
        f.close()

    def _get_list_of_photos(self, response, count):
        number_of_photos = response['response']['count']

        # Определяем случайные номера фотографий для загрузки
        if count < min(1000, number_of_photos):
            numbers_for_download = sample(range(number_of_photos), count)
        else:
            numbers_for_download = range(min(1000, number_of_photos))

        files = list()
        for number in numbers_for_download:
            items = response['response']['items'][number]
            likes = items['likes']['count']
            date = items['date']

            # Ищем индекс максимального разрешения
            sizes = items['sizes']
            size_type = [size['type'] for size in sizes]
            index = -1
            for char in 'wzyxrqpoms':
                if char in size_type:
                    index = size_type.index(char)
                    break
            photo_url = sizes[index]['url']
            height = sizes[index]['height']
            width = sizes[index]['width']
            files.append({'likes': likes, 'date': date, 'url': photo_url, 'height': height, 'width': width})
        return files

    def get_photo(self, album_id, count=5):
        if album_id == -9000:
            url = 'https://api.vk.com/method/photos.getUserPhotos'
            params = {
                'user_id': self.id,
                'access_token': self.token,
                'v': 5.131,
                'extended': 1,
                'count': 1000
            }
        else:
            url = 'https://api.vk.com/method/photos.get'
            params = {
                'user_id': self.id,
                'access_token': self.token,
                'v': 5.131,
                'album_id': album_id,
                'extended': 1,
                'photo_sizes': 1,
                'count': 1000
            }
        print(datetime.datetime.now(), 'Формируется список фотографий...')
        response = requests.get(url, params=params)
        response = response.json()

        if 'response' in response.keys():
            files = self._get_list_of_photos(response, count)
            chosen_photos = list()
            # Ищем повторы в количествах лайков и менуем файлы
            likes_on_photo = [file['likes'] for file in files]
            for file in files:
                if likes_on_photo.count(file['likes']) > 1:
                    file_name = f"{file['likes']}_{file['date']}.jpg"
                else:
                    file_name = f"{file['likes']}.jpg"  # path.splitext(photo_url)[1]
                chosen_photos.append(
                    {'file_name': file_name, 'url': file['url'], 'size': f"{file['width']}x{file['height']}"})
            return chosen_photos
        print(f"Ошибка. {response['error']['error_msg']}")
        print('Загрузка невозможна')
        return []

    def get_albums(self):
        url = 'https://api.vk.com/method/photos.getAlbums'
        params = {
            'owner_id': self.id,
            'access_token': self.token,
            'v': 5.131,
            'count': 5,
            'need_system': 1
        }
        response = requests.get(url, params=params)
        response = response.json()

        if 'response' in response.keys():
            album_list = list()
            number = 1
            for album in response['response']['items']:
                if album['size'] > 0:
                    album_list.append((number, album.get('title'), album.get('size'), album.get('id')))
                    number += 1
            print('Доступны следующие альбомы:')
            for album in album_list:
                print(f'{album[0]}. {album[1]} - в альбоме доступно {album[2]} фото')
            album_number = input('Введите номер альбома: ')
            if album_number.isdigit() and 0 < int(album_number) <= len(album_list):
                album_number = int(album_number)
            else:
                print('Неверный номер альбома. Выбран первый альбом.')
                album_number = 1
            return album_list[album_number - 1][3]
        print(f"Ошибка. {response['error']['error_msg']}")
        print('Загрузка невозможна')
        return []


class OkPhoto:

    def __init__(self, id):
        self.id = id
        f = open('Ok_token.txt', 'r')
        self.application_key = f.readline().strip()
        self.token = f.readline().strip()
        f.close()

    def _get_list_of_photos(self, response, count):
        if response['hasMore']:
            number_of_photos = 100
        else:
            number_of_photos = response['totalCount']

        # Определяем случайные номера фотографий для загрузки
        if count < min(100, number_of_photos):
            numbers_for_download = sample(range(number_of_photos), count)
        else:
            numbers_for_download = range(min(100, number_of_photos))

        photos = response['photos']
        size_type = ['pic1024max', 'pic1024x768', 'pic640x480', 'pic320min', 'pic240min', 'pic190x190', 'pic180min',
                     'pic176x176', 'pic160x120', 'pic128max', 'pic128x128', 'pic50x50']

        files = list()
        for number in numbers_for_download:
            likes = photos[number]['mark_count']
            date = photos[number]['id']  # Взял id фотки вместо даты, в ответе от сервера нет даты

            # Ищем индекс максимального разрешения
            index = 0
            for size in size_type:
                if size in photos[number]:
                    index = size
                    break
            photo_url = photos[number][index]
            files.append({'likes': likes, 'date': date, 'url': photo_url, 'size': index})
        return files

    def get_photo(self, album_id, count=5):
        url = 'https://api.ok.ru/fb.do'
        if album_id == -1:
            params = {
                'application_key': self.application_key,
                'fid': self.id,
                'format': 'json',
                'method': 'photos.getPhotos',
                'access_token': self.token,
                'count': 100,
                'detectTotalCount': True
            }
        else:
            params = {
                'application_key': self.application_key,
                'aid': album_id,
                'format': 'json',
                'method': 'photos.getPhotos',
                'access_token': self.token,
                'count': 100,
                'detectTotalCount': True
            }
        print(datetime.datetime.now(), 'Формируется список фотографий...')
        response = requests.get(url, params=params)
        response = response.json()

        if 'photos' in response.keys():
            files = self._get_list_of_photos(response, count)
            chosen_photos = list()
            # Ищем повторы в количествах лайков и менуем файлы
            likes_on_photo = [file['likes'] for file in files]
            for file in files:
                if likes_on_photo.count(file['likes']) > 1:
                    file_name = f"{file['likes']}_{file['date']}.jpg"
                else:
                    file_name = f"{file['likes']}.jpg"

                chosen_photos.append(
                    {'file_name': file_name, 'url': file['url'], 'size': file['size']})
            return chosen_photos
        print(f"Ошибка. {response['error_msg']}")
        print('Загрузка невозможна')
        return []

    def _determine_mainalbum_size(self):
        url = 'https://api.ok.ru/fb.do'
        size_params = {
            'application_key': self.application_key,
            'fid': self.id,
            'format': 'json',
            'method': 'photos.getPhotos',
            'access_token': self.token,
            'count': 100
        }
        response = requests.get(url, params=size_params)
        response = response.json()
        if not response["hasMore"]:
            album_size = response.get('totalCount')
        else:
            album_size = 100
        return album_size

    def _determine_album_size(self, album_id):
        url = 'https://api.ok.ru/fb.do'
        size_params = {
            'application_key': self.application_key,
            'aid': album_id,
            'format': 'json',
            'method': 'photos.getPhotos',
            'access_token': self.token,
            'count': 100
        }
        response = requests.get(url, params=size_params)
        response = response.json()
        if not response["hasMore"]:
            album_size = response.get('totalCount')
        else:
            album_size = 100
        return album_size

    def get_albums(self):
        url = 'https://api.ok.ru/fb.do'
        params = {
            'application_key': self.application_key,
            'fid': self.id,
            'format': 'json',
            'method': 'photos.getAlbums',
            'access_token': self.token
        }
        print(datetime.datetime.now(), 'Ищем альбомы пользователя...')
        response = requests.get(url, params=params)
        response = response.json()
        if 'albums' in response.keys():
            album_list = [(1, 'Личные фотографии', -1, self._determine_mainalbum_size())]
            number = 2
            for album in response['albums']:
                album_size = self._determine_album_size(album['aid'])
                if album_size > 0:
                    album_list.append((number, album.get('title'), album.get('aid'), album_size))
                    number += 1
            print('Доступны следующие альбомы:')
            for album in album_list:
                print(f'{album[0]}. {album[1]} - в альбоме доступно {album[3]} фото')
            album_number = input('Введите номер альбома: ')
            if album_number.isdigit() and 0 < int(album_number) <= len(album_list):
                album_number = int(album_number)
            else:
                print('Неверный номер альбома. Выбран первый альбом.')
                album_number = 1
            return album_list[album_number - 1][2]
        print(f"Ошибка. {response['error_msg']}")
        print('Загрузка невозможна')
        return []


if __name__ == '__main__':
    print('''Из какой соцсети скачивать фотографии?
          1. Вконтакте
          2. Одноклассники''')
    social_number = input('Введите номер соцсети: ')
    id = input('Ведите id пользователя: ')
    social = {'1': VkPhoto, '2': OkPhoto}
    photos = social[social_number](id)
    album_id = photos.get_albums()
    if album_id:
        my_token = input('Введите токен ЯДиска: ')
        uploader = YaUploader(my_token)
        folder = uploader.create_folder()
        num = int(input('Сколько фотографий скачивать? '))
        uploader.upload(folder, photos.get_photo(album_id, num))
