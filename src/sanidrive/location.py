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
    distances: dict[str, float]
    selected_comune: str
    distance_max: float
    forced_comuni: list[str]
    mock: bool = False

    def __init__(self, name:str, distance:float, forced: list[str]) -> None:
        if name == 'mock':
            self.mock = True
            return
        self.populate_names_list()
        if name not in self.comuni_names:
            return
        del type(self).comuni_names
        self.distance_max = distance
        self.forced_comuni = forced
        self.select_comune(name)

    def __str__(self):
        lines = [f"{self.__class__.__name__}:"]
        d = vars(self)
        for k, v in d.items():
            if v is self:
                display_value = "<self>"
            elif type(v) == dict:
                display_value = "<dict>"
            else:
                display_value = str(v)
            lines.append(f'  {k}: {display_value}')
        return "\n".join(lines)

    def select_comune(self, name:str) -> None:
        with open(locations_path.__str__(), 'r', encoding='utf-8') as f:
            data: dict = json.load(f)
            self.selected_comune = name
            self.distances = data[name]

    def get_distance_to(self, name:str) -> float:
        return self.distances[name]

    def can_reach(self, name:str) -> bool:
        if self.mock or name in self.forced_comuni:
            return True
        distance = self.distances.get(self.find_match(name), None)
        if distance is None:
            print('WARN: comune letto da lista appuntamenti non combacia')
            return True
        return (distance <= self.distance_max)

    def get_furthest_valid(self, count: int) -> list[str]:
        results = [(comune, distance)
            for comune, distance in self.distances.items()
            if distance <= self.distance_max
        ]
        results.sort(key=lambda item: item[1], reverse=True)
        return [comune for comune, distance in results[:count]]

    @classmethod
    def populate_names_list(cls) -> None:
        try:
            do_load = (len(cls.comuni_names) == 0)
        except AttributeError:
            cls.comuni_names = []
            do_load = True
        if do_load:
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
            return 'none'
        else:
            return matches[0]

class LocationPickMenu(InteractiveMenu):
    def __init__(self, *args, **kwargs) -> None:
        self.p = lambda s: _center(s, line_width, False, False)
        super().__init__(*args, **kwargs)

    def print_header(self) -> None:
        p = self.p
        cls()
        divider('=', line_width, '\n')
        _center("IMPOSTA LOCALITA', DISTANZA MASSIMA\n", line_width, True)
        p("SaniDrive permette di filtrare gli appuntamenti che ti propone in "
        "base a quanto il tuo comune dista dal luogo di ogni appuntamento "
        "disponibile sul portale CUPWeb, stimando i chilometri da percorrere "
        "(in macchina) per raggiungerlo.\n")
        p("Per farlo, puoi impostare il comune in cui risiedi e specificare "
        "la distanza massima che sei disposto a guidare per l'appuntamento "
        "(calcolata approssimativamente dai dati offerti da OpenRouteService "
        "e OpenStreetMap sulle strade sarde e da Istat sui comuni "
        "al 14/10/2026). Se "
        "vuoi essere notificato a prescindere dal comune dell'appuntamento, "
        "premi Invio lasciando il campo vuoto per saltare questo passaggio.")
        divider('-', line_width, '\n')
        #print('\n\n')
        #_center('-'*48, line_width, True); print('')


# ============= Step functions for interactive location selection =============

