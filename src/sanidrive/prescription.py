"""
Provides classes and routines to manage the user-defined prescriptions
for which appointments will be searched.

See Also
--------
:py:mod:`appointment`
"""


import os
import sys
import json
from pathlib import Path

from . import config
from .util import divider, backline, cls

class FileEmptyError(Exception):
    pass

class Prescription:
    """
    Stores information on a saved prescription.
    """
    def __init__(self, cf: str, nre: str, name: str, note: str):
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
        """Returns relevant information for login as tuple."""
        return self.cf, self.nre
    
def read_prescriptions(path: Path | str) -> list[Prescription]:
    """
    Open file and populate prescriptions. Handles sending the correct error
    messages to the user depending on the specified file and its contents.

    Parameters
    ----------
    path : str
        The path of the file to open.

    Returns
    -------
    list[Prescription]
        The read prescriptions as returned from pop_prescription() function.
    """
    prescriptions : list[Prescription] = []
    print("Lettura impegnative... ", end='')

    try:
        prescriptions = pop_prescriptions(path)
        print("fatto.")
    except FileNotFoundError:
        print(f"il file specificato non esiste.\nInserisci un'impegnativa nuova "+
              f"al passaggio successivo per crearlo e salvarla.\n")
        pass
    except FileEmptyError:
        print(f"il file specificato e' vuoto.\nInserisci un'impegnativa nuova "+
              f"al passaggio successivo per salvarla nel file.\n")
        pass
    except json.decoder.JSONDecodeError:
        print(f"non riuscita.\nIl file specificato non contiene json valido.\n"+
              f"Specifica un altro file oppure rimuovi il parametro --file per "+
              f"usare il percorso di default (data/credenziali.json).\n")
        sys.exit(1)
    except KeyError:
        print(f"non riuscita.\nIl file specificato non e' nel formato corretto "+
              f"oppure e' corrotto. Per favore specificane uno nuovo o vuoto.\n")
        sys.exit(1)
    except Exception:
        print("non riuscita.\nQualcosa e' andato storto.\n")
        sys.exit(1)
    return prescriptions

def pop_prescriptions(path: Path | str) -> list[Prescription]:
    """
    Populates list of prescription objects with attributes as read from
    .json file and return the list.

    Uses `json` standard library for reading and decoding into dictionary and
    list Python objects.

    Parameters
    ----------
    path : str
        The path to the .json file.

    Returns
    -------
    list[Prescription]
        The list with the populated Prescriptions.

    Raises
    ------
    FileEmptyError
        Custom exception raised when specified file is empty.
    Exception
        All exceptions are handled by caller function.
    """
    # determine if file is empty, if not load json
    with open(path, 'r') as f:
        f.seek(0, os.SEEK_END)
        end = f.tell()
        if end == 0:
            raise FileEmptyError
        else:
            f.seek(0, 0)
            data = json.load(f)
    
    prescriptions : list[Prescription] = []
    for cf, dict in data.items():
        for nre, meta in dict.items():
            name = meta['nome']
            note = meta['nota']
            new_pre = Prescription(cf, nre, name, note)
            prescriptions.append(new_pre)

    return prescriptions

def choose_prescription(prescrs: list[Prescription], path: Path | str) -> int:
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
    line_width = config.line_width
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

def add_prescription() -> Prescription:
    """
    Create a new prescription, asking the user to input relevant data

    Returns
    -------
    Prescription
        Prescription to be appended to list by caller function and
        to be written to .json file with the others in the list
    """

    print("AGGIUNGI NUOVA IMPEGNATIVA".center(config.line_width), '\n')
    cf = input("Inserisci il Codice Fiscale:\t\t\t\t\t").strip()

    print("\n\nN.B: Il NRE deve includere 2000A e non contenere spazi!",
          end='')
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

def write_prescriptions(prescr_list: list[Prescription],
                        path: Path | str) -> None:
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

    bigdict : dict[str, dict] = {}
    for prescr in prescr_list:
        if prescr.cf not in bigdict.keys():
            bigdict[prescr.cf] = {}

        smoldict = {"nome":prescr.name, "nota":prescr.note}
        bigdict[prescr.cf][prescr.nre] = smoldict

    with open(path, 'w') as f:
        json.dump(bigdict, f, indent=4)

    return