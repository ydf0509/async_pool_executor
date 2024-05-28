import asyncio
import atexit
import time
import traceback
from threading import Thread
import sys


print(sys.version_info.major)
class AsyncPoolExecutorInAsync:
    """
    使api和线程池一样，提供并发数量控制。这个是在异步函数种提交任务，不是在同步函数中提交任务。 submit 是async定义的，请注意对比区别。
    """

    def __init__(self, size, loop=None):
        """

        :param size: 同时并发运行的协程任务数量。
        :param loop:
        """
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        if sys.version_info.minor>=10:  # 3.10之后
            self._sem = asyncio.Semaphore(self._size,)
            self._queue = asyncio.Queue(maxsize=size, )
        else:
            self._sem = asyncio.Semaphore(self._size, loop=self.loop)
            self._queue = asyncio.Queue(maxsize=size, loop=self.loop)

    async def submit(self, func, *args, **kwargs):
        # await self._queue.put((func, args, kwargs))
        await self._sem.acquire()
        await func(*args,**kwargs)
        self._sem.release()




if __name__ == '__main__':
    import nb_log
    async def async_f(x):
        await asyncio.sleep(2)
        print(x)

    async def start():
        pool  =AsyncPoolExecutorInAsync(3)
        for i in range(30):
            print('i:',i)
            await pool.submit(async_f,i)

    asyncio.get_event_loop().run_until_complete(start())