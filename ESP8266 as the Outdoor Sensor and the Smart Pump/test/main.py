# main.py
import threading
import asyncio
from send_state import send
from coap_client import get

async def run_send():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    await send()

async def run_get():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    await get()

if __name__ == "__main__":
    # Tạo hai luồng và gắn hàm chạy của mỗi tệp vào từng luồng
    send_thread = threading.Thread(target=lambda: asyncio.run(run_send()))
    get_thread = threading.Thread(target=lambda: asyncio.run(run_get()))

    # Bắt đầu chạy từng luồng
    send_thread.start()
    get_thread.start()

    # Chờ đợi cả hai luồng kết thúc
    send_thread.join()
    get_thread.join()
