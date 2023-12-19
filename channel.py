import asyncio
import aiohttp
from bs4 import BeautifulSoup

class Channel():
    """
    Класс канала. Создает подключение к каналу для скачивания информации
    """
    def __init__(self, url, loop=None):
        self.url = url.split('/')
        self.url = self.url[:-1] + ['s', self.url[-1]]
        self.url = '/'.join(self.url)

        self.session = aiohttp.ClientSession(loop=loop)

    async def disconnect(self):
        await self.session.close()
    async def load_batch(self, batch):
        """
        Метод для скачивания определенного количества сообщений.
        :param batch: str - определенный номер пачки сообщений
        """
        async with self.session.post(self.url + (f'?before={batch}' if batch else '')) as response: # запрос на получение определенной пачки сообщений

            html = await response.text()

            soup = BeautifulSoup(html, features='html.parser')

            texts = [i.text for i in soup.find_all('div', class_='tgme_widget_message_text')] # получение все блоков сообщений
            try:
                batch = soup.find('a', class_='tme_messages_more').get('href') # номер следующей пачки сообщений
                if 'before' in batch:
                    batch = batch.split('=')[-1]
                else:
                    batch = None # если мы дошли до конца, то будеми получать немного другой формат пачки, поэтому проводим проверку
            except AttributeError:
                batch = None
        #print(self.url, texts, batch, soup.find('a', class_='tme_messages_more'))
        return texts, batch, soup.find('a', class_='tme_messages_more')

    async def get_page(self, stop_message=None, start_callback=None, callback=None):
        """
        Метод, который скачивает все сообщения канала
        :param stop_message: при обновлении канала, можем передать этот параметр(последнее скачанное сообщение из базы). Как только в пачке будет это сообщение, то процесс прекратится
        :param start_callback: колбэк-функция, вызываемая при начале загрузки сообщений
        :param callback: колбэк-функция, вызываемая каждый батч, в которую передается текущий прогресс
        """
        texts = []
        text, batch, q = await self.load_batch(0) # загружаем самую первую пачку
        if stop_message and stop_message in text: # если в этой пачке будет стоп-сообщение, то возьмем все сообдщения до него и выйдем

            text = text[text.index(stop_message):]

            texts.extend(text[::-1])
            return texts[:-1]
        if not batch: # если это был первый и последний батч сообщение, то выходим
            return texts
        start_callback(batch)
        texts.extend(text[::-1])
        while True:
            await asyncio.sleep(0)
            if not batch:
                break

            #await asyncio.sleep(1)
            text, batch, q = await self.load_batch(batch) # загружаем следующую пачку сообщений
            callback(batch)
            if stop_message and stop_message in text:
                text = text[text.index(stop_message):]
                texts.extend(text[::-1])
                return texts[:-1]
            texts.extend(text[::-1])

        return texts





if __name__ == '__main__':
    c = Channel('https://t.me/ds_wiki')

    ioloop = asyncio.get_event_loop()
    tasks = [ioloop.create_task(c.get_page())]
    wait_tasks = asyncio.wait(tasks)
    ioloop.run_until_complete(wait_tasks)

    #ioloop.close()