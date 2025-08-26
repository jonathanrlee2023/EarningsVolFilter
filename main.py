import os
from dotenv import load_dotenv
import schwabdev
from earnings import write_upcoming_earnings_symbols


if __name__ == "__main__":
    load_dotenv()  # loads variables from .env into environment

    appKey = os.getenv("appKey")
    appSecret = os.getenv("appSecret")
    client = schwabdev.Client(app_key=appKey, app_secret=appSecret)
    write_upcoming_earnings_symbols(client=client)