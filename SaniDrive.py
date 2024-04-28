import sys
from time import sleep
from plyer import notification
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def fail():
    print("failed.\nPage layout must have changed. If you'd be so kind,\
          please notify me at michele.deiana.dev@gmail.com")
    sys.exit()

def main():
    # get credentials from file
    print("Getting credentials... ", end='')
    try:
        with open("credentials.txt", "r") as f:
            cf = f.readline()
            nre = f.readline()
            print("done.")
    except FileNotFoundError:
        print("failed.\nFile not found. Make sure your credentials are\
              in the file credentials.txt in the same directory as\
              SaniDrive.py, one value per line.")
        sys.exit()

    # stuff we'll need to ID the elements we'll be interacting with
    id_cf = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:CFInput'
    id_nre = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:nreInput0'
    name_button_submit = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:nreButton_button'
    name_button_proceed = '_ricettaelettronica_WAR_cupprenotazione_:navigation-prestazioni-under:prestazioni-nextButton-under__button'
    class_button_cookies = '.js-cookieBarAccept'
    name_class_appointment = 'appuntamento'

    # initialize driver
    print("Initializing ChromeDriver... ", end='')
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--log-level=3")
        #chrome_options.add_argument('--executable_path="./chromedriver.exe"')
        chrome_service = Service()
        chrome_service.log_output = './ChromeDriver_logs.txt'
        driver = webdriver.Chrome(chrome_options)
        driver.get("https://cupweb.sardegnasalute.it/web/guest/ricetta-elettronica?")
        print("done.")
    except:
        print("failed.\nSomething went wrong. Make sure you have downloaded\
              the right version of ChromeDriver. You can get it from: \
              https://googlechromelabs.github.io/chrome-for-testing/ \n\
              the version must be the same as that of your Chrome installation,\
              which you can check by going to chrome://version")
        sys.exit()

    # get the damn cookie banner out the way so it doesn't break stuff
    print("Clearing cookie banner... ", end='')
    try:
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, class_button_cookies))
        )
        button_cookies = driver.find_element(By.CSS_SELECTOR, class_button_cookies)
        button_cookies.click()
        print("done.")
    except TimeoutException:
        fail()

    sleep(2)

    # get input fields and submit button
    print("Locating input fields... ", end='')
    try:
        field_cf = driver.find_element(By.ID, id_cf)
        field_nre = driver.find_element(By.ID, id_nre)
        button_submit = driver.find_element(By.NAME, name_button_submit)
        print("done.")
    except:
        fail

    # input data in fields and proceed
    print("Inserting credentials... ", end='')
    try:
        field_cf.send_keys(cf.strip())
        field_nre.send_keys(nre.strip())
        button_submit.click()
        print("done.")
    except:
        print("failed.\nMake sure your credentials are correct, and appear\
              in the credentials.txt file one per line, and try again.")
        sys.exit()


    # second page is useless, just wait for loading and proceed
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.NAME, name_button_proceed))
    )
    button_proceed = driver.find_element(By.NAME, name_button_proceed)
    button_proceed.click()

    # get number of elements that look like appointments
    # if there are none, refresh the page and look again
    # repeat until there's something
    appnts = []
    refreshes = 1
    print("Got to the page. Checking once every 30 seconds.")
    while True:
        try:
            print(f"Check count: {refreshes}... ", end='')
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, name_class_appointment))
            )
            appnts = driver.find_elements(By.CLASS_NAME, name_class_appointment)
            break
        except TimeoutException:
            print("\r", end='')
            refreshes += 1
            driver.refresh()

    # once we find one, notify the user
    if not len(appnts) == 0:
        notification.notify(
            title='SaniDrive ha trovato qualcosa!',
            message='Sembra che ci sia un appuntamento disponibile!',
            app_name='SaniDrive',
            app_icon='',
            timeout=20,
            ticker='Strike!',
        )

    driver.quit()
    print("Possible appointment slot found! Check it out ASAP!")

if __name__ == "__main__":
    main()