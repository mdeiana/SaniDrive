import os
import sys
import json
import argparse
import requests
from time import sleep
from threading import Timer
from bs4 import BeautifulSoup
from argparse import Namespace
from plyer import notification
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException as SERE
from selenium.common.exceptions import ElementClickInterceptedException as ECI

# Version
__version__ = '1.1'

# Constant Parameters
driver_dl_page = 'https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json'
id_cf = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:CFInput'
id_nre = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:nreInput0'
name_button_submit = '_ricettaelettronica_WAR_cupprenotazione_:ePrescriptionSearchForm:nreButton_button'
name_button_proceed = '_ricettaelettronica_WAR_cupprenotazione_:navigation-prestazioni-under:prestazioni-nextButton-under__button'
class_button_cookies = '.js-cookieBarAccept'
name_button_expand_list = '_ricettaelettronica_WAR_cupprenotazione_:appuntamentiForm:_t439_button'
name_class_appointment = 'appuntamento'

line_width = 120

# Lookup Tables
MONTH = {
    'Gennaio':1, 'Febbraio':2, 'Marzo':3, 'Aprile':4, 'Maggio':5, 'Giugno':6,
    'Luglio':7, 'Agosto':8, 'Settembre':9, 'Ottobre':10, 'Novembre':11, 'Dicembre':12
}
DAYS = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}

# Exceptions
class FileEmptyError(Exception):
    pass

