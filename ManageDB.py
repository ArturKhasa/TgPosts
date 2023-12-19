import aiosqlite
import asyncio
import secrets
import torch
import io
import sqlite3

def adapt_array(arr):
    """
    функция для конвертации тензора в допустий формат sql
    """
    out = io.BytesIO()
    torch.save(arr, out)
    out.seek(0)
    return sqlite3.Binary(out.read())


def convert_array(text):
    """
    обратная функция adapt_array
    :param text:
    """
    out = io.BytesIO(text)
    out.seek(0)
    return torch.load(out)

class Manage():
    """
    класс для работы с базой данных
    """
    def __init__(self, loop):
        self.loop = loop

        # регистрируем новый формат данных - тензор
        aiosqlite.register_adapter(torch.Tensor, adapt_array)

        aiosqlite.register_converter("array", convert_array)

    async def connect(self):
        self.con = await aiosqlite.connect('test.db', loop=self.loop)
        cur = await self.con.cursor()
        await cur.execute(f"CREATE TABLE IF NOT EXISTS channels("
                          f"id INTEGER PRIMARY KEY,"
                          f"url,"
                          f"channel_name)")
        await cur.execute(f"CREATE TABLE IF NOT EXISTS mean_embs("
                          f"id INTEGER PRIMARY KEY,"
                          f"channel_hex,"
                          f"mean_emb array)")
        await cur.close()

    async def commit(self):
        await self.con.commit()
        """print('disconnect')
        await self.con.close()
        print('connect')
        self.con = await aiosqlite.connect('test.db', loop=self.loop)
        print('connecnted')"""

    async def add_channel(self, url):
        cur = await self.con.cursor()
        channel_name = 'channel_' + secrets.token_hex(16)
        await cur.execute(f"INSERT INTO channels(url, channel_name) VALUES ('{url}', '{channel_name}')")

        await cur.execute(f"CREATE TABLE {channel_name}("
                          f"id INTEGER PRIMARY KEY,"
                          f"text,"
                          f"emb array)")

        await cur.close()

    async def add_text_to_channel(self, url, text, embs):
        print('add', url, len(text))
        cur = await self.con.cursor()
        channel_hex = await cur.execute(f"SELECT channel_name FROM channels WHERE url='{url}'")
        channel_hex = await channel_hex.fetchone()
        channel_hex = channel_hex[0]
        await cur.executemany(f"INSERT INTO {channel_hex}(text, emb) VALUES (?, ?)",
                              [[text[i], embs[i]] for i in range(len(text))])
        await cur.close()

    async def get_mean_embs_from_channel(self, url):
        cur = await self.con.cursor()

        channel_hex = await cur.execute(f"SELECT channel_name FROM channels WHERE url='{url}'")
        channel_hex = await channel_hex.fetchone()
        channel_hex = channel_hex[0]

        res = await cur.execute(f"SELECT mean_emb FROM mean_embs WHERE channel_hex='{channel_hex}'")
        embs = await res.fetchone()
        if not embs:
            res = await cur.execute(f"SELECT emb FROM {channel_hex}")
            res = await res.fetchall()
            embs = torch.concat([convert_array(i[0]).unsqueeze(0) for i in res], dim=0)
            embs = torch.mean(embs, dim=0)
            await cur.executemany(f"INSERT INTO mean_embs(channel_hex, mean_emb) VALUES (?, ?)",
                                  [[channel_hex, embs]])
        else:
            embs = convert_array(embs[0]).unsqueeze(0)
        await cur.close()
        await self.commit()
        return embs


    async def get_text_from_channel(self, url):
        cur = await self.con.cursor()
        channel_hex = await cur.execute(f"SELECT channel_name FROM channels WHERE url='{url}'")
        channel_hex = await channel_hex.fetchone()
        channel_hex = channel_hex[0]
        res = await cur.execute(f"SELECT text FROM {channel_hex}")
        res = await res.fetchall()
        await cur.close()
        return [i[0] for i in res]

    async def get_channels(self):
        cur = await self.con.cursor()
        res = await cur.execute(f"SELECT url FROM channels")
        res = await res.fetchall()
        await cur.close()
        return [i[0] for i in res]


async def test():
    await c.connect()
    print('start')
    embs = await c.get_mean_embs_from_channel('https://t.me/znakharj')
    print(embs.shape)
    await c.commit()
    await c.con.close()


if __name__ == '__main__':
    ioloop = asyncio.get_event_loop()
    c = Manage(ioloop)

    tasks = [ioloop.create_task(test())]
    wait_tasks = asyncio.wait(tasks)
    ioloop.run_until_complete(wait_tasks)

    ioloop.close()