def step_comune(context: dict) -> tuple[str, str]:
    _center('Inserisci il tuo comune di residenza o premi Invio: ',
            line_width * 13 // 14, True, False, False)
    query = input()
    if query == '':
        context.pop('comune', None)
        return 'BACK', ''
    name = Location.find_match(query)
    if name == 'none':
        context['warning'] = 'Comune non trovato. Riprova.'
        return 'RETRY', ''
    context['comune'] = name
    return 'ADVANCE', ''

def step_comune_confirm(context: dict) -> tuple[str, str]:
    _center(f'Comune selezionato: {context['comune']}. Confermi? (Si/no): ',
            line_width * 13 // 14, True, False, False)
    answer = input().capitalize().startswith('S')
    if not answer:
        context.pop('comune', None)
        return 'BACK', ''
    return 'ADVANCE', ''

def step_distance(context: dict) -> tuple[str, str]:
    valid = True
    _center('Indica la distanza massima (in chilometri) che sei disposto a '
            f'viaggiare in macchina da {context['comune']} al luogo dell\''
            'appuntamento o lascia il campo vuoto per cambiare comune: ',
            line_width, False, False, False)
    answer = input()
    if answer == '':
        if context.get('distance', False):
            context.pop('distance')
        context.pop('comune')
        return 'BACK', ''
    try:
        answer = float(answer)
        if answer <= 0:
            valid = False
    except ValueError:
        valid = False

    if not valid:
        context['warning'] = 'Il numero inserito non e\' valido, riprova.'
        return 'RETRY', ''
    context['distance'] = answer
    return 'ADVANCE', ''

def step_distance_confirm(context: dict) -> tuple[str, str]:
    comuni = ', '.join(Location(context['comune'], context['distance'], [])
              .get_furthest_valid(3))
    
    if comuni == 'lol':
        _center('Non puoi raggiungere nessun comune percorrendo solo '
            f'{context['distance']} chilometri da {context['comune']}.',
            line_width, True)
        _center(f'Vuoi cercare appuntamenti solo a {context['comune']}? '
                '(Si/no): ', line_width, True, True, False)
        answer = input().capitalize().startswith('S')
        if not answer:
            context.pop('distance')
            return 'BACK', ''
        return 'ADVANCE', ''
    
    _center('I comuni piu\' distanti che puoi raggiungere percorrendo '
            f'{context['distance']} chilometri sono:',
            line_width * 13 // 14, True, False, True)
    _center(f'{comuni}.', line_width, True, False)
    _center('\tConfermi? (Si/no): ', line_width * 13 // 14, True, False, False)
    answer = input().capitalize().startswith('S')
    if not answer:
        context.pop('distance', None)
        return 'BACK', ''
    return 'ADVANCE', ''

def step_forced_comuni(context: dict) -> tuple[str, str]:
    _center('Puoi anche indicare comuni che sei disposto a raggiungere a '
            'prescindere dalla distanza. Scrivi il nome del comune oppure '
            'lascia il campo vuoto per continuare.',
            line_width, False, False, False)
    print('\n\n')
    comuni = context.get('forced_comuni', [])
    if comuni:
        _center(f'Fino ad ora hai selezionato: {', '.join(comuni)}',
                line_width * 13 // 14, True, False, False)
    print('\n\n')
    _center('Nome comune da aggiungere: ',
            line_width * 13 // 14, True, False, False)
    answer = input()
    if answer == '':
        return 'ADVANCE', ''
    name = Location.find_match(answer)
    if name == 'none':
        context['warning'] = 'Comune non trovato. Riprova.'
        return 'RETRY', ''
    elif name in comuni or name == context['comune']:
        return 'RETRY', ''
    else:
        comuni.append(name)
        context['forced_comuni'] = comuni
        return 'RETRY', ''
    

def interactive_location() -> Location:
    """
    Prompt the user to select the comune they reside in interactively
    to help them determine the maximum distance they are willing to travel
    to reach an appointment in another comune.
    """
    workflow = {
        'comune': {
            'handler': step_comune,
            'next': 'comune_confirm'
        },
        'comune_confirm': {
            'handler': step_comune_confirm,
            'next': 'distance',
            'transient': True
        },
        'distance': {
            'handler': step_distance,
            'next': 'distance_confirm'
        },
        'distance_confirm': {
            'handler': step_distance_confirm,
            'next': 'forced_comuni',
            'transient': True,
            'suppress_context': True
        },
        'forced_comuni': {
            'handler': step_forced_comuni,
            'next': None,
            'suppress_context': True
        }
    }

    config = LocationPickMenu(workflow, 'comune', '', 4).run()

    if config:
        return Location(config['comune'], float(config['distance']),
                        config['forced_comuni'])
    return Location('mock', 0.0, [])
    