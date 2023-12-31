import asyncio
import logging

import aiohttp
import names
import websockets
from websockets import WebSocketServerProtocol, WebSocketProtocolError

logging.basicConfig(level=logging.INFO)

# https://api.privatbank.ua/#p24/exchangeArchive архів
#https://api.privatbank.ua/#p24/exchange
#Готівковий курс ПриватБанку (у відділеннях):

# GET JSON:
# https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5
# https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5
# 14.11.2022р. XML відповідь буде змінена на JSON формат
# Безготівковий курс ПриватБанку (конвертація за картками, Приват24, поповнення вкладів):

# GET JSON:
# https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=11
# https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11
# 14.11.2022р. XML відповідь буде змінена на JSON формат


async def get_exchange():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5') as resp:
            if resp.status == 200:
                r = await resp.json()
                exc, = list(filter(lambda el: el['ccy'] == 'USD', r))
            return f"USD: buy: {exc['buy']}, sale: {exc['sale']}"
        

class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except WebSocketProtocolError as err:
            logging.error(err)
        finally:
            await self.unregister(ws)



    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == 'exchange':
                message = await get_exchange()
                await self.send_to_clients(message)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())
