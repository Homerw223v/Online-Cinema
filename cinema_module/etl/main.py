import logging

from dotenv import load_dotenv

from etl import ETLProcess
from settings import AppSettings, adapters

if __name__ == "__main__":
    load_dotenv()

    app_settings = AppSettings()
    logging.basicConfig(**app_settings.logging.as_dict())
    etl = ETLProcess(app_settings)

    etl.run(adapters)