# Classes
class Appointment:
    """
    Class that stores information on found appointments and provides
    ways of comparing and ordering them by date

    Attributes
    ----------
    place : str
        String with place information as read from website appointment list
    date : str
        String with date information in the form 'Sabato 2 Novembre 2025'
    time : str
        String with time information in the form '14:20'
    notes : str
        String with other information as read from website (not implemented)

    Methods
    -------
    is_sooner_than
        Returns True when called from an instanced Appointment
        that is closer in time than the Appointment instance
        passed as argument
    latest
        Class method that returns an Appointment instance whose `date`
        attribute is based on the date specified from command line
        arguments to allow for date comparisons with is_sooner_than
    """
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

    def is_sooner_than(self, other: 'Appointment') -> bool:
        """
        Method that is used to determine which of two Appointment instances
        comes first in time. Returns True when the instance this is called
        from is closer in time than the Appointment instance that is passed
        as argument, or when the latter instance is empty.

        Parameters
        ----------
        other : Appointment
            The instance to compare against

        Returns
        -------
        bool
            Tells whether instance comes before in time than argument
        """
        # if we're comparing against an empty appointment, return True
        if other.date == '':
            return True

        # sanitize inputs
        tokens = self.date.split()
        this_hour = int('0'+self.time.replace(':', ''))
        this_day = tokens[1]; this_month = MONTH[tokens[2]]
        this_year = int(tokens[3])

        tokens = other.date.split()
        other_hour = int('0'+other.time.replace(':', ''))
        other_day = tokens[1]; other_month = MONTH[tokens[2]]
        other_year = int(tokens[3])

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
    
    @classmethod
    def latest(cls, date: list[str]) -> 'Appointment | None':
        """
        Generate and return Appointment class whose `date` attribute reflects
        the date passed as argument and is coherent with how it's stored in all
        other instances. The only exception is if the passed date consists of
        an empty list, which is a special case that requires returning an
        Appointment instance whose every attribute is an empty string '' as
        such an instance is treated as later than any other (and itself).
        
        The `date` parameter is passed to static method `date_is_valid`
        for validation.

        Parameters
        ----------
        date : list[str]
            The date as read from command line arguments, i.e. in the
            format DD MM YYYY, or DD Month YYYY as a list of strings;
            alternatively, a list of one string with format DD-MM-YYYY
            or DD/MM/YYY; alternatively, an empty list.
            Year can also be specified as YY, in which case '20' is prefixed.

        Returns
        -------
        Appointment
            The class initialized with the passed `date` parameter
        None
            If the `date` parameter isn't properly formatted
        """
        # determine if date is an empty list
        if date == []:
            return cls('','','','')

        # determine if date is properly formatted
        valid, date = Appointment.date_is_valid(date)
        if not valid:
            return None

        appnt = cls('', date, '', '')
        return appnt
    
    @staticmethod
    def date_is_valid(arg: list[str]) -> tuple[bool, str]:
        """
        Static method that checks whether the user-entered date is formatted
        as supported first, and whether it's a valid date second.

        Parameters
        ----------
        arg : list[str]
            The date argument as a list of either 1 or 3 strings

        Returns
        -------
        tuple[bool, str]

        valid : bool
            True if date is valid, False otherwise
        info : str
            Small string that has different meanings depending on the value
            of the bool `valid` that's returned in the same tuple.
            If `valid` == False, `info` stores the reason the date isn't
            valid. Possible `info` values are:
                'year_format', 'year_not_int', 'month_spelling',
                'invalid_month', 'day_not_int', 'invalid_day',
                'argument_number', 'format_error'

            If instead `valid` == True, `info` stores the date in the
            following format so as to be compatible with `is_sooner_than`
            method for date comparisons: '<dummy> 7 Ottobre 2025'.
        """
        # check if input was empty string
        if len(arg) == 1 and arg[0] == '':
            return True, ''

        # helper function to clean up the code a bit
        def year_is_leap(year: int) -> bool:
            if not year % 4 == 0:
                return False
            elif not year % 100 == 0:
                return True
            elif not year % 400 == 0:
                return False
            else:
                return True

        # define reverse dictionary to convert from int to month name
        HTNOM = {v: k for k, v in MONTH.items()}
        n = len(arg)

        if not n == 1 and not n == 3:
            return False, 'argument_number'

        # convert into ['DD', 'MM', 'YYYY'] format or return False
        if n == 1:
            s = arg[0]
            l_dash = s.split('-')
            l_slash = s.split('/')
            if len(l_dash) == 3:
                arg = l_dash
            elif len(l_slash) == 3:
                arg = l_slash
            else:
                return False, 'format_error'
            
        # parse format: year
        try:
            if len(arg[2]) == 2:
                year_str = '20' + arg[2]
            elif len(arg[2]) == 4:
                year_str = arg[2]
            else:
                return False, 'year_format'
            year_int = int(arg[2])
        except ValueError:
            return False, 'year_not_int'
        # month
        try:
            month_int = int(arg[1])
            if not 1 <= month_int <= 12:
                return False, 'invalid_month'
            else:
                month_str = HTNOM[month_int].capitalize()
        except ValueError:
            try:
                month_int = MONTH[arg[1].capitalize()]
                if not 1 <= month_int <= 12:
                    return False, 'invalid_month'
                else:
                    month_str = HTNOM[month_int].capitalize()
            except KeyError:
                return False, 'month_spelling'
        # day
        try:
            day_int = int(arg[0])
            day_max = DAYS[month_int]

            if month_int == 2 and year_is_leap(year_int):
                day_max += 1

            if not 1 <= day_int <= day_max:
                return False, 'invalid_day'
            
            day_str = str(day_int)
        except ValueError:
            return False, 'day_not_int'

        # if all checks passed, join with whitespace and return
        date = " ".join(['<dummy>', day_str, month_str, year_str])
        return True, date

class Prescription:
    """
    Class used to store information on saved prescriptions

    Methods
    -------
    get_creds
        Returns relevant information for login as tuple
    """
    def __init__(self, cf: str, nre: str, name: str, note: str):
        """Constructor for Prescription class"""
        self.cf = cf
        self.nre = nre
        self.name = name
        self.note = note

    def __str__(self) -> str:
        name = self.name
        for _ in range(0, 3 - int(len(self.name)/8)):
            name = name + '\t'
        return "\t".join([self.cf, self.nre, name, self.note])
    
    def __eq__(self, other: 'Prescription') -> bool:
        return self.__dict__ == other.__dict__
    
    def get_creds(self) -> tuple[str, str]:
        """Returns relevant information for login as tuple"""
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

