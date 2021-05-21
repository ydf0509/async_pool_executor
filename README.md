## pip install async_pool_executor



## 主要功能

```
主要功能是仿照 concurrent.futures 的线程池报的submit shutdown方法。

使得在做生产 消费 时候，无需学习烦人的异步思维写代码 ，可以直接在同步函数中 submit。
生产和消费不需要在同一个loop中，喜欢同步编程思维的人可以用这个。

async def 的函数，定义协程函数本身不难，难的是如果要并发起来执行，要搞懂以下这些概念，
以下这些概念非常多十分之复杂，asyncio的并发玩法与同步函数 + 线程池并发写法区别很大，asyncio的并发写法难度大太多。
异步要想玩的溜，用户必须精通的常用方法和对象的概念包括以下：

loop 对象
asyncio.get_event_loop 方法
asyncio.new_event_loop 方法
asyncio.set_event_loop 方法
asyncio.ensure_future  方法
asyncio.create_task 方法
asyncio.wait  方法
asyncio.gather  方法
asyncio.run_coroutine_threadsafe 方法
loop.run_in_executor 方法
run_until_complete  方法
run_forever 方法
future 对象
task  对象
corotinue 对象

```

```
上面的概念学会要比学怎么使用线程池难太多了，写法代码也更繁琐。但有了这个AsyncPoolExecutor这个包，
上面所有的概念用户都不需要学了，写起异步并发来简化了10倍。
```

```python
import asyncio

async def async_f(x):
    await asyncio.sleep(2)
    print(x)

pool = AsyncPoolExecutor(3)
for i in range(30):
    pool.submit(async_f,i)

```


## 实现代码

```python

import asyncio
import atexit
import time
import traceback
from threading import Thread


class AsyncPoolExecutor:
    """
    使api和线程池一样，最好的性能做法是submit也弄成 async def，生产和消费在同一个线程同一个loop一起运行，但会对调用链路的兼容性产生破坏，从而调用方式不兼容线程池。
    """

    def __init__(self, size, loop=None):
        """

        :param size: 同时并发运行的协程任务数量。
        :param loop:
        """
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        self._queue = asyncio.Queue(maxsize=size, loop=self.loop)
        t = Thread(target=self._start_loop_in_new_thread)
        t.setDaemon(True)  # 设置守护线程是为了有机会触发atexit，使程序自动结束，不用手动调用shutdown
        t.start()
        self._can_be_closed_flag = False
        atexit.register(self.shutdown)


    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)  # 这个 run_coroutine_threadsafe 方法也有缺点，消耗的性能巨大。
        future.result()  # 阻止过快放入，放入超过队列大小后，使submit阻塞。

    async def _produce(self, func, *args, **kwargs):
        await self._queue.put((func, args, kwargs))

    async def _consume(self):
        while True:
            func, args, kwargs = await self._queue.get()
            if func == 'stop':
                break
            try:
                await func(*args, **kwargs)
            except Exception as e:
                traceback.print_exc()

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # 这种也可以。
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(asyncio.wait([self._consume() for _ in range(self._size)], loop=self.loop))
        self._can_be_closed_flag = True

    def shutdown(self):
        for _ in range(self._size):
            self.submit('stop', )
        while not self._can_be_closed_flag:
            time.sleep(0.1)
        self.loop.close()
        print('关闭循环')


if __name__ == '__main__':
    import nb_log
    async def async_f(x):
        await asyncio.sleep(2)
        print(x)

    pool  =AsyncPoolExecutor(3)
    for i in range(30):
        pool.submit(async_f,i)
```

### 对比没使用 asyncio，如果进行10并发调度协程并实现asyncio动态追加任务，太难了。



#### 下面的例子是对比AsyncPoolExecutor 和临时手写操作loop 和task

###### 这个例子还没有实现随时动态追加协程任务，写法就已经很繁琐了。

```
如果是没有async_pool_executor，那就要手动操作 asyncio.wait/gather run_until_complete future task corotinue 这些复杂的概念。

本人热衷于致力使临时写代码简单，把复杂的东西抽象到一个通用地方，虽然是需要花时间花想法来实现这些高难度的抽象，但还是值得的。
```

```python
import nb_log
import asyncio

from async_pool_executor import AsyncPoolExecutor


async def async_f(x):
    await asyncio.sleep(2)
    print(x)


if __name__ == '__main__':
    """
    使用asyncio异步池实现10并发，可以任意时候动态追加任务到loop循环里面。写法极其简单。
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
    

```

### csdn 的 python3 异步 asyncio 动态添加任务

[csdn 的 asyncio python3 异步 asyncio 动态添加任务](https://blog.csdn.net/whatday/article/details/106886811) 

里面的写法复杂到吓人,所以需要 AsyncPoolExecutor 这个异步池来减小码农的编程难度。

```python
import asyncio
import time
 
from threading import Thread
 
 
def start_loop(loop):
    asyncio.set_event_loop(loop)
    print("start loop", time.time())
    loop.run_forever()
 
 
async def do_some_work(x):
    print('start {}'.format(x))
    await asyncio.sleep(x)
    print('Done after {}s'.format(x))
 
 
new_loop = asyncio.new_event_loop()
t = Thread(target=start_loop, args=(new_loop,))
t.start()
 
asyncio.run_coroutine_threadsafe(do_some_work(6), new_loop)
asyncio.run_coroutine_threadsafe(do_some_work(4), new_loop)
```

