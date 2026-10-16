"""Задание 2. Реальный I/O и обработка ошибок

Замеры:
  robust: 28.54s
  результат: ok: 20, errors: 2
    no-such-site.invalid -> ConnectError
    httpbin.org/delay/10 -> ReadTimeout

Что сделано в robust_fetch:
- Таймаут 5 с на каждый запрос (timeout=5), чтобы зависший сервер не держал
  задачу бесконечно.
- До 3 попыток с экспоненциальным backoff: паузы 1 с -> 2 с -> 4 c. Пауза делается через asyncio.sleep, а не time.sleep, чтобы не
  блокировать event loop. После последней неудачной попытки исключение пробрасывается наверх через raise.
- raise_for_status() превращает ответы 4xx/5xx в исключения, иначе они
  считались бы успехом. Ловится только httpx.HTTPError, а не любой Exception,
  чтобы не скрыть собственные ошибки в коде.

В robust_main задачи запускаются через asyncio.gather(..., return_exceptions=True):
исключение не вылетает наружу, а попадает в список результатов на место
значения. Затем результаты разделяются на успешные и ошибки, и функция
возвращает кортеж (результаты, ошибки).

Конкурентность:
Все 22 URL обрабатываются одновременно, поэтому общее время определяется
самым долгим из них (httpbin.org/delay/10), а не суммой по всем адресам.
"""


import asyncio
import time

import httpx

MAX_ATTEMPTS = 3
TIMEOUT = 5

# 20 разных картинок (у каждой свой номер в адресе) — ответы достаточно
# «тяжёлые», чтобы разница между sync и async была хорошо видна

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]
BAD_URLS = [
    "https://no-such-site.invalid",
    "https://httpbin.org/delay/10",
]
ALL_URLS = URLS + BAD_URLS


def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


async def robust_fetch(client: httpx.AsyncClient, url: str) -> int:
    delay = 1
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.status_code
        except httpx.HTTPError:
            if attempt == MAX_ATTEMPTS:
                raise
            await asyncio.sleep(delay)
            delay *= 2




async def robust_main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=TIMEOUT) as client:
        outcomes = await asyncio.gather(
            *(robust_fetch(client, url) for url in ALL_URLS),
            return_exceptions=True,
        )

    results = []
    errors = []
    for url, outcome in zip(ALL_URLS, outcomes):
        if isinstance(outcome, Exception):
            errors.append((url, repr(outcome)))
        else:
            results.append(outcome)
    return results, errors
    

def run():
    results, errors = asyncio.run(robust_main())
    print(f"ok: {len(results)}, errors: {len(errors)}")
    for url, err in errors:
        print(" ", url, err)


if __name__ == "__main__":
    timed("robust", run)

# Битые адреса для проверки — добавь их к URLS:
# "https://no-such-site.invalid" — домена не существует, упадёт сразу
# "https://httpbin.org/delay/10" — отвечает 10 секунд, должен сработать таймаут