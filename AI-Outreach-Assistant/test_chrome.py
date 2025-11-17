from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--start-maximized")

service = Service("chromedriver.exe")  # path to chromedriver
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://www.google.com")