def interactive_latest_appointment() -> Appointment:
    """
    Prompts the user for the date before which they don't want found
    appointments to produce notifications and returns an instance.

    Returns
    -------
    Appointment
        The instance whose `date` attribute is set to the date input by the
        user after having been converted to a format compatible with the 
        `is_sooner_than` method for later comparison.
        Said format is: 'str int str int'
    """
    valid = False
    lines_printed = -1
    p = lambda s: _center(s, line_width, False, False)

    cls()
    divider('=', line_width, '\n')
    _center("IMPOSTA LA DATA MASSIMA\n", line_width, True)
    p("Imposta una data. Sanidrive non ti avvisera' se trovera' degli "+
        "appuntamenti per date successive a quella impostata: potrai "+
        "vederli nella lista, ma SaniDrive continuera' a cercare.\n")
    p("La data puo' essere espressa nei formati: GG MM AAAA, GG-MM-"+
        "AAAA, GG/MM/AAAA, oppure GG Mese AAAA. Puoi anche usare AA "+
        "anziche' AAAA. Puoi anche premere invio senza inserire una data, "+
        "ed in tal caso SaniDrive ti avvisera' ogni volta che trovera' un "+
        "appuntamento per un giorno piu' vicino di tutti quelli trovati in "+
        "precedenza.")
    print("\n\nEsempi: 07 10 25, 17/04/25, 2 Marzo 2025.\n\n")
    _center('-'*48, line_width, True); print('')
    
    while True:
        
        print(f'\x1b[{lines_printed+1}F\x1b[2K', end='')
        date = input('\t\t\t\t\t    Inserisci la data: ')

        print(f'\x1b[{lines_printed}E')
        backline(lines_printed)
        lines_printed = 1

        date = date.split(' ')
        valid, reason = Appointment.date_is_valid(date)
        if valid: break

        match reason:
            case 'year_format':
                lines_printed += p("Sembra che tu abbia commesso un "+
            "errore digitando l'anno. L'anno deve essere un numero di due o "+
            "quattro cifre, senza apostrofo. Riprova.")
            case 'year_not_int':
                lines_printed += p("L'anno deve essere espresso con "+
            "un numero intero di due o quattro cifre, senza apostrofo. "+
            "Riprova.")
            case 'month_spelling':
                lines_printed += p("Sembrerebbe che tu abbia scritto "+
            "male il nome del mese. Controlla e riprova.")
            case 'invalid_month':
                print("Questo mese non esiste. Riprova.")
                lines_printed += 1
            case 'day_not_int':
                lines_printed += p("Il giorno deve essere espresso con "+
            "un numero di una o due cifre, con o senza lo zero. Riprova.")
            case 'invalid_day':
                print("Questo giorno non e' valido.")
                lines_printed += 1
            case 'argument_number', 'format_error':
                lines_printed += p("Sembra che tu abbia abbia "+
            "sbagliato qualcosa. Devono comparire tre numeri separati da "+
            "spazio, - o /, oppure il numero del giorno, il nome del mese, "+
            "e il numero dell'anno. ")
                lines_printed += p("Non mischiare spazi, - e /, e "+
            "se scrivi il nome del mese per intero usa solo spazi e non "+
            "- o /. Riprova.")
            case '':
                pass
            case _:
                print("E' successo qualcosa di strano. Non so cos'hai "+
                      "combinato, complimenti. Comunque riprova.")
                lines_printed += 1
    
    return Appointment.latest(date)

