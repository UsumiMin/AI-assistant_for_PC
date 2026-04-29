import asyncio
import json
import logging
from collections.abc import AsyncIterable, Callable
from contextlib import suppress

import websockets

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    force=True,
)

logger = logging.getLogger(__name__)

HOST = '127.0.0.1'
PORT = 8080


class MessageSender:
    def __init__(
        self,
        connection: websockets.ServerConnection,
        message_iter: AsyncIterable[str | bytes],
    ) -> None:
        self._connection = connection
        self._message_iter = message_iter

    async def __call__(self) -> None:
        async for msg in self._message_iter:
            await self._connection.send(msg)


class WebsocketConnectionHandler:
    def __init__(
        self,
        sender_factory: Callable[[websockets.ServerConnection], MessageSender],
    ) -> None:
        self._sender_factory = sender_factory
        self._active_connection: websockets.ServerConnection | None = None

    async def __call__(self, connection: websockets.ServerConnection) -> None:
        sender_task: asyncio.Task[None] | None = None

        try:
            if self._active_connection is not None:
                await connection.close(reason='Server connection limit')
                return

            self._active_connection = connection

            sender: MessageSender = self._sender_factory(connection)

            sender_task = asyncio.create_task(sender())

            await connection.wait_closed()

        except websockets.ConnectionClosedError as exc:
            logger.exception('Connection closed with error', exc_info=exc)

        except websockets.ConnectionClosedOK:
            pass

        finally:
            logger.info(
                'Connection id=%(id)s closed with code=%(code)s and reason=%(reason)s',
                {
                    'id': connection.id,
                    'code': connection.close_code,
                    'reason': f'"{connection.close_reason}"',
                },
            )

            if sender_task:
                if not sender_task.done():
                    sender_task.cancel()

                with suppress(asyncio.CancelledError):
                    await sender_task

            self._active_connection = None


def message_sender_factory(connection: websockets.ServerConnection) -> MessageSender:

    async def message_gen(delay: float = 5) -> AsyncIterable[str]:
        while True:
            yield json.dumps({'action': 'smile'})
            await asyncio.sleep(delay)

    return MessageSender(connection, message_gen(delay=5))


async def main() -> None:
    async with websockets.serve(
        handler=WebsocketConnectionHandler(sender_factory=message_sender_factory),
        host=HOST,
        port=PORT,
        ping_interval=None,
        ping_timeout=None,
    ) as server:
        await server.wait_closed()
        logger.info('Closing server...')


if __name__ == '__main__':
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info('Shutting down...')

    except Exception as exc:
        logger.exception('Unexpected error', exc_info=exc)