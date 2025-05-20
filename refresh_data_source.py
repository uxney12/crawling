import os
import time
import re
import random
import requests
from datetime import datetime
import pandas as pd
import zipfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import json
import csv

##### CHẶN THÔNG BÁO #####

options = Options()
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
prefs = {
    "credentials_enable_service": False, 
    "profile.password_manager_enabled": False, 
}
options.add_experimental_option("prefs", prefs)


web_url = "https://public.tableau.com/app/profile/yen.le2602/viz/automation_17425499286520/TNGSSNPHM"
driver = webdriver.Chrome(options=options)
driver.maximize_window()
driver.get(web_url)

time.sleep(5)

login = driver.find_element(By.CSS_SELECTOR, "button._signIn_1jkmy_149")
actions = ActionChains(driver)
actions.move_to_element(login).click().perform()

# driver.switch_to.window(driver.window_handles[-1])
time.sleep(5)

email_input = driver.find_element(By.ID, "email")
email_input.send_keys("211124029145@due.udn.vn")

password_input = driver.find_element(By.ID, "password")
password_input.send_keys("Lethikimyen12112003@")

time.sleep(2)

login_button = driver.find_element(By.CSS_SELECTOR, "button.cta.cta--secondary")
login_button.click()

time.sleep(10)

refresh_button = driver.find_element(By.CSS_SELECTOR, "button._actionButton_bx5nk_99")
actions.move_to_element(refresh_button).click().perform()