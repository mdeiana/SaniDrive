"""Defines global variables and setters."""

import os
from importlib import resources
from platformdirs import user_data_path

# Static lookup tables
MONTH = {
    'Gennaio':1, 'Febbraio':2, 'Marzo':3, 'Aprile':4, 'Maggio':5, 'Giugno':6,
    'Luglio':7, 'Agosto':8, 'Settembre':9, 'Ottobre':10, 'Novembre':11, 'Dicembre':12
}
DAYS = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}

line_width = 120

data_dir = resources.files('sanidrive').joinpath('data')
appdata_dir = user_data_path('SaniDrive')
driver_dir = user_data_path('SaniDrive').joinpath('chromedriver-win64')

title_path = data_dir.joinpath('title.txt')#.read_text()
audio_path = data_dir.joinpath('emmescingue.mpeg')
creds_path = appdata_dir.joinpath('credenziali.json')
driver_path = driver_dir.joinpath('chromedriver.exe')

# Setters
def set_line_width(n : int) -> None:
    global line_width
    line_width = n