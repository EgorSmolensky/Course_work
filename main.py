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

    def _get_list_of_photos(self, response, count):
        number_of_photos = response['response']['count']

        # Определяем случайные номера фотографий для загрузки
        if count < min(1000, number_of_photos):
            numbers_for_download = sample(range(number_of_photos), count)
        else:
            numbers_for_download = range(min(1000, number_of_photos))

        files = list()
        for number in numbers_for_download:
            likes = response['response']['items'][number]['likes']['count']
            date = response['response']['items'][number]['date']

            # Ищем индекс максимального разрешения
            size_type = [size['type'] for size in response['response']['items'][number]['sizes']]
            index = -1
            for char in 'wzyxrqpoms':
                if char in size_type:
                    index = size_type.index(char)
                    break
            photo_url = response['response']['items'][number]['sizes'][index]['url']
            height = response['response']['items'][number]['sizes'][index]['height']
            width = response['response']['items'][number]['sizes'][index]['width']
            files.append({'likes': likes, 'date': date, 'url': photo_url, 'height': height, 'width': width})
        return files

    def get_photo(self, count=5):
        url = 'https://api.vk.com/method/photos.get'
        params = {
            'user_id': self.id,
            'access_token': 'a67f00c673c3d4b12800dd0ba29579ec56d804f3c5f3bbcef5328d4b3981fa5987b951cf2c8d8b24b9abd',
            'v': 5.131,
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1,
            'count': 1000
        }
        print(datetime.datetime.now(), 'Формируется список фотографий...')
        response = requests.get(url, params=params)
        response = response.json()

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


if __name__ == '__main__':
    id = input('Ведите id пользователя Вконтаке: ')
    my_token = input('Введите токен ЯДиска: ')
    photos = VkPhoto(id)
    uploader = YaUploader(my_token)
    folder = uploader.create_folder()
    num = int(input('Сколько фотографий скачивать? '))
    uploader.upload(folder, photos.get_photo(num))


