import asyncio
import websockets

async def send_exchange_command():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # Gửi lệnh "exchange 2" để lấy tỷ giá của 2 ngày gần nhất
        await websocket.send("exchange 11")
        
        # Nhận phản hồi từ server
        response = await websocket.recv()
        print(f"Received exchange rate: {response}")

asyncio.run(send_exchange_command())