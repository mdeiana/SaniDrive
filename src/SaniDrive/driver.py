"""
Defines variables that store URLs and DOM object names and provides routines
to navigate the CUP website and extract information from it using Selenium.
"""

from util import backline, _fail

import os
import sys
from time import sleep
from threading import Timer
from argparse import Namespace
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException as SERE
from selenium.common.exceptions import ElementClickInterceptedException as ECI

login_page = 'https://cupweb.sardegnasalute.it/web/guest/ricetta-elettronica?'
id_cf = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:CFInput'
id_nre = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:nreInput0'
name_button_submit = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:nreButton_button'
name_button_proceed = '_ricettaelettronica_WAR_cupprenotazione_:navigation-prestazioni-under:prestazioni-nextButton-under__button'
class_button_cookies = '.js-cookieBarAccept'
name_button_expand_list = '_ricettaelettronica_WAR_cupprenotazione_:appuntamentiForm:_t439_button'
name_class_appointment = 'appuntamento'

class RefreshTimer:
    """
    Custom wrapper for threading.Timer class.
    
    It's used when precise timing isn't needed by checking if the 
    timer has finished at any point by evaluating is_due.

    Starts on instancing, can be reset by further calling start() method on
    same object, but not if that object's timer hasn't finished yet.

    Attributes
    ----------
    is_due : bool
        False if the timer is still ticking, True if it's expired.

    Methods
    -------
    set_interval(interval)
        Change the length of the interval the timer will wait for
        the next time it's reset with start()
    start()
        Restart the timer with the previously set interval

    Notes
    -----
    At the moment, this class is not used. It was required when a different
    strategy to crawl the website was being used, but it turned out to be
    ineffective and another approach was chosen.

    The class exists nonetheless as changes to the website may make it relevant
    again in the future.
    """
    def __init__(self, interval):
        # Provide an interval to wait for
        self.is_due = True
        self.interval = interval
        self.start()

    def _callback(self):
        self.is_due = True

    def set_interval(self, interval):
        # Change interval
        self.interval = interval

    def start(self):
        if self.is_due:
            self.is_due = False
            Timer(self.interval, self._callback).start()

def init_driver(path: str, visible: bool) -> WebDriver:
    """
    Create a new WebDriver instance with the correct parameters specified
    by the user from CLI and return it.

    Parameters
    ----------
    args : Namespace
        The Namespace object produced by argparse.

    Returns
    -------
    WebDriver
        The instance of the Selenium ChromeDriver.
    """
    print("Inizializzazione ChromeDriver... ", end='') # 33 characters in line
    sys.stdout.flush()
    try:
        chrome_options = Options()
        #chrome_service = Service()

        if not visible:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument(f'--executable_path={path}')
        #chrome_service.log_output = os.path.abspath(args.logFile)
        # chrome_service isn't included as the second argument because
        # Selenium bugs out if it is as of version 4.20.0
        driver = webdriver.Chrome(chrome_options)
        backline(1)
        print("\x1b[1A\x1b[33Cfatto.")
        sys.stdout.flush()
    except Exception as e:
        print("non riuscita.\nQualcosa e' andato storto. Assicurati di aver "+
            "scaricato la giusta versione di ChromeDriver. La puoi trovare "+
            "qui: https://googlechromelabs.github.io/chrome-for-testing/ \n"+
            "La versione deve essere la stessa del browser Chrome, che puoi "+
            "trovare andando alla pagina chrome://version")
        #sys.exit(1)
        raise e
    return driver

def get_appointments_page(driver: WebDriver, cf: str, nre: str) -> None:
    """
    Core script that reaches the login page, navigates to where the list
    of appointments is given and extracts them into a list of objects
    with sanitised text fields.
    Unfortunately, the website's list of apointments is generated anew
    only by logging in again, so this function has to be re-run for every
    cycle update.

    Parameters
    ----------
    driver : WebDriver
        The WebDriver instance that's been initialized by `init_driver`
    cf : str, nre : str
        The credentials to be inserted in the page's input fields
    """
    driver.get(login_page)

    # get the damn cookie banner out the way so it doesn't break stuff
    print("Rimozione cookie banner... ", end='')
    sys.stdout.flush()
    try:
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, class_button_cookies))
        )
        button_cookies = driver.find_element(By.CSS_SELECTOR, class_button_cookies)
        button_cookies.click()
        print("fatto.")
    except TimeoutException:
        _fail(reason='layout')
    sleep(1)

    # get input fields and submit button
    print("Locazione input fields... ", end='')
    sys.stdout.flush()
    try:
        field_cf = driver.find_element(By.ID, id_cf)
        field_nre = driver.find_element(By.ID, id_nre)
        button_submit = driver.find_element(By.NAME, name_button_submit)
        print("fatto.")
    except:
        _fail(reason='layout')
    
    # input data in fields and proceed
    print("Inserimento credenziali... ", end='')
    sys.stdout.flush()
    try:
        field_cf.send_keys(cf.strip())
        field_nre.send_keys(nre.strip())
        button_submit.click()
        print("fatto.")
    except:
        print("non riuscito.\nCrea una nuova prescrizione ed assicurati che "+
            "le credenziali siano corrette.")
        sys.exit(1)

    # second page is useless, just wait for loading and proceed
    try:
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.NAME, name_button_proceed))
        )
        button_proceed = driver.find_element(By.NAME, name_button_proceed)
        button_proceed.click()
    except:
        _fail(reason='layout')
    return

def expand_list(driver: WebDriver):
    """
    Instructs driver to click the button that loads all appointments
    
    Parameters
    ----------
    driver : WebDriver
        The driver, which must already be on the correct page
    """
    print("Espansione lista appuntamenti... ", end='')
    sys.stdout.flush()
    retries = 0; retry = True

    # unfortunately button names are dynamically assigned so we have to
    # get every button and click the one that has text = 'Altre disponibilità'
    while retry:
        try:
            buttons = driver.find_elements(By.XPATH, './/button')
            for b in buttons:
                if b.text == 'Altre disponibilità':
                    b.click()
                    retry = False
                    print('fatto.')
                    sys.stdout.flush()
            sleep(2)
        except ECI:
            driver.execute_script("window.scrollBy(0, -200);")
            sleep(0.2)
            pass
        except SERE:
            retries += 1
            if retries >= 5:
                _fail(reason='session', masculine=False)
        except Exception:
            _fail(reason='layout', masculine=False)
    return

