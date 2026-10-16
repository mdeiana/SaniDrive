import os
import sys
import json
import difflib
from pathlib import Path

from .config import locations_path, line_width
from .util import InteractiveMenu
from .util import divider, backline, cls, _center, CLEAR_SCREEN

class Location:
    """Represents a selected comune and the distances to all other comuni.

    The class loads the Sardinian comune distance matrix from the configured
    JSON file and keeps a shared list of known comune names for fuzzy matching.
    """
    comuni_names: list[str] = []
    selected_comune: str
    distances: dict[str, float]
    distance_max: float

    def __init__(self, name:str) -> None:
        self.populate_names_list()
        if name not in self.comuni_names:
            return
        del type(self).comuni_names
        self.select_comune(name)

    def select_comune(self, name:str) -> None:
        with open(locations_path.__str__(), 'r', encoding='utf-8') as f:
            data: dict = json.load(f)
            self.selected_comune = name
            self.distances = data[name]

    def get_distance_to(self, name:str) -> float:
        return self.distances[name]

    def can_reach(self, name:str) -> bool:
        distance = self.distances.get(self.find_match(name), None)
        if distance is None:
            print('WARN: comune letto da lista appuntamenti non combacia')
            return True
        return (distance <= self.distance_max)

    def get_furthest_valid(self, count: int, dist_max: float) -> list[str]:
        results = ['lol']
        distances_buff = []
        for i in range(count):
            distances_buff.append(0.0)
        for comune, distance in self.distances.items():
            if distance > dist_max:
                continue
            for i in range(count):
                if distance > distances_buff[i]:
                    distances_buff.insert(i, distance)
                    distances_buff.pop()
                    results.insert(i, comune)
                    results.pop()
                    break
        return results

    @classmethod
    def populate_names_list(cls) -> None:
        if len(cls.comuni_names) == 0:
            with open(locations_path.__str__(), 'r', encoding='utf-8') as f:
                data: dict = json.load(f)
                for key in data.keys():
                    cls.comuni_names.append(str(key).strip())

    @classmethod
    def find_match(cls, query: str) -> str:
        cls.populate_names_list()
        matches = difflib.get_close_matches(
            query, cls.comuni_names, n=1, cutoff=0.6)
        if len(matches) == 0:
            return ''
        else:
            return matches[0]

class InteractiveLocationMenu(InteractiveMenu):
    def __init__(self) -> None:
        pass

    def print_header(self) -> None:
        p = lambda s: _center(s, line_width, False, False)
        cls()
        divider('=', line_width, '\n')
        _center("IMPOSTA LOCALITA', DISTANZA MASSIMA\n", line_width, True)
        p("SaniDrive permette di filtrare gli appuntamenti che ti propone in "+
            "base a quanto il tuo comune dista dal luogo di ogni appuntamento "+
            "disponibile sul portale CUPWeb, stimando i chilometri da percorrere "+
            "(in macchina) per raggiungerlo.\n")
        p("Per farlo, puoi impostare il comune in cui risiedi e specificare la "+
            "distanza massima che sei disposto a guidare per l'appuntamento. Se "+
            "vuoi essere notificato a prescindere dal comune dell'appuntamento, "+
            "premi Invio lasciando il campo vuoto per saltare questo passaggio.")
        print('\n\n')
        _center('-'*48, line_width, True); print('')


# ============= Step functions for interactive location selection =============



def interactive_location() -> Location:
    """
    Prompt the user to select the comune they reside in interactively
    to help them determine the maximum distance they are willing to travel
    to reach an appointment in another comune.
    """
    location = Location('lol')



    return location
    