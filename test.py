import nb_log
import asyncio

from async_pool_executor import AsyncPoolExecutor


async def async_f(x):
    await asyncio.sleep(2)
    print(x)


if __name__ == '__main__':
    """
    使用asyncio异步池实现10并发，可以任意时候动态追加任务到loop循环里面。
    """

    pool = AsyncPoolExecutor(10)
    for i in range(100):
        pool.submit(async_f, i)



    """
    如果没有异步池的帮助，代码要完成10并发有多复杂，写法太难了。
    
    下面这个还没支持动态向loop添加asyncio的协程任务，如果要动态随时追加任务，下面的run_until_complete就不合适。
    要引入asyncio queue解耦生产和消费
    或者 使用 run_coroutine_threadsafe，例子可以见 https://blog.csdn.net/whatday/article/details/106886811 ，里面的写法复杂到吓人。
    """

    sem = asyncio.Semaphore(10)
    async def fun_with_semaphore(x):
        async with sem:
            await async_f(x)
    tasks = []
    for i in range(100):
        tasks.append(asyncio.ensure_future(fun_with_semaphore(i)))
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
    
    
