"""Entry point with main script logic"""

import os
import sys
import shutil
from time import sleep

import config
from util import cls, title, _center, backline, divider, _fail
from util import parse_arguments, download_chromedriver
from prescription import read_prescriptions, choose_prescription
from appointment import Appointment, interactive_latest_appointment, send_notif
from driver import By
from driver import name_class_appointment
from driver import init_driver, get_appointments_page, expand_list

__version__ = '1.3'

def run():
    # parse arguments, get absolute directories for files
    args = parse_arguments()
    cred_path = os.path.join(root, args.credFile)
    audio_path = os.path.join(root, args.audioFile)
    audio_exists = os.path.isfile(audio_path)
    driver_path = os.path.join(root, args.driverFile)
    list_reload_interval = int(args.interval)

    # download the latest version of chromedriver if it's not in provided path
    if not os.path.isfile(driver_path):
        if not os.path.exists(os.path.dirname(driver_path)):
            os.mkdir(os.path.dirname(driver_path))
        driver_path = download_chromedriver(os.path.dirname(driver_path))

    # read prescriptions from file and choose which to track
    prescriptions = read_prescriptions(cred_path)
    c = choose_prescription(prescriptions, cred_path)

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
    driver = init_driver(driver_path, args.visible)

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
    p = lambda s: _center(s, line_width, True) # shorten call to _center
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
                
                if audio_exists:
                    os.system(f'{audio_path}')

                if not args.nonstop:
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
        p(f'{' '.join(earliest_appointment.__str__().split())}')
        print('')
        p(f"Aggiornamenti totali: {refresh_counter}"+' '*25+
          f"Cambiamenti rilevati: {change_counter+pretty}")
        print('')
        """ print(f'\n\t\t\tAggiornamenti totali: '+
              f'{refresh_counter}\t\t\t\tCambiamenti rilevati: '+
              f'{change_counter+pretty}\n') """
        divider('=', line_width, '\n')

        # cycle data
        old_appointments = appointments
        appointments = []
        appnts = []
        refresh_counter += 1

        # refresh
        driver.delete_all_cookies()
        sleep(list_reload_interval)
        print("Aggiornamento lista appuntamenti... ")
        get_appointments_page(driver, *prescriptions[c].get_creds())
        expand_list(driver)

if __name__ == "__main__":
    # parse arguments, get absolute directories for files
    root = os.path.dirname(os.path.realpath(__file__))
    title_path = os.path.join(root, '../../data/title.txt')

    # get screen dimensions and print title
    line_width = shutil.get_terminal_size((120, 30))[0]
    config.set_line_width(line_width)
    cls()
    title(title_path)

    try:
        run()
    except (KeyboardInterrupt, EOFError):
        print('')
        sys.exit(0)