import asyncio
import json
from collections.abc import AsyncIterable

import websockets

from actions import init_dispatcher
from MiniLM import MiniLMFunc
from server import MessageSender, WebsocketConnectionHandler
from Vosk import async_speech_to_text_gen


async def main() -> None:
    dispatcher = init_dispatcher()
    mini_lm = MiniLMFunc()

    def message_sender_factory(connection: websockets.ServerConnection) -> MessageSender:

        async def message_gen() -> AsyncIterable[str]:
            async for text in async_speech_to_text_gen():
                response = mini_lm.get_json_response(text)
                yield response
                print('\nresponse:')
                print(response)
                try:
                    dispatcher.dispatch(json.loads(response)['action'])
                except ValueError:
                    print('Unexpected action')

        return MessageSender(connection, message_gen())

    ws_server = await websockets.serve(
        handler=WebsocketConnectionHandler(sender_factory=message_sender_factory),
        host='127.0.0.1',
        port=8080,
        ping_interval=None,
        ping_timeout=None,
    )

    tasks = [
        asyncio.create_task(ws_server.wait_closed()),
    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
