from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


import requests
import os
import logging
import sys

WEB = "https://cebcare.ceb.lk/Incognito/OutageMap"
CEB_ACCOUNT = "4290195113"


def start_webdriver():
    """When you're running GitHub Actions, it's probably on a Ubuntu Linux machine. In those situations, you install software using apt. Since you can't install Chrome with apt, you'll install Chromium instead, the open-source version of Chrome. Works the same, just opens a little differently."""

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
    chromium_service = Service(
        ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
    )
    driver = webdriver.Chrome(service=chromium_service, options=options)
    driver.implicitly_wait(10)  # seconds
    return driver


def get_outage_data(driver, web):
    # Go to website
    driver.get(web)

    outage_calender = driver.find_element(
        By.XPATH, '//select[@id="choice"]/option[text()="Outage Calendar"]'
    )
    account_num = driver.find_element(By.ID, "acctNo")
    submit_btn = driver.find_element(By.XPATH, '//button[@id="btnSearch"]')

    outage_calender.click()
    account_num.send_keys(CEB_ACCOUNT)
    submit_btn.click()

    # Get outage time elements
    powercuts = driver.find_elements(By.CLASS_NAME, "fc-start")
    # Get date
    date = driver.find_element(By.XPATH, '//div[@id="calendar"]/div/div/h2').text

    schedule = []
    for powercut in powercuts:
        time = "🕔  "
        time += powercut.find_element(By.TAG_NAME, "span").text
        time += "\n"
        schedule.append(time)
    logging.basicConfig(filename="myapp.log", level=logging.INFO)
    if date and schedule:
        logging.info(f"date: {date} schedule: {schedule}")
        return date, schedule
    else:
        logging.error(f"date: {date} schedule: {schedule}")
        sys.exit()


def draft_messege_text(date, schedule):
    times = "".join(schedule)
    messege = f"*CEB powercuts: {date}* ⚠\n\n{times}\n_Data source: cebcare.ceb.lk_"
    print(messege)
    return messege


def send_messege(messege):

    url = "https://graph.facebook.com/v15.0/107954815499870/messages"
    access_token = os.environ.get("whatsapp_access_token")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    myobj = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "94773943935",
        "type": "text",
        "text": {"preview_url": False, "body": messege},
    }

    x = requests.post(url, headers=headers, json=myobj)

    print(x.text)


def main():
    driver = start_webdriver()
    date, schedule = get_outage_data(driver, WEB)
    messege = draft_messege_text(date, schedule)
    send_messege(messege)
    driver.quit()


if __name__ == "__main__":
    main()
