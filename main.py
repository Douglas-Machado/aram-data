import os
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchDriverException
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from pymongo import MongoClient
from dotenv import load_dotenv

SCROLL_PAUSE_TIME = 0.5

load_dotenv(override=True)


class AramDetails:
    db = MongoClient(os.getenv("MONGO_URL")).aramid
    def __init__(self):
        self.keys = ["rank", "name", "tier", "winrate", "pickrate", "matches"]
        self.driver = None
        self.data = []
        self.patch = ""

    def get_tierlist(self):
        self.get_default_browser()
        self.driver.get(os.getenv("ARAM_WEB_URL"))
        self.patch = self.driver.find_element(By.XPATH, '//*[@id="stats-tables-container-ID"]/div[2]/h1/div').text
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        rows = self.driver.find_elements(By.CLASS_NAME, "rt-tr")
        rows.pop(0)
        items = []
        for row in rows:
            values = row.text.split("\n")
            values[0] = int(values[0])
            values[1] = values[1].lower()
            items.append(values)

        self.driver.close()
        response_dict = [{k: v for (k, v) in zip(self.keys, infos)} for infos in items]
        self.data = response_dict

    def get_default_browser(self):
        try:
            service = Service(ChromeDriverManager().install())
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--single-process')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=options)
            self.driver = driver
            driver.set_window_size(1280, 1696)
            return
        except NoSuchDriverException as ex:
            print("chrome")
            print(ex)
    
    def insert_champions_data(self):
        collection = self.db.champions_data
        collection.delete_many({})
        count = 0
        for data in self.data:
            collection.insert_one(data)
            count += 1
        print(f"Inserted ids: {count}")

    def insert_patch_info(self):
        collection = self.db["patch_info"]
        collection.delete_many({})
        collection.insert_one({"patch": self.patch})

aram_details = AramDetails()
aram_details.get_tierlist()
aram_details.insert_champions_data()
aram_details.insert_patch_info()
