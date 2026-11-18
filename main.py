import asyncio
import json
from datetime import datetime

import aiohttp

BRAND_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/GetMakesForVehicleType/car?format=json" #марки
CHARACTERISTICS_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMake/honda?format=json" #модели

SEMAPHORE = asyncio.Semaphore(3)


async def fetch_data(url: str, session: aiohttp.ClientSession):
    """Загружает JSON по URL. Возвращает dict или None при ошибке."""
    async with SEMAPHORE:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json() #парс
                print(f"Ошибка {response.status} при запросе {url}")
        except asyncio.TimeoutError: 
            print(f"Таймаут при запросе {url}")
        except aiohttp.ClientError as e:
            print(f"Сетевая ошибка: {e} при запросе {url}")
        except Exception as e:
            print(f"Ошибка: {e} при запросе {url}")
        return None


async def get_car_data(session: aiohttp.ClientSession) -> dict:
    brand_data, char_data = await asyncio.gather(
        fetch_data(BRAND_URL, session),
        fetch_data(CHARACTERISTICS_URL, session),
    )
    return {
        "brand": brand_data,
        "characteristics": char_data,
        "timestamp": datetime.now().isoformat(),
    }


def save_data(data: dict, filename: str = "cars_data.json") -> None:
    """Синхронно сохраняет данные в JSON-файл."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        while True:
            data = await get_car_data(session)

            # Проверяем, что хотя бы один запрос вернул данные
            if data["brand"] or data["characteristics"]:
                save_data(data)

                brands_count = data["brand"].get("Count", 0) if data["brand"] else 0
                models_count = (
                    data["characteristics"].get("Count", 0)
                    if data["characteristics"]
                    else 0
                )

                print(
                    f"[{datetime.now():%H:%M:%S}] Данные сохранены! "
                    f"Получено марок: {brands_count}, моделей: {models_count}"
                )
            else:
                print(f"[{datetime.now():%H:%M:%S}] Данные не получены, пропуск сохранения.")

            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())