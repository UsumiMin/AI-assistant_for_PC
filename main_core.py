import asyncio
import json
import logging
from collections.abc import AsyncIterable

import websockets

from actions import init_dispatcher
from MiniLM import MiniLMFunc
from server import MessageSender, WebsocketConnectionHandler
from assistent_vosk import speech_recognition_stream
from tts import say 

logger = logging.getLogger(__name__)


async def main() -> None:
    dispatcher = init_dispatcher()
    mini_lm = MiniLMFunc()

    def message_sender_factory(connection: websockets.ServerConnection) -> MessageSender:

        async def message_gen() -> AsyncIterable[str]:
            loop = asyncio.get_running_loop()
            iterator = iter(speech_recognition_stream())

            await loop.run_in_executor(None, say, "Система запущена")

            while True:
                text = await loop.run_in_executor(None, next, iterator)
                text_lower = text.lower().strip()
                
                activation_keys = ["афина", "афину", "афине"]
                is_activated = any(key in text_lower for key in activation_keys)
                
                if not is_activated:
                    continue 
                
                found_key = next(key for key in activation_keys if key in text_lower)
                clean_cmd = text_lower.replace(found_key, "").strip()
                
                logger.info('Распознано обращение к Афине: %s', text_lower)

                if not clean_cmd:
                    logger.info('Обращение по имени без конкретной команды')
                    response = json.dumps({
                        "answer": "Да, я вас слушаю?", 
                        "action": "none", 
                        "target": ""
                    }, ensure_ascii=False)

                    yield response

                    asyncio.create_task(loop.run_in_executor(None, say, "Да, я вас слушаю?"))
                else:
                    logger.info('Отправка команды в MiniLM: %s', clean_cmd)
                    response = mini_lm.get_json_response(clean_cmd)
                    
                    try:
                        parsed_response = json.loads(response)
                        answer = parsed_response.get("answer", "")
                        yield response
                        if answer:
                            tts_task = asyncio.create_task(
                                loop.run_in_executor(None, say, answer)
                            )
                        
                        action = parsed_response.get('action')
                        if action and action != 'none':
                            dispatcher.dispatch(
                                action,
                                kwargs={'target': parsed_response.get('target', '')},
                            )
                        
                        if answer:
                            await tts_task
                            
                    except Exception as e:
                        logger.error('Ошибка: %s', e)
                
                
                logger.info('Ответ отправлен в интерфейс:\n%s', response)

                try:
                    parsed_response = json.loads(response)
                    if parsed_response.get('action') and parsed_response['action'] != 'none':
                        dispatcher.dispatch(
                            parsed_response['action'],
                            kwargs={'target': parsed_response.get('target', '')},
                        )
                except (ValueError, KeyError):
                    logger.exception('Ошибка при выполнении системного действия')
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
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
        force=True,
    )

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info('Shutting down...')

    except Exception as exc:
        logger.exception('Unexpected error', exc_info=exc)
