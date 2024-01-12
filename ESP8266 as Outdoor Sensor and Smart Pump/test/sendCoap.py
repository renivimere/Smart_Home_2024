import asyncio
import aiocoap
from aiocoap import Context, Message

async def coap_client():
    protocol = await Context.create_client_context()

    # Địa chỉ IP của ESP8266
    esp8266_ip = "192.168.109.201"  # Thay thế bằng địa chỉ IP thực của ESP8266

    # Gửi yêu cầu PUT để bật đèn LED
    request = Message(code=aiocoap.Code.PUT, payload=b'1')
    request.set_request_uri(f'coap://{esp8266_ip}/light')

    try:
        response = await asyncio.wait_for(protocol.request(request).response, timeout=10)

        # In ra terminal
        print(f'Response Code: {response.code}')
    except asyncio.TimeoutError:
        print('Request timed out')
    except Exception as e:
        print(f'Error: {e}')

asyncio.get_event_loop().run_until_complete(coap_client())
