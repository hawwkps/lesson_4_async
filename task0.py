"""Задание 0. Разминка-ловушка «Почему не быстрее?»
Замеры:
  slow: 13.03s
  fast: 3.04s

В slow_main каждый await fetch(...) внутри цикла for дожидается завершения запроса, прежде чем начнётся следующий. 
В loop одновременно существует только одна ожидающая задача, поэтому ожидания сети не перекрываются, и общее время равно сумме времён всех запросов. 
В fast_main все корутины передаются в asyncio.gather, оборачиваются в таски и запускаются конкурентно: 
пока одна ждёт ответ, loop обрабатывает остальные. Ускорение около 4x.
Во всех AsyncClient указан follow_redirects=True: иначе httpx не идёт по 302-редиректам picsum и «скачивает» не картинки.
"""



import asyncio
import time

import httpx

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code


async def slow_main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        for url in URLS:
            await fetch(client, url)


async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True, timeout = 10) as client:
        tasks = [fetch(client, url) for url in URLS]
        results = await asyncio.gather(*tasks)


# Запуск и замер — добавь в конец файла:
if __name__ == "__main__":
    timed("slow ", lambda: asyncio.run(slow_main()))
    timed("fast ", lambda: asyncio.run(fast_main()))

# lambda нужна, чтобы запуск произошёл ВНУТРИ timed: если написать
# timed("slow ", asyncio.run(slow_main())), корутина выполнится ещё
# до начала замера, и timed получит уже готовый результат.