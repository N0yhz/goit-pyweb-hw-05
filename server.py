import sys
import asyncio
import aiohttp
import websockets
from aiofile import AIOFile
from datetime import datetime, timedelta
from typing import List, Dict
from aiopath import AsyncPath

log_file = AsyncPath("exchange.log.txt")

class Currency_API_Client:
    base_url = 'https://api.privatbank.ua/p24api/exchange_rates?date='

    def __init__(self):
        pass

    async def fetch_exhange_rates(self, session: aiohttp.ClientSession, date: str) -> Dict: 
        url = f'{self.base_url}{date}'
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as ce:
            print(f'Error occurred while fetching exchange rates on {date}: {ce}')
            return {}

class CurrencyService:
    def __init__(self,api_client: Currency_API_Client):
        self.api_client = api_client
    
    async def get_exchange_rates_for_days(self, days: int, currencies:List[str]) -> List[Dict]:
        today = datetime.now()
        results = []
        async with aiohttp.ClientSession() as session:
            for i in range(days):
                date = (today - timedelta(days=i)).strftime('%d.%m.%Y')
                rates_data = await self.api_client.fetch_exhange_rates(session,date)
                rates = self.filter_rates(rates_data, currencies)
                if rates:
                    results.append({date:rates})
            return results

    def filter_rates(self, rates_data: Dict, currencies: List[str]) -> Dict:
        filtered_rates = {}
        for rate in rates_data.get('exchangeRate', []):
            if rate['currency'] in currencies:
                filtered_rates[rate['currency']] = {
                    'sale': rate.get('saleRateNB', rate.get('saleRate')),
                    'purchase': rate.get('purchaseRateNB', rate.get('purchaseRate'))                                    
                }
        return filtered_rates

#Websocket
async def log_command(command:str):
    async with AIOFile(log_file, 'a') as afp:
        await afp.write(f'{datetime.now()} - Execute command: {command}\n')

async def get_exchange_for_days(days: int):
    fetcher = CurrencyService()
    rates = await fetcher.get_exchange_rates(days)
    return rates

async def websockets_handler(websocket, path, currency_service):
        async for message in websocket:
            if message.startswith('exchange'):
                await log_command(message)
                parts = message.split()
                if len(parts)< 1:
                    try:
                        days = int(parts[1])
                        rates = await currency_service.get_exchange_rates_for_days(days, ['USD', 'EUR'])
                        response = f'Exchange rates for the last {days} days:\n{rates}'
                    except ValueError:
                        response = 'Invalid number of days.'
                else:
                    rates = await get_exchange_for_days()
                    response = f'Current exchange rates:\n{rates}'

                await websocket.send(response)

async def main(days: int, currencies: List[str]):
    api_client = Currency_API_Client()
    currency_service = CurrencyService(api_client)
    results = await currency_service.get_exchange_rates_for_days(days, currencies)
    for result in results:
        print(result)

if __name__ == '__main__':

    star_server = websockets.serve(websockets_handler, 'localhost', 6789)

    asyncio.get_event_loop().run_until_complete(star_server)
    asyncio.get_event_loop().run_forever()

    if len(sys.argv) < 2:
        print('Usage: pyhton main.py <days> <currency>')
        sys.exit(1)
    
    days = int(sys.argv[1])

    if days >10:
        print('You can only fetch data up to 10 days.')
        sys.exit(1)
    currencies = sys.argv[2:] if len(sys.argv) > 2 else ['USD','EUR']

    asyncio.run(main(days, currencies))
