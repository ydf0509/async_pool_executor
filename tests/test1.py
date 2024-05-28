import asyncio

from async_pool_executor import AsyncPoolExecutor



pool = AsyncPoolExecutor(100)


async def af(x,y):
    await asyncio.sleep(4)
    print(x,y)
    return (x+y)

for i in range(10):
    r = pool.submit(af,i,i*20)
    print('r:',r)