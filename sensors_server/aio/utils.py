import asyncio
import contextlib
import logging
import os
import sys

import aiorun

logger = logging.getLogger(__name__)

_shutdown_env_key = __name__ + 'SHUTDOWN_SIGNALLED'
_shutdown_env_val = 'abracadabra'

def shutdown_signalled():
    return os.environ.get(_shutdown_env_key) == _shutdown_env_val

def _signal_shutdown():
    os.environ[_shutdown_env_key] = _shutdown_env_val

def _shutdown_handler(loop=None):
    def get_pending_tasks():
        return [task for task in asyncio.Task.all_tasks(loop) if not task.cancelled()]

    async def wait_for_tasks(tasks):
        logger.debug('Waiting for %d tasks...', len(tasks))
        try:
            await asyncio.gather(*tasks)
            logger.debug('All awaited tasks finished')
        except asyncio.CancelledError:
            logger.debug('Got cancelled')
            raise

    _signal_shutdown()

    if loop is None:
        loop = asyncio.get_event_loop()

    for task in get_pending_tasks():
        task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        loop.run_until_complete(asyncio.shield(wait_for_tasks(get_pending_tasks())))
    with contextlib.suppress(asyncio.CancelledError):
        loop.run_until_complete(asyncio.shield(wait_for_tasks(get_pending_tasks())))
    loop.close()


def main(async_main):
    if sys.platform == 'win32':
        # need to use ProactorEventLoop to support asyncio.subprocess_exec
        # https://docs.python.org/3/library/asyncio-eventloops.html#windows
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

        # https://stackoverflow.com/questions/27480967/why-does-the-asyncios-event-loop-suppress-the-keyboardinterrupt-on-windows
        async def wakeup():
            while True:
                await asyncio.sleep(1)
        loop.create_task(wakeup())

        status = 0
        try:
            loop.run_until_complete(async_main())
        except KeyboardInterrupt:
            logger.info('Interrupted')
        except:
            status = 1
        finally:
            _shutdown_handler(loop)
            # workaround for deadlock in Thread._wait_for_tstate_lock
            os._exit(status)
    else:
        # TODO: untested
        aiorun.run(main, shutdown_handler=_shutdown_handler)
