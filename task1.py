"""Задание 1. Синхронно vs асинхронно

Замеры:
  sync:         65.34s
  sync+session: 12.06s
  async:         3.75s

sync складывает время всех запросов, потому что каждый ждёт предыдущий (да ещё и открывает новое соединение), 
а async с asyncio.gather перекрывает ожидания сети и переиспользует соединения клиента, поэтому он быстрее 
(около 17x, из них примерно 5x даёт Session, а ещё 3x конкурентность).
"""

import asyncio
import time

import httpx
import requests

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code


def sync_main():
    for url in URLS:
        requests.get(url, timeout = 10)  # по очереди, время складывается


def sync_session_main():
    with requests.Session() as session:
        for url in URLS:
            session.get(url, timeout=10)


async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True, timeout = 10) as client:
        tasks = [fetch(client, url) for url in URLS]
        results = await asyncio.gather(*tasks)


if __name__ == "__main__":
    timed("sync", sync_main)
    timed("sync+session", sync_session_main)
    timed("async", lambda: asyncio.run(fast_main()))