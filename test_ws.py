import asyncio
import websockets

async def test_ws():
    url = "ws://localhost:8000/ws/relatorio_diario"
    async with websockets.connect(url) as websocket:
        print("Conectado!")
        while True:
            msg = await websocket.recv()
            print("Recebido:", msg)

asyncio.run(test_ws())