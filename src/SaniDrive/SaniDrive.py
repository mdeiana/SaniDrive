import os
import sys
import json
import argparse
from argparse import Namespace
from time import sleep
from threading import Timer
from plyer import notification
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException as ECI
from selenium.common.exceptions import StaleElementReferenceException as SERE

# Static Parameters
id_cf = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:CFInput'
id_nre = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:nreInput0'
name_button_submit = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:nreButton_button'
name_button_proceed = '_ricettaelettronica_WAR_cupprenotazione_:navigation-prestazioni-under:prestazioni-nextButton-under__button'
class_button_cookies = '.js-cookieBarAccept'
name_button_expand_list = '_ricettaelettronica_WAR_cupprenotazione_:appuntamentiForm:_t439_button'
name_class_appointment = 'appuntamento'

# Global Variables
list_reload_interval = 30
button_timer = 10
button_retries = 10

month = {
    'Gennaio':1, 'Febbraio':2, 'Marzo':3, 'Aprile':4, 'Maggio':5, 'Giugno':6,
    'Luglio':7, 'Agosto':8, 'Settembre':9, 'Ottobre':10, 'Novembre':11, 'Dicembre':12
}

# Exceptions
class FileEmptyError(Exception):
    pass

# Classes
class Appointment:
    def __init__(self, place: str, date: str, time: str, notes: str):
        self.place = place
        self.date = date
        self.time = time
        self.notes = notes

    def __str__(self):
        """Returns appointment information in readable string form"""
        # set up proper spacing
        if len(self.date) <= 22:
            date = self.date + '\t\t'
        else:
            date = self.date + '\t'
        time = "\t".join([date, self.time])
        return "\t".join([time, self.place, self.notes])
    
    def __eq__(self, other: 'Appointment'):
        if self.__dict__ == other.__dict__:
            return True
        else: return False

    def is_sooner_than(self, other: 'Appointment'):
        # sanitize inputs
        tokens = self.date.split()
        this_hour = int(self.time.replace(':', ''))
        this_day = tokens[1]; this_month = month[tokens[2]]; this_year = int(tokens[3])

        tokens = other.date.split()
        other_hour = int(other.time.replace(':', ''))
        other_day = tokens[1]; other_month = month[tokens[2]]; other_year = int(tokens[3])

        # compare
        if this_year > other_year:
            return False
        if this_year < other_year:
            return True
        if this_year == other_year:
            if this_month > other_month:
                return False
            if this_month < other_month:
                return True
            if this_month == other_month:
                if this_day > other_day:
                    return False
                if this_day < other_day:
                    return True
                if this_day == other_day:
                    if this_hour >= other_hour:
                        return False

        return True

class Prescription:
    def __init__(self, cf: str, nre: str, name: str, note: str):
        #self.appointments: Appointment = []
        self.cf = cf
        self.nre = nre
        self.name = name
        self.note = note

    def __str__(self) -> str:
        return "\t".join([self.cf, self.nre, self.name, self.note])
    
    def __eq__(self, other: 'Prescription') -> bool:
        return self.__dict__ == other.__dict__
    
    def get_creds(self) -> tuple[str, str]:
        return self.cf, self.nre

