from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By

from cs50 import SQL

import requests
import os
import logging
from urllib import request, error
from time import sleep


def start_webdriver():
    """When you're running, it's probably on a Ubuntu Linux machine. In those situations, you install software using apt. Since you can't install Chrome with apt, you'll install Chromium instead, the open-source version of Chrome. Works the same, just opens a little differently."""

    # Configure options
    options = Options()
    arguments = [
        "--headless",
        "--disable-gpu",
        "--window-size=1920,1200",
        "--ignore-certificate-errors",
        "--disable-extensions",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ]
    for argument in arguments:
        options.add_argument(argument)

    # Creating the driver
    chromium_service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chromium_service, options=options)
    driver.implicitly_wait(10)  # seconds
    return driver


def get_outage_data(accounts):
    driver = start_webdriver()

    # Go to website
    driver.get("https://cebcare.ceb.lk/Incognito/OutageMap")

    # Get date
    date = driver.find_element(By.XPATH, '//div[@id="calendar"]/div/div/h2').text
    date = date.capitalize()

    for account in accounts:
        logging.basicConfig(filename="log.log", level=logging.INFO)
        # Go to website
        driver.get("https://cebcare.ceb.lk/Incognito/OutageMap")
        # Select outage calender from dropdown
        outage_calender = driver.find_element(
            By.XPATH, '//select[@id="choice"]/option[text()="Outage Calendar"]'
        )
        # Select Account info text field
        account_num = driver.find_element(By.ID, "acctNo")
        # Select submit button
        submit_btn = driver.find_element(By.XPATH, '//button[@id="btnSearch"]')

        outage_calender.click()
        account_num.send_keys(account["ceb_account"])
        submit_btn.click()

        # If invalid account warning
        if driver.find_elements(By.XPATH, '//h2[@id="swal2-title"]'):
            account["schedule"] = "invalid_ceb_account"
            # Go to the next account
            driver.quit()
            logging.info(
                f"account: {account['ceb_account']} , date: {date} ERROR: invalid_ceb_account"
            )
            continue

        # Get outage time elements
        powercuts = driver.find_elements(By.CLASS_NAME, "fc-start")

        schedule = []
        for powercut in powercuts:
            time = powercut.find_element(By.TAG_NAME, "span").text
            times = time.split(" - ")

            schedule.append({"start": times[0], "end": times[1]})
        account["schedule"] = schedule

        if not date and not schedule:
            print("No data recived")
            logging.info(
                f"account: {account['ceb_account']} , date: {date} schedule: No data"
            )
            continue
        sleep(5)

    driver.quit()
    return date, accounts


def create_messege_object(date, phone, schedule):
    messege_object = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "template",
        "template": {
            "name": "2_powercuts",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": date},
                    ],
                }
            ],
        },
    }
    if not schedule:
        messege_object["template"]["name"] = "no_power_cuts"
        return messege_object
    elif schedule == "invalid_ceb_account":
        messege_object["template"]["name"] = schedule
        return messege_object

    if len(schedule) == 1:
        messege_object["template"]["name"] = "1_power_cut"
    elif len(schedule) == 2:
        messege_object["template"]["name"] = "2_powercuts"
    elif len(schedule) == 3:
        messege_object["template"]["name"] = "3_power_cuts"
    elif len(schedule) == 4:
        messege_object["template"]["name"] = "4_power_cuts"

    for session in schedule:
        messege_object["template"]["components"][0]["parameters"].append(
            {"type": "text", "text": session["start"]}
        )
        messege_object["template"]["components"][0]["parameters"].append(
            {"type": "text", "text": session["end"]}
        )
    return messege_object


def send_messege(messege_object):

    access_token = os.environ.get("whatsapp_access_token")
    phone_id = os.environ.get("whatsapp_phone_id")
    url = f"https://graph.facebook.com/v15.0/{phone_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    result = requests.post(url, headers=headers, json=messege_object)
    print(result)


def wait_for_internet_connection():
    while True:
        try:
            request.urlopen("http://www.google.com", timeout=2)
            print("connected")
            return
        except error.URLError:
            print("waiting for connection...")
            sleep(20)


def main():
    # check API keys

    if not os.environ.get("whatsapp_access_token") or not os.environ.get(
        "whatsapp_phone_id"
    ):
        raise RuntimeError("API_KEY not set")

    # Wait for internet connection
    wait_for_internet_connection()
    # Configure CS50 Library to use SQLite database
    db = SQL("sqlite:///powercut_bot.db")
    # Select all unique accounts from db
    accounts = db.execute("SELECT DISTINCT ceb_account FROM users")
    # Scrape outage data for all DISTINCT accounts
    date, outage_data = get_outage_data(accounts)
    # Select all user phone numbers and relevent ceb accounts from db

    for account in outage_data:
        users = db.execute(
            "SELECT phone FROM users WHERE ceb_account = ?", account["ceb_account"]
        )
        # Send messege
        for user in users:
            # Create graph api objects for each user
            json_object = create_messege_object(
                date, user["phone"], account["schedule"]
            )
            # Send messeges to each user
            send_messege(json_object)
            # print(json_object)
            # print()


if __name__ == "__main__":
    main()
