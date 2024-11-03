"""Defines global variables and a setter for each variable."""

# Static lookup tables
MONTH = {
    'Gennaio':1, 'Febbraio':2, 'Marzo':3, 'Aprile':4, 'Maggio':5, 'Giugno':6,
    'Luglio':7, 'Agosto':8, 'Settembre':9, 'Ottobre':10, 'Novembre':11, 'Dicembre':12
}
DAYS = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}

# Variables
line_width = 120

# Setters
def set_line_width(n : int) -> None:
    global line_width
    line_width = n