def init_driver(args: Namespace) -> WebDriver:
    """
    Create a new WebDriver instance with the correct parameters specified
    by the user from CLI and return it. This unfortunately needs to be done
    for every cycle because the website freaks out if all context isn't
    completely reset when re-visiting the login page.

    MAKE SURE the previous instance of the driver has been killed with
    driver.quit() before reassigning it with init_driver again

    Parameters
    ----------
    args : Namespace
        The Namespace object produced by argparse. This must contain:
        driverFile : str
            Path to the ChromeDriver executable
        logFile : str
            Path to the file to write ChromeDriver logs to
    Returns
    -------
    WebDriver
        The instance of the Selenium ChromeDriver

    """
    print("Inizializzazione ChromeDriver... ", end='') # 33 characters in line
    sys.stdout.flush()
    try:
        chrome_options = Options()
        chrome_service = Service()

        if not args.visible:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument(f'--executable_path={args.driverFile}')
        chrome_service.log_output = os.path.abspath(args.logFile)
        # chrome_service isn't included as the second argument because
        # Selenium bugs out if it is as of version 4.20.0
        driver = webdriver.Chrome(chrome_options)
        backline(1)
        print("\x1b[1A\x1b[33Cfatto.")
        sys.stdout.flush()
    except:
        print("non riuscita.\nQualcosa e' andato storto. Assicurati di aver "+
            "scaricato la giusta versione di ChromeDriver. La puoi trovare "+
            "qui: https://googlechromelabs.github.io/chrome-for-testing/ \n"+
            "La versione deve essere la stessa del browser Chrome, che puoi "+
            "trovare andando alla pagina chrome://version")
        sys.exit(1)
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

