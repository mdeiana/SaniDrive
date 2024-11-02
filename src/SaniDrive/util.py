"""
Defines routines to format text and print information to the user.
Additionally provides command-line argument parsing and a routine to
automatically download ChromeDriver.
"""

import os
import sys
import json
import config
import zipfile
import requests
import argparse
from time import sleep
from bs4 import BeautifulSoup
from argparse import Namespace

# Constant Values
driver_version_page = 'https://googlechromelabs.github.io/chrome-for-testing/'
driver_dl_page = 'https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json'

def parse_arguments() -> Namespace:
    """Parse arguments using Argparse."""
    class ArgumentParser(argparse.ArgumentParser):
        """Custom class that overrides default message"""
        def error(self, message):
            print("\nSembra che tu abbia commesso un errore nell'usare le "+
            "opzioni da linea di comando.\nUsa l'opzione --help per una "+
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
    parser.add_argument('--driver', dest='driverFile', default='data/chromedriver-win64/chromedriver.exe', metavar='FILE',
        help='Specifica il percorso dell\'eseguibile di ChromeDriver. E\' bene usare un percorso assoluto '+
        'per garantire l\'uso del file corretto. Il percorso di default e\' "data/chromedriver-win64/chromedriver.exe", '+
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
    parser.add_argument('--nonstop', '--nostop', '-n', dest='nonstop',
        default=False, action='store_true',
        help="Non fermare il programma quando un appuntamento "+
        "precedente la data scelta con --data e' trovato. La notifica verra' "+
        "prodotta comunque.")
    parser.add_argument('--exec', '-e', '--audio', '-a', dest='audioFile',
        default='data/emmescingue.mpeg',
        action='store', help="Specifica il percorso di un file "+
        "da eseguire quando un appuntamento precedente la data scelta con "+
        "--data e' trovato. L'utilizzo inteso e' quello di riprodurre un "+
        "file audio o aprire un collegamento a un video, ma eseguire un "+
        "file arbitrario puo' essere un modo di estendere le funzionalita' "+
        "di SaniDrive.", metavar='FILE')
    args = parser.parse_args()
    return args

def download_chromedriver(dir_path: str) -> str:
    """
    Download the latest stable version of ChromeDriver automatically.

    Go to the dispatch page `https://googlechromelabs.github.io/chrome-for-\
    testing/known-good-versions-with-downloads.json` and download the latest
    stable version of ChromeDriver obtained by parsing the official page
    `https://googlechromelabs.github.io/chrome-for-testing/`.

    Parameters
    ----------
    dir_path : str
        The absolute path to the directory that is either specified as
        destined for chromedriver.exe to reside in or the default one.

    Returns
    -------
    str
        The absolute path to the downloaded chromedriver.exe, which should be
        `f'{dir_path}/chromedriver-win64/chromedriver.exe'`
    """

    archive_path = os.path.join(dir_path, 'chromedriver-win64.zip')
    extr_dir_path = os.path.join(dir_path, 'chromedriver-win64')
    driver_path = os.path.join(extr_dir_path, 'chromedriver.exe')
    p = lambda s: _center(s, config.line_width)
    print("Controllo presenza ChromeDriver... non rilevata.\n")
    p("Se non hai indicato manualmente il percorso di chromedriver.exe, "+
      "probabilmente non hai scaricato ChromeDriver. SaniDrive puo' "+
      "scaricarlo automaticamente per te nella cartella di default o "+
      "in quella specificata se ne hai scelta una.")
    print('\n')

    c = 0
    while c != 1:
        c = input('Scaricare ChromeDriver automaticamente? (S/n): ')
        backline(1)
        if c == 'S' or c == 's':
            c = 1
        if c == 'N' or c == 'n':
            sys.exit(0)

    # get the latest stable version
    print('Controllo versione ChromeDriver... ', end=''); sys.stdout.flush()
    sleep(1)
    try:
        response = requests.get(driver_version_page)
        soup = BeautifulSoup(response.text, 'html.parser')
        version = soup.find('code').text
    except:
        _fail('automatic_download')
    print(f"trovata versione {version}.\n")
    p("Assicurati di avere la stessa "+
      f"versione del browser Google Chrome installata (solitamente "+
      f"coincide con l'ultimo aggiornamento disponibile).")

    print('\nConsultazione JSON API endpoints... ', end=''); sys.stdout.flush()
    sleep(1)
    try:
        response = requests.get(driver_dl_page)
        soup = BeautifulSoup(response.text, 'html.parser')
        biglist = json.loads(soup.__str__())['versions']
        for bigdict in biglist:
            if bigdict['version'] == version:
                dictlet = bigdict['downloads']
                break
        dl_url = dictlet['chromedriver'][4]['url']
    except:
        _fail('automatic_download')
    print('fatto.')

    print(f'\nDownload da {dl_url}... '); sys.stdout.flush()
    sleep(1)
    try:
        response = requests.get(dl_url, stream=True)
        response.raise_for_status()

        with open(archive_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    break
                f.write(chunk)
        print('fatto.')
    except:
        _fail('automatic_download')
        sys.exit(1)

    print(f'\nDecompressione archivio... ', end=''), sys.stdout.flush()
    sleep(1)
    try:
        with zipfile.ZipFile(archive_path, 'r') as zip:
            zip.extractall(dir_path)
    except:
        _fail('automatic_download', masculine=False)
    print('fatto.')

    print("Rimozione archivio... ", end=''), sys.stdout.flush()
    sleep(1)
    try:
        os.remove(archive_path)
        print("completata.")
    except:
        print("non riuscita. Passaggio non vitale, procediamo...\n")

    print("\n\n")
    _center('-'*47, config.line_width, True)
    _center("Installazione automatica avvenuta con successo.",
            config.line_width, True)
    _center('-'*47, config.line_width, True)
    print("\n\n")
    print("L'eseguibile di ChromeDriver si trova ora nel percorso:\n"+
          f"{driver_path}\n\n")
    
    _center('|||   Premere Invio per continuare   |||', config.line_width,
            True)
    input('')
    cls()

    return driver_path

def cls():
    """Clear the screen using shell commands."""
    os.system('cls' if os.name == 'nt' else 'clear')
    return

def title():
    """Print title from file if available, otherwise from string literals."""
    title_path = os.path.abspath('data/title.txt')
    p = lambda s: _center(s, config.line_width, True, False, True)
    divider('=', config.line_width, '\n')

    if not os.path.isfile(title_path) or config.line_width < 92:
        p(r'')
        p(r'  / ____|           (_)  __ \     (_)           ')
        p(r' | (___   __ _ _ __  _| |  | |_ __ ___   _____  ')
        p(r"  \___ \ / _` | '_ \| | |  | | '__| \ \ / / _ \ ")
        p(r'  ____) | (_| | | | | | |__| | |  | |\ V /  __/ ')
        p(r' |_____/ \__,_|_| |_|_|_____/|_|  |_| \_/ \___| ')
    else:
        with open(title_path, 'r') as f:
            for line in f:
                p(line.strip('\n'))

    print('\n')
    print('by Michele Deiana, github.com/mdeiana'.rjust(config.line_width))
    divider('=', config.line_width, '\n')
    print('\n\n\n\n'); p('|||   Premi Invio per iniziare   |||')
    sys.stdout.write("\033[?25l"); input('')
    sys.stdout.write("\033[?25h"); cls()
    return

def backline(n: int = 1):
    """Go back to start of n-th last line and erase it."""
    for i in range(n):
        print('\x1b[F\x1b[2K', end='')
        sys.stdout.flush()
    return

def divider(char: str, n: int, *args: str):
    """Print a divider that matches the length of the terminal."""
    print(char*n)
    for arg in args:
        print(arg, end='')
    return

def _center(string: str, n: int, center_last: bool = False,
	    center_all: bool = False, trailing_newline: bool = True) -> int:
    """
    Internal function that formats text dynamically.
    
    Parameters
    ----------
    string : str
        The text to be printed.
    n : int
        The width of the screen, used for wrapping the text into many lines.
    center_last : bool
        Whether to have the last line be centered or left-aligned.
    center_all : bool
        Whether the text should be simply wrapped, or also centered.
        This affects all lines except the last, which is instead controlled
        by the `center_last` parameter.
    trailing_newline : bool
        Whether to print a newline after all the text has been printed.

    Returns
    -------
    int
        The amount of lines printed.
    """

    def center_line(line, n, end_char = '\n'):
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

        print(f"{left}{line}", end=end_char)

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
        center_line(string[index:], n, end_char='')
    else:
        print(string[index:], end='')
    lines_printed += 1

    if trailing_newline:
        print('')

    return lines_printed

def _fail(reason: str = '', masculine: bool = True) -> None:
    """
    Internal function that prints info on failure for user
    
    Parameters
    ----------
    reason : str
        Valid strings are 'layout', 'date', 'session', 'automatic_download',
        ''.
    """
    p = lambda s: _center(s, config.line_width)
    start = 'non riuscito.\n' if masculine else 'non riuscita.\n'
    if reason == 'layout':
        print(start); p("Probabilmente il layout della pagina e' "+
            "cambiato, per favore avvisami con email a "+
            "michele.deiana.dev@gmail.com")
    if reason == 'date':
        p("Errore: la data specificata non e' valida oppure e' "+
            "formattata incorrettamente. Controlla la data e ricorda che "+
            "puoi usare l'opzione --help per vedere i formati supportati.")
    if reason == 'session':
        print(start); p("Probabilmente la sessione e' scaduta oppure "+
            "la connessione e' stata interrotta. Per favore riprova, "+
            "e se il problema persiste avvisami con email a "+
            "michele.deiana.dev@gmail.com")
    if reason == 'automatic_download':
        print(start); p("Qualcosa e' andato storto. Per favore riprova, e se "+
              "il problema persiste contattami con email a "+
              "michele.deiana.dev@gmail.com")
    if reason == '':
        print("Errore generico: qualcosa e' andato storto.")
    sys.exit(1)