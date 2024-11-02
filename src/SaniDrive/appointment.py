"""
Provides class and routines to store, manage, compare and convert appointments
as parsed from the CUP website into useful, structured objects.
"""

import config
from config import MONTH, DAYS
from util import divider, _center, backline, cls

from plyer import notification

class Appointment:
    """
    Class that stores information on found appointments and provides
    ways of comparing and ordering them by date.

    Attributes
    ----------
    place : str
        Place information as read from website appointment list
    date : str
        Date information in the form 'Sabato 2 Novembre 2025'
    time : str
        Time information in the form '14:20'
    notes : str
        Other information as read from website (not implemented)

    Methods
    -------
    is_sooner_than
        Returns True if called from an instanced Appointment
        that is closer in time than the Appointment instance
        passed as argument.
    latest
        Class method that returns an Appointment instance whose `date`
        attribute is based on the date specified from command line
        arguments to allow for date comparisons with is_sooner_than.
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
        comes first in time.
        
        Returns True if the instance this is called from is closer in time
        than the Appointment instance that is passed as argument, or when
        the latter instance is empty.

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
        other instances.
        
        The only exception is if the passed date consists of an empty list,
        which is a special case that requires returning an Appointment instance
        whose every attribute is an empty string '' as such an instance is
        treated as positioned later in time than any other (and itself).
        
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
            The class initialized with the passed `date` parameter.
        None
            If the `date` parameter isn't properly formatted.

        See Also
        --------
        Appointment.date_is_valid
            Used for date validation.
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
            If `valid` == False, `info` stores the reason the date isn't
            valid.
            
            Possible `info` values are:
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
    line_width = config.line_width
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
        _center('Inserisci la data: ', line_width * 13/14, True, False, False)
        date = input()

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