def expand_list(driver: webdriver):
    """
    Instructs driver to click the button that loads all appointments
    
    Parameters
    ----------
    driver : webdriver
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

def parse_arguments() -> Namespace:

    class ArgumentParser(argparse.ArgumentParser):
        # Custom class that overrides default message
        def error(self, message):
            print("\nSembra che tu abbia commesso un errore nell'usare le "+
            "opzioni da linea di comando.\nUsa l'opzione --aiuto per una "+
            "lista di tutte le opzioni e istruzioni su come usarle.")
            self.exit(1)

    parser = ArgumentParser(
                prog="SaniDrive",
                description="Tieni traccia e avverti automaticamente di posti liberi per una prenotazione al CUP Sardegna",
                epilog='SaniDrive by Michele Deiana (github.com/mdeiana). Governo pls fix sanita\''#,
                #formatter_class=argparse.RawTextHelpFormatter
                )
    parser.add_argument('--file', '-f', dest='credFile', default='data/credenziali.json', metavar='FILE',
        help=f'Specifica il percorso del file con le credenziali. E\' bene usare un percorso assoluto '+
        'per garantire l\'uso del file corretto. Il percorso di default e\' "data/credenziali.json", '+
        'relativamente alla directory da cui e\' eseguito SaniDrive.\n')
    parser.add_argument('--driver', dest='driverFile', default='driver/chromedriver.exe', metavar='FILE',
        help='Specifica il percorso dell\'eseguibile di ChromeDriver. E\' bene usare un percorso assoluto '+
        'per garantire l\'uso del file corretto. Il percorso di default e\' "driver/chromedriver.exe", '+
        'relativamente alla directory da cui e\' eseguito SaniDrive. Scarica la versione di ChromeDriver '+
        'che combacia a quella del tuo browser Chrome da https://googlechromelabs.github.io/chrome-for-testing/\n')
    parser.add_argument('--visibile', '--visible', '-v', dest='visible', default=False, action='store_true', help=
        'Di default, il driver e\' eseguito in modalita\' headless, ovvero la finestra del browser '+
        'e\' nascosta per evitare di interagirci accidentalmente. Specificare questa opzione la rende visible.\n')
    parser.add_argument('--log', '-l', dest='logFile', default=None, action='store', metavar='FILE', help='Specifica il percorso '+
        'del file in cui salvare il log di ChromeDriver. Se il parametro non e\' specificato, i log '+
        'non sono salvati. Questo parametro e\' correntemente disabilitato per un bug in Selenium.\n')
    parser.add_argument('--intervallo', '-i', '--timer', '-t', dest='interval', default='30', action='store', metavar='SECONDI', help=
        "Specifica quanti secondi far passare tra un aggiornamento e il prossimo. L'intervallo di default "+
        "e' di 30 secondi. Impostare un'attesa troppo breve potrebbe risultare in malfunzionamenti.\n")
    parser.add_argument('--data', '--date', '-d', '--primadi', '--primadel', '-p', dest='latestDate', default='', action='store',
        nargs='*', metavar='DATA', help="Specifica una data in uno dei seguenti formati: GG MM AAAA, GG-MM-AAAA, "+
        "GG/MM/AAAA, oppure GG Mese AAAA. Puoi anche usare AA anziche' AAAA.\nAd esempio, date valide sono: "+
        "01 01 2025, 29-02-2028, 3/4/25, 19 settembre 2025, 7 Ottobre 25, ma NON lo sono 28-02/25 o 28-ottobre-25."+
        "\nSe questa opzione e' usata ed una data e' specificata, solo gli appuntamenti disponibili prima di "+
        "tale data produrranno una notifica e metteranno in pausa SaniDrive per permettere di procedere "+
        "con la prenotazione, a meno che l'opzione --nonstop sia specificata. Se invece l'opzione e' usata da sola senza una data, "+
        "una notifica sara' prodotta ogni volta che viene trovato un appuntamento per un giorno piu' vicino "+
        "di tutti quelli trovati in precedenza, ma la finestra di ChromeDriver non sara' aperta e SaniDrive "+
        "continuera' a cercare. Infine, se l'opzione non e' specificata, la data potra' essere scelta "+
        "interattivamente dopo aver selezionato un'impegnativa da monitorare.\n")
    #parser.add_argument('--nonstop', '--nostop', '-n', ... 
    #    help="Non fermare il programma quando un appuntamento "+
    #    "precedente la data scelta con --data e' trovato. La notifica verra' "+
    #    "prodotta comunque. Questa opzione e' sempre attiva se l'opzione "+
    #    "--data non e' specificata.")
    args = parser.parse_args()
    return args

def backline(n: int = 1):
    """Goes back to start of n-th last line and erases it"""
    for i in range(n):
        print('\x1b[F\x1b[2K', end='')
        sys.stdout.flush()
    return

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')
    return

def divider(char: str, n: int, *args: str):
    print(char*n)
    for arg in args:
        print(arg, end='')
    return

def _center(string: str, n: int, center_last: bool = False,
	    center_all: bool = False) -> int:
    """Internal function that formats text dynamically"""

    def center_line(line, n):
        """Local function that centers a line in an n character-wide space"""
        l = len(line)
        buf = 0

        if n % 2:
            n += 1
        if l % 2:
            buf +=1
        if l == n - 1:
            buf +=1

        left = ' ' * (int(n/2) - int(l/2) - buf)

        print(f"{left}{line}")

    lines_printed = 0
    index = 0
    remaining_len = len(string)

    if center_all:
        printing_fn = lambda s: center_line(s, n)
    else:
        printing_fn = print

    while remaining_len > n:
        #rightmost_space = index + n - 1
        for subindex in range(0, n):
            if string[index + n-1 - subindex] == ' ':
                break
        if subindex == n-1:
            subindex = 0

        printing_fn(string[index : index + (n - subindex)])
        remaining_len -= n - subindex
        index += n - subindex
        lines_printed += 1

    if center_last:
        center_line(string[index:], n)
    else:
        print(string[index:])
    lines_printed += 1

    return lines_printed

def _fail(reason: str = '', masculine: bool = True) -> None:
    """Internal function that prints info on failure for user"""

    start = 'non riuscito.\n' if masculine else 'non riuscita.\n'
    if reason == 'layout':
        print(start + "Probabilmente il layout della pagina e' "+
            "cambiato, per favore avvisami con email a "+
            "michele.deiana.dev@gmail.com")
    if reason == 'date':
        print("Errore: la data specificata non e' valida oppure e' "+
            "formattata incorrettamente. Controlla la data e ricorda che "+
            "puoi usare l'opzione --help per vedere i formati supportati.")
    if reason == 'session':
        print(start + "Probabilmente la sessione e' scaduta oppure "+
            "la connessione e' stata interrotta. Per favore riprova, "+
            "e se il problema persiste avvisami con email a "+
            "michele.deiana.dev@gmail.com")
    if reason == '':
        print("Errore generico: qualcosa e' andato storto.")
    sys.exit(1)

def pop_prescriptions(path: str) -> list[Prescription]:
    """
    Populates list of prescription objects with attributes
    as read from .json file and return the list.
    Uses `json` standard library for reading and decoding
    into dictionary and list Python objects.

    Parameters
    ----------
    path : str
        The path to the .json file

    Returns
    -------
    list[Prescription]
        The list with the populated Prescriptions

    Raises
    ------
    FileEmptyError
        Custom exception raised when specified file is empty
    Exception
        All exceptions are handled by calling function
    """
    # determine if file is empty, if not load javascript
    with open(path, 'r') as f:
        f.seek(0, os.SEEK_END)
        end = f.tell()
        if end == 0:
            raise FileEmptyError
        else:
            f.seek(0, 0)
            data = json.load(f)
    
    prescriptions : Prescription = []
    for cf, dict in data.items():
        for nre, meta in dict.items():
            name = meta['nome']
            note = meta['nota']
            new_pre = Prescription(cf, nre, name, note)
            prescriptions.append(new_pre)

    return prescriptions

def read_prescriptions(path: str) -> list[Prescription]:
    """
    Open file and populate prescriptions. Used to handle sending
    correct messages to user depending on condition of the specified file

    Parameters
    ----------
    path : str
        The path of the file to open

    Returns
    -------
    list[Prescription]
        The read prescriptions as returned from pop_prescription() function
    """
    prescriptions : Prescription = []
    print("Lettura impegnative... ", end='')

    try:
        prescriptions = pop_prescriptions(path)
        print("fatto.")
    except FileNotFoundError:
        print(f"il file specificato non esiste.\nInserisci un'impegnativa nuova "+
              f"al passaggio successivo per crearlo e salvarla.")
        pass
    except FileEmptyError:
        print(f"il file specificato e' vuoto.\nInserisci un'impegnativa nuova "+
              f"al passaggio successivo per salvarla nel file.")
        pass
    except json.decoder.JSONDecodeError:
        print(f"non riuscita.\nIl file specificato non contiene json valido.\n"+
              f"Specifica un altro file oppure rimuovi il parametro --file per "+
              f"usare il percorso di default (data/credenziali.json).")
        sys.exit(1)
    except KeyError:
        print(f"non riuscita.\nIl file specificato non e' nel formato corretto "+
              f"oppure e' corrotto. Per favore specificane uno nuovo o vuoto.")
        sys.exit(1)
    except Exception:
        print("non riuscita.\nQualcosa e' andato storto.")
        sys.exit(1)
    return prescriptions

def add_prescription() -> Prescription:
    """
    Create a new prescription, asking the user to input relevant data

    Returns
    -------
    Prescription
        Prescription to be appended to list by caller function and
        to be written to .json file with the others in the list
    """

    print("AGGIUNGI NUOVA IMPEGNATIVA".center(line_width), '\n')
    cf = input("Inserisci il Codice Fiscale:\t\t\t\t\t").strip()

    print("\n\nN.B: Il NRE deve includere 2000A e non contenere spazi!", end='')
    print("\x1b[F", end='')

    nre = input("Inserisci il Numero di Ricetta Elettronica:\t\t\t").strip()
    print("\x1b[2K", end='')

    print("\n\nN.B: Se scegli di dare un nome alla prescrizione,\n     non "+
          "superare i 31 caratteri!", end = '')
    print("\x1b[2F", end='')

    name = input("Inserisici il nome della prescrizione (facoltativo):\t\t")
    print("\x1b[2K", end='')

    note = input("\nInserisci una nota aggiuntiva (facoltativo):\t\t\t")

    p = Prescription(cf, nre, name, note)
    return p

def choose_prescription(prescrs: list[Prescription], path: str) -> int:
    """
    Prints all prescriptions, takes user input to choose which one to
    select and start querying the website for. If there are no saved
    prescriptions, creates one. Whenever a new prescription is made,
    prints the whole list again and lets the user decide once more.

    Parameters
    ----------
    prescrs : list[Prescription]
        The list of prescriptions as returned by read_prescriptions()
    path : str
        The path to the .json file to save the newly added prescriptions to

    Returns
    -------
    int
        The index that identifies the chosen prescription from the list
    """
    c = 0
    while c == 0:
        if len(prescrs) > 0:
            print("\nNumero\t Codice fiscale\t\tNRE\t\tNome\t\t\t\tNota")
            divider('-', line_width)
            for i, prescr in enumerate(prescrs):
                print(i+1, "\t", prescr)
            divider('-', line_width)
            print("0",
                  "<<< CREA UNA NUOVA IMPEGNATIVA >>>".center(line_width - 2))
            print("")
            # get int representing choice but accept only valid input
            c = -1
            while c < 0 or c > (i + 1):
                try:
                    c = int(input(f"Seleziona un'impegnativa (0 - {i+1}): "))
                    backline(1)
                except ValueError:
                    backline(1)
                    pass
        else:
            c = 0

        # if selection was 0 or if list is empty, add a new prescription
        if c == 0:
            divider('=', line_width, '\n')
            prescrs.append(add_prescription())
            cls()
            print("Nuova impegnativa definita con successo.")
            print("Salvataggio impegnative... ", end='')
            sys.stdout.flush()
            write_prescriptions(prescrs, path)
            print("fatto."); sys.stdout.flush()

    # subtract 1 from `c` so we can use it as index later
    c -= 1
    return c

def write_prescriptions(prescr_list: list[Prescription], path: str) -> None:
    """
    Starting from a list of read prescriptions, generate the correct
    dictionary object to write to .json file

    Parameters
    ----------
    list : list[Prescription]
        The list of prescriptions
    path : str
        The file to which to write json data
    """
    # this is the dictionary with all the data that will be written
    bigdict = {} # lmao

    # start with a dict where keys are CFs and values are n. of NRE
    # associated with each CF
    cfs = {}
    for prescr in prescr_list:
        if prescr.cf in cfs:
            cfs[prescr.cf] = cfs[prescr.cf] + 1
        else:
            cfs[prescr.cf] = 1

    # loop over each unique CF
    idx = 0
    keys = list(cfs)
    for cf in keys:
        nres = {}
        # loop for each occurrence of that CF
        for i in range(0, cfs[cf]):
            data = {}
            data['nome'] = prescr_list[idx + i].name
            data['nota'] = prescr_list[idx + i].note
            nres[prescr_list[i].nre] = data
        idx = i + 1
        bigdict[cf] = nres

    # dump dictionary to file and we're done
    with open(path, 'w') as f:
        json.dump(bigdict, f, indent=4)

    return

def main():
    cls()
    # parse arguments
    args = parse_arguments()
    credPath = os.path.abspath(args.credFile)
    list_reload_interval = int(args.interval)

    # read prescriptions from file and choose which to track
    prescriptions = read_prescriptions(credPath)
    c = choose_prescription(prescriptions, credPath)

    # set up latest date appointment if date is defined by command line
    if args.latestDate != '':
        latest_appointment = Appointment.latest(args.latestDate)
        if latest_appointment is None:
            _fail(reason='date')
    # set up latest appointment interactively otherwise
    else:
        latest_appointment = interactive_latest_appointment()

    # set up variable for easier printing later
    ldate = latest_appointment.date[7:]
    if ldate == '':
        ldate = 'non specificata'

    # initialize driver
    driver = init_driver(args)

    # get the page with the list of all the appointments and expand the list
    get_appointments_page(driver, *prescriptions[c].get_creds())
    expand_list(driver)
    
    print(f"\nRaggiunta la pagina. Aggiornamento ogni "+
          f"{list_reload_interval} secondi.")
    print("Caricamento lista appuntamenti... ")

    # main loop
    appointments : list[Appointment] = []
    old_appointments : list[Appointment] = []
    appnts = [] # the appointment webelements from the driver, bad name mb
    earliest_appointment = Appointment('','','','')
    change_counter = -1
    refresh_counter = 0
    found_on_refresh = 0
    pretty = 0 # used to make change_counter display intuitive stats
    p = lambda s: _center(s, line_width, True) # ""pretty"" printing lmao
    while True:
        cls()

        # print selected prescription data for sanity
        print("\nNumero\t Codice fiscale\t\tNRE\t\tNome\t\t\t\tNota")
        print(c+1, "\t", prescriptions[c], '\n')
        divider('=', line_width, '\n')
        sys.stdout.flush()
        
        # get appointment objects and discard the first because it's repeated later
        while len(appnts) == 0:
            sleep(1)
            appnts = driver.find_elements(By.CLASS_NAME,
                                          name_class_appointment)
            appnts = appnts[1:]

        for appnt in appnts:
            # extract information
            time_obj = appnt.find_element(By.CLASS_NAME,
                                          'captionAppointment-dateApp')
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

        # store earliest found appointment separately and compare the new
        # batch's earliest with it and the latest for notifications
        try:
            if appointments[0].is_sooner_than(earliest_appointment):
                earliest_appointment = appointments[0]
                found_on_refresh = refresh_counter
            if appointments[0].is_sooner_than(latest_appointment):
                send_notif(appointments[0])
                print('')
                p('|||   NUOVO APPUNTAMENTO TROVATO   |||')
                print('')
                _center('Trovato un appuntamento per prima della data '+
                'specificata. '+
                'Effettua la prenotazione dalla finestra di ChromeDriver '+
                'oppure premi Invio per continuare a cercare usando la '+
                'data di questo prossimo appuntamento come nuova data.'
                , line_width)
                input('')
                backline(6)
                latest_appointment = appointments[0]
                ldate = ' '.join(appointments[0].date.split()[1:])
            pass
        except IndexError:
            pass

        # print prescription column info
        print(f'APPUNTAMENTI'.center(line_width), '\n')
        print(f'Numero\t\t Data\t\t\t\t Ora\t\t\tVia')
        sys.stdout.flush()

        # print all available appointments
        if len(appointments) == 0:
            print("\t\t\t\t\tNessun appuntamento.")
            pretty = 1
        else:
            for i, a in enumerate(appointments):
                print(f"{i+1}\t", a)

        # print some statistics
        print('\n')
        p(f'Data prima della quale avvisare con notifica:')
        p(f'{ldate}')
        print('')
        p(f"Appuntamento piu' vicino trovato (durante aggiornamento "+
          f"{found_on_refresh}):")
        #print('\t\t', earliest_appointment, '\n')
        p(f'{' '.join(earliest_appointment.__str__().split())}')
        print(f'\n\t\t\tAggiornamenti totali: '+
              f'{refresh_counter}\t\t\t\tCambiamenti rilevati: '+
              f'{change_counter+pretty}\n')
        divider('=', line_width, '\n')

        # cycle data
        old_appointments = appointments
        appointments = []
        appnts = []
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