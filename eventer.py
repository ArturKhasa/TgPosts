import asyncio
import time

import torch.nn.functional
from shemas import Channels, Channel
from channel import Channel as ChTg
from ManageDB import Manage
from recognize import Recognizer
import sqlite3
import validators


class Eventer():
    """класс, который содерждит все методы для удобного их вызова в основном коде"""
    def __init__(self, loop: asyncio.BaseEventLoop):
        self.loop = loop
        self.manage = Manage(loop)
        self.messages = { # флаги, которые содержат некоторые процессы, которые работают асинхронно основному серверу
            'add_channels': [],
            'reload_channel': [],
            'get_similarity': []
        }
        self.rec = Recognizer()

        self.channels_download_info = {}
        self.added_channels = []

    async def connect(self):
        await self.manage.connect()

    def wrapper2(self, url):
        def start_callback(info):
            self.channels_download_info[url] = [info, 0]
        return start_callback
    def wrapper(self, url):
        def channel_callback(info):
            self.channels_download_info[url][1] = info
        return channel_callback

    async def add_ch(self, url):
        """
        добавление канала по ссылке
        :param url: строка
        """
        print('start', url)
        ch = ChTg(url, self.loop)
        texts = await ch.get_page(start_callback=self.wrapper2(url),
            callback=self.wrapper(url))
        await ch.disconnect() #загрузка сообщений канала и удаление сессии

        while True:
            try:
                if len(texts) > 0:
                    embs = await self.rec.embed_bert_cls(texts[::-1]) # получение эмбеддингов
                    await self.manage.add_channel(url) # длобавление канала в бд
                    await self.manage.add_text_to_channel(url, texts[::-1], embs) # добавление текста и эмбеддингов в канала в бд
                    await self.manage.commit()
                break
            except sqlite3.ProgrammingError:
                print('repeat', url, texts)
                continue
        if url in self.channels_download_info.keys(): # удаление канала из списка скачиваемых
            del self.channels_download_info[url]
        print('end', url)
        self.added_channels.append(url)


    async def add_channels(self, chs: list[Channel]):
        """добавление списка каналов"""
        t = time.time()
        tasks = []

        for channel in chs:
            # итерируемся по каналам, проводим проверки на уже добавленные каналы, валидность ссылки
            chs = await self.manage.get_channels()
            if channel.url in chs:
                continue
            if not validators.url(channel.url):
                continue
            url = channel.url

            task = self.loop.create_task(self.add_ch(url)) # создаем задачу по скачиванию канала(она сразу запускается асинхронно
            tasks.append(task)

            if len(tasks) == 30:
                # как только запустили 30 задач, начинаем ожидание выполнения хотя бы одной
                while True:
                    await asyncio.sleep(1)
                    flag = False
                    i = 0
                    while i < len(tasks):
                        # как только выполнена одна задача, то удлаляем ее из списка и выходим из бесконечного цикла, тем самым запуская скачивание следующей задачи
                        if tasks[i].done():
                            del tasks[i]
                            flag = True
                            break
                        i += 1
                    if flag:
                        break

        print('Добавление закончено', time.time() - t)


    async def get_channels(self):
        """
        получение списка всех каналов
        """
        t = await self.manage.get_channels()
        return t

    async def reload_channel(self, url):
        """
        скачивание всех новых сообщений канала
        :param url:
        :return:
        """
        print('reload', url)
        text = await self.manage.get_text_from_channel(url) # получаем список всех сообщений канала

        ch = ChTg(url, self.loop)
        texts = await ch.get_page(stop_message=text[-1]) # запускаем скачивание новых сообщений до последнего скачанного
        await ch.disconnect()
        print(texts)
        embs = await self.rec.embed_bert_cls(texts[::-1]) # получаем эмбеддинги
        await self.manage.add_text_to_channel(url, texts[::-1], embs) # добавляем в бд новый текст и эмбеддинги
        await self.manage.commit()

    async def get_sim(self, url):
        """
        получение похожих каналов
        :param url: ссылка на канал
        """
        chs = await self.manage.get_channels() # получаем список всех каналов
        ch_emb = None
        mean_embs = []
        from tqdm import tqdm
        for i in tqdm(chs):
            out = await self.manage.get_mean_embs_from_channel(i) # итерируемся по всем каналам и достаем усредненный эмбеддинг каждого
            if i != url:
                mean_embs.append({'url': i, 'emb': out}) # добавляем в словарь пару ссылка - эмбеддинг
            else:
                ch_emb = out
        out = []
        for i in tqdm(mean_embs): # итерируемся по полученным средним эмбеддингам и высчитываем косинусную схожесть.
            out.append({'url': i['url'],
                        'similarity': torch.nn.functional.cosine_similarity(
                            i['emb'],
                            ch_emb
                        )})
        return out

    async def looper(self):
        """
        для определнных задач треубется связь с классом во время работы какой-то функции
        поэтому создан такой цикл который постоянно проверяет поле классана какие-то запущенные процессы и запускает долгие функции
        """
        while True:
            await asyncio.sleep(0.5)
            if self.messages['add_channels']:
                print('add')
                await self.add_channels(self.messages['add_channels']) # запуск процесса по скачиванию каналов
                self.messages['add_channels'] = []
            if self.messages['reload_channel']:
                await self.reload_channel(self.messages['reload_channel']) # запуск процесса по перезагрузке канала
                self.messages['reload_channel'] = []


async def test():
    await c.connect()
    await c.add_channels([Channel('https://t.me/ds_wiki'),
                          Channel('https://t.me/OpportunityCup2023')])


if __name__ == '__main__':
    ioloop = asyncio.get_event_loop()
    c = Eventer(ioloop)

    tasks = [ioloop.create_task(test())]
    wait_tasks = asyncio.wait(tasks)
    ioloop.run_until_complete(wait_tasks)

    ioloop.close()
