import asyncio
import websockets
import aiohttp
import json
from datetime import datetime, timedelta
from aiofile import AIOFile

class Currency_API_Client:
    base_url = 'https://api.privatbank.ua/p24api/exchange_rates?date='

    async def fetch_exchange_rates(self, date: str) -> dict:
        url = f'{self.base_url}{date}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()

class CurrencyService:
    def __init__(self, api_client: Currency_API_Client):
        self.api_client = api_client

    async def get_exchange_rate(self, currencies: list, days: int = 1):
        today = datetime.now()
        results = []
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%d.%m.%Y')
            rates_data = await self.api_client.fetch_exchange_rates(date)
            rates = self.filter_rates(rates_data, currencies)
            if rates:
                results.append({date: rates})
        return results

    def filter_rates(self, rates_data: dict, currencies: list) -> dict:
        filtered_rates = {}
        for rate in rates_data.get('exchangeRate', []):
            if rate['currency'] in currencies:
                filtered_rates[rate['currency']] = {
                    'sale': rate.get('saleRateNB', rate.get('saleRate')),
                    'purchase': rate.get('purchaseRateNB', rate.get('purchaseRate'))
                }
        return filtered_rates

async def handle_client(websocket, path):
    api_client = Currency_API_Client()
    currency_service = CurrencyService(api_client)
    async for message in websocket:
        if message.startswith('exchange'):
            parts = message.split()
            days = int(parts[1]) if len(parts) > 1 else 1
            currencies = ['USD', 'EUR']  # Default currencies
            rates = await currency_service.get_exchange_rate(currencies, days)
            await websocket.send(json.dumps(rates, indent=2))
            await log_command('Exchange command executed')

async def log_command(message: str):
    async with AIOFile('exchange_log.txt', 'a') as log_file:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await log_file.write(f'{now} - {message}\n')

async def main():
    server = await websockets.serve(handle_client, 'localhost', 8765)
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())