from quart import Quart, render_template, url_for
from quart_schema import QuartSchema, Info, validate_response, validate_request, tag
from shemas import Channels, Channel, BaseOutput, SimilarutyOutput200, SimChannel
import asyncio
from eventer import Eventer


app = Quart(__name__)
QuartSchema(app,
            info=Info(
                title="Telegram Similarity Channels",
                version="0.0.1"
            ),
            tags=[
                {'name': 'v0', 'description': ''},
            ])


@app.post('/add_channels')
@validate_request(Channels)
@validate_response(BaseOutput)
@tag(['v0'])
async def add_channels(data: Channels) -> BaseOutput:
    '''
    Добавляет отслеживаемый каналы, скачивает и обрабатывает все сообщения каналов
    '''
    ev.messages['add_channels'] = data.channels
    return BaseOutput(message='access')

@app.post('/get_download_info')
async def get_info():
    return ev.channels_download_info

@app.post('/get_download_deleted_info')
async def get_deleted_info():
    return ev.added_channels

@app.get('/downloads')
async def d():
    return await render_template('download.html')

@app.get('/get_all_channels')
@validate_response(Channels)
@tag(['v0'])
async def get_channels() -> Channels:
    """
    Получить список всех отслеживаемых каналов
    """
    out = await ev.get_channels()
    return Channels(channels=[Channel(url) for url in out])

@app.post('/reload_channel')
@validate_request(Channel)
@validate_response(BaseOutput)
@tag(['v0'])
async def reload(data: Channel) -> BaseOutput:
    """
    Принудительное скачивание новых сообщений канала и их обработка
    """
    ev.messages['reload_channel'] = data.url
    return BaseOutput(message='access')

@app.get('/get_similarity')
@validate_request(Channel)
@validate_response(SimilarutyOutput200, 200)
@tag(['v0'])
async def sim(data: Channel) -> SimilarutyOutput200:
    """
    Похожесть канала на все остальные
    """
    out = await ev.get_sim(data.url)
    out = sorted(out, reverse=True, key=lambda x: x['similarity'])
    out = out[:5] if len(out) > 5 else out
    return SimilarutyOutput200(
        top_channels=
        [SimChannel(url=i['url'], similatity=i['similarity']) for i in out]
    )

async def run(loop):
    await ev.connect()
    await ev.looper()
    print('stop')


if __name__ == '__main__':

    ioloop = asyncio.get_event_loop()
    ev = Eventer(ioloop)
    tasks = [ioloop.create_task(run(ioloop)),
             ioloop.create_task(app.run_task(debug=True))]

    wait_tasks = asyncio.wait(tasks)

    ioloop.run_until_complete(wait_tasks)