class RefreshTimer:
    """
    Custom wrapper for threading.Timer class. Starts on instancing,
    can be reset by further calling start() method on same object,
    but not if that object's timer hasn't finished yet.
    
    It's used when precise timing isn't needed by checking if the 
    timer has finished at any point by evaluating is_due.

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

# Functions
def send_notif(appnt: Appointment) -> None:
    """Send desktop notification with appointment information"""
    notification.notify(
            title='SaniDrive ha trovato qualcosa!',
            message=appnt.date + ' ' + appnt.place,
            app_name='SaniDrive',
            app_icon='',
            timeout=30,
            ticker='Strike!',
        )
    return

def init_driver(args: Namespace) -> WebDriver:
    """
    Create a new WebDriver instance with the correct parameters specified
    by the user from CLI and return it. This unfortunately needs to be done
    multiple times because the website freaks out if all context isn't
    completely reset when re-visiting the login page.
    MAKE SURE the previous instance of the driver has been killed with
    driver.quit()

    Parameters:
        args (Namespace): The Namespace object produced by argparse
    """
    chrome_options = Options()
    chrome_service = Service()

    if not args.visible:
        chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument(f'--executable_path={args.driverFile}')
    chrome_service.log_output = os.path.abspath(args.logFile)
    # chrome_service isn't included as the second argument because Selenium bugs out
    driver = webdriver.Chrome(chrome_options)
    backline(1)
    return driver

def get_appointments_page(driver: webdriver, cf: str, nre: str):
    """
    Core script that reaches the login page, navigates to where the list
    of appointments is given and extracts them into a list of objects
    with sanitised text fields.
    Unfortunately, the website's list of apointments is generated anew
    only by logging in again, so this function has to be re-run for every
    cycle update.

    
    """
    driver.get("https://cupweb.sardegnasalute.it/web/guest/ricetta-elettronica?")

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
        fail()
    sleep(2)

    # get input fields and submit button
    print("Locazione input fields... ", end='')
    sys.stdout.flush()
    try:
        field_cf = driver.find_element(By.ID, id_cf)
        field_nre = driver.find_element(By.ID, id_nre)
        button_submit = driver.find_element(By.NAME, name_button_submit)
        print("fatto.")
    except:
        fail()
    
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
        fail()

    return

def expand_list(driver: webdriver):
    print("Espansione lista appuntamenti... ", end='')
    sys.stdout.flush()
    retries = 1; retry = True

    # unfortnuately we have to do a hacky workaround due to navigation issues:
    # get every button, click the one that has text = Altre disponibilità
    while retry:
        try:
            sleep(button_timer)
            buttons = driver.find_elements(By.XPATH, './/button')

            for b in buttons:
                if b.text == 'Altre disponibilità':
                    b.click()
                    retry = False
                    print('fatto.')
                    sys.stdout.flush()
            if retry:
                retries += 1
                print('\x1b[2K\r', end='') # clear line, we'll reprint it
                print("Espansione lista appuntamenti... ", end='')
                print(f'bottone non trovato. Tentativo {retries}... ', end='')
                sys.stdout.flush()
        except ECI:
            driver.execute_script("window.scrollBy(0, -200);")
            sleep(0.2)
            pass
        except SERE:
            retries += 1
            sleep(button_timer)
            pass
        except Exception:
            print("fallita.\nProbabilmente il layout della pagina e' cambiato, "+
            "per favore avvisami con email a michele.deiana.dev@gmail.com")
            sys.exit(1)
    return

def parse_arguments():
    parser = argparse.ArgumentParser(
                prog="SaniDrive",
                description="Tieni traccia e avverti dei posti liberi per una prenotazione al CUP automaticamente",
                epilog='SaniDrive by Michele Deiana (github.com/mdeiana). Governo pls fix sanita\'')
    parser.add_argument('--file', '-f', dest='credFile', default='data/credenziali.json',
                        help=f'Specifica il percorso del file con le credenziali. E\' bene usare un percorso assoluto '+
                        'per garantire l\'uso del file corretto. Il percorso di default e\' "data/credenziali.json", '+
                        'relativamente alla directory da cui e\' eseguito SaniDrive.')
    parser.add_argument('--driver', '-d', dest='driverFile', default='driver/chromedriver.exe',
                        help='Specifica il percorso dell\'eseguibile di ChromeDriver. E\' bene usare un percorso assoluto '+
                        'per garantire l\'uso del file corretto. Il percorso di default e\' "driver/chromedriver.exe", '+
                        'relativamente alla directory da cui e\' eseguito SaniDrive. Scarica la versione di ChromeDriver '+
                        'che combacia a quella del tuo browser Chrome da https://googlechromelabs.github.io/chrome-for-testing/')
    parser.add_argument('--visibile', '--visible', '-v', dest='visible', default=False, action='store_true', help=
                        'Di default, il driver e\' eseguito in modalita\' headless, ovvero la finestra del browser '+
                        'e\' nascosta per evitare di interagirci accidentalmente. Specificare questa opzione la rende visible.')
    parser.add_argument('--log', '-l', dest='logFile', default=None, action='store', help='Specifica il percorso '+
                        'del file in cui salvare il log di ChromeDriver. Se il parametro non e\' specificato, i log '+
                        'non sono salvati. Questo parametro e\' correntemente disabilitato per un bug in Selenium.')
    args = parser.parse_args()
    return args

def backline(n):
    for i in range(n):
        print('\x1b[F\x1b[2K', end='')
        sys.stdout.flush()
    return

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')
    return

def divider(*args: str):
    print("=================================================="+
          "==================================================")
    for arg in args:
        print(arg, end='')
    return

def fail():
    print("non riuscito.\nProbabilmente il layout della pagina e' cambiato, "+
          "per favore avvisami con email a michele.deiana.dev@gmail.com")
    sys.exit(1)

def pop_prescriptions(path: str) -> list[Prescription]:
    """
    Populate list of prescription objects with attributes
    as read from .json file and return the list.

        Parameters:
                path (str): The path to the .json file
    """
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            # determine if file is empty
            f.seek(0, os.SEEK_END)
            end = f.tell()
            if end == 0:
                raise FileEmptyError
            else:
                f.seek(0, 0)
    except Exception as e:
        raise e
    
    prescriptions = []
    for cf, dict in data.items():
        for nre, meta in dict.items():
            name = meta['nome']
            note = meta['nota']
            new_pre = Prescription(cf, nre, name, note)
            prescriptions.append(new_pre)

    return prescriptions

def add_prescription():
    return

def main():
    cls()
    args = parse_arguments()
    credPath = os.path.abspath(args.credFile)

    print("Lettura impegnative... ", end='')
    try:
        prescriptions = pop_prescriptions(credPath)
        print("fatto.")
    except FileNotFoundError:
        print(f"il file {credPath} non esiste. Inserisci un'impegnativa nuova "+
              f"al passaggio successivo per crearlo e salvarla.")
        pass
    except FileEmptyError:
        print(f"il file {credPath} e' vuoto. Inserisci un'impegnativa nuova "+
              f"al passaggio successivo per salvarla nel file.")
        pass
    except json.decoder.JSONDecodeError:
        print(f"non riuscita.\nIl file {credPath} non sembra essere json valido.")
        sys.exit(1)
    except KeyError:
        print(f"non riuscita.\nIl file specificato non e' nel formato corretto "+
              f"oppure e' corrotto. Per favore specificane uno nuovo o vuoto.")
        sys.exit(1)
    except Exception:
        print("non riuscita.\nQualcosa e' andato storto.")
        sys.exit(1)
    
    # print prescriptions and choose which to track
    print("\nNumero\t Codice fiscale\t\tNRE\t\tNome\t\t\tNota")
    for i, prescr in enumerate(prescriptions):
        print(i+1, "\t", prescr)
    print("")

    c = int(input(f"Seleziona un'impegnativa (1 - {i+1}): ")) - 1
    backline(1)

    # initialize driver, delete some nasty output by driver to stdout
    print("Inizializzazione ChromeDriver... ", end='') # 33 characters in line
    sys.stdout.flush()
    try:
        driver = init_driver(args)
        print("\x1b[1A\x1b[33Cfatto.")
        sys.stdout.flush()
    except:
        print("non riuscita.\nQualcosa e' andato storto. Assicurati di aver "+
                "scaricato la giusta versione di ChromeDriver. La puoi trovare qui: "+
                "https://googlechromelabs.github.io/chrome-for-testing/ \n"+
                "La versione deve essere la stessa del browser Chrome, che puoi "+
                "trovare andando alla pagina chrome://version")
        sys.exit(1)

    # get the page with the list of all the appointments and expand the list
    get_appointments_page(driver, *prescriptions[c].get_creds())
    expand_list(driver)
    
    print(f"\nRaggiunta la pagina. Aggiornamento ogni {list_reload_interval} secondi.")    
    print("Caricamento lista appuntamenti... ")

    # main loop
    appointments : list[Appointment] = [] # these are the sanitised appointments from the class
    old_appointments : list[Appointment] = [] # expensive but easy way to keep track of changes
    appnts = [] # these are the appointment webelements from the driver, bad name mb
    change_counter = -1
    refresh_counter = 0
    pretty = 0 # used to make change_counter display intuitively
    while True:
        sleep(10)
        """
        used to make sure the list has loaded fully before reading appointments
        this is temporary and needs to be replaced with an implicit wait method
        """
        cls()
        # print selected prescription data for sanity
        print("\nNumero\t Codice fiscale\t\tNRE\t\tNome\t\t\tNota")
        print(c+1, "\t", prescriptions[c], '\n')
        divider('\n')
        sys.stdout.flush()

        # print prescription column info
        print(f'\t\t\t\t\t\tAPPUNTAMENTI\n')
        print(f'Numero\t\t Data\t\t\t\t Ora\t\t\tVia')
        sys.stdout.flush()
        
        # get appointment objects and discard the first because it's repeated later
        appnts = driver.find_elements(By.CLASS_NAME, name_class_appointment)
        appnts = appnts[1:]

        for appnt in appnts:
            # extract information
            time_obj = appnt.find_element(By.CLASS_NAME, 'captionAppointment-dateApp')
            time_fields = time_obj.find_elements(By.XPATH, './*')
            place_obj = appnt.find_element(By.CLASS_NAME, 'unita-address')
            place = place_obj.text
            # note support to be added

            # store information in new instance
            appointments.append(Appointment(place, time_fields[0].text.strip(),
                                            time_fields[2].text, ''))

        # find out if something changed, send a notif and move on
        if appointments != old_appointments:
            change_counter += 1

        # store earliest found appointment separately
        try:
            if appointments[0].is_sooner_than(earliest_appointment):
                earliest_appointment = appointments[0]
                found_on_refresh = refresh_counter
                send_notif(earliest_appointment)
        except NameError:
            earliest_appointment = appointments[0]
            found_on_refresh = refresh_counter
            pass

        # print all available appointments
        if len(appointments) == 0:
            print("\t\t\tNessun appuntamento.")
            pretty = 1
        else:
            for i, a in enumerate(appointments):
                print(f"{i+1}\t", a)

        # print some statistics
        print(f"\n\t\tAppuntamento piu' vicino trovato (durante aggiornamento {found_on_refresh}):\n",
                "\t", earliest_appointment, "\n")
        print(f'\t\tAggiornamenti totali: {refresh_counter}\t\t\tCambiamenti rilevati: '+
                f'{change_counter+pretty}\n')
        divider('\n')

        # cycle data
        old_appointments = appointments
        appointments = []
        refresh_counter += 1

        # refresh
        driver.quit()
        sleep(list_reload_interval)
        print("Aggiornamento lista appuntamenti... ")
        driver = init_driver(args)
        get_appointments_page(driver, *prescriptions[c].get_creds())
        expand_list(driver)

if __name__ == "__main__":
    main()