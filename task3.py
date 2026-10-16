import asyncio
import hashlib
import time

# 20 разных картинок (у каждой свой номер в адресе) — ответы достаточно
# «тяжёлые», чтобы разница между sync и async была хорошо видна
URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


def heavy(body: bytes) -> str:
    # body * 1000 раздувает данные, чтобы хеш считался заметно долго
    return hashlib.sha256(body * 1000).hexdigest()


async def ticker():
    # «пульс» event loop: если точки перестали печататься — loop заблокирован
    while True:
        print(".", end="", flush=True)
        await asyncio.sleep(0.1)


async def cpu_main():
    ...  # 1) запусти ticker фоновой задачей: asyncio.create_task(ticker())
         # 2) скачай ответы и посчитай heavy «в лоб» — точки замрут
         # 3) посчитай heavy через loop.run_in_executor + ProcessPoolExecutor —
         #    точки бегут
         # 4) в конце отмени ticker через .cancel()


if __name__ == "__main__":
    # проверка обязательна: без неё ProcessPoolExecutor падает на Windows
    # и macOS — дочерние процессы заново импортируют этот файл
    timed("cpu  ", lambda: asyncio.run(cpu_main()))