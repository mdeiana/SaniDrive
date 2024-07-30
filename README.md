# SaniDrive
Hai prenotato una visita specialistica al CUP ma è tutto pieno?
Con SaniDrive, inserisci Codice Fiscale e NRE nel file `credentials.txt` e controlla automaticamente ogni 30 secondi se si è liberato un posto.

## Requirements
Per usare SaniDrive devi scaricare ChromeDriver, che trovi [qui](https://googlechromelabs.github.io/chrome-for-testing/). Ti servirà inoltre il browser Chrome. Assicurati di scaricare la versione di ChromeDriver che corrisponde a quella del browser che hai installato!

Metti `chromedriver.exe` nella stessa directory in cui si trova `SaniDrive.py`.
Nella stessa directory crea anche il file di testo `credentials.txt` che deve rigorosamente contenere solo due righe: nella prima il tuo Codice Fiscale, nella seconda l'NRE della tua prescrizione.

Infine, installa i seguenti pacchetti con `pip install`:
```
sys
time
plyer
selenium
```

Esegui SaniDrive.py e vai a fare altro!

## To do
Tanti exception catch, supportare l'inserimento delle credenziali con argomenti direttamente da CLI, supportare invio di email o push di notifica su telefono, supportare diversi siti, inserire euristiche di riserva o più resilienti ad un possibile cambiamento del layout del sito.


### Actual To-do
- [ ] Investigate to see if other pages contain more information. If so:
    - [ ] find a better way of extracting and refreshing info

- [ ] Find a way to catalogue all of it and display changes on terminal
    - [ ] Continuously refresh and find a way to track changes:
          What spots are new, which ones are gone...
        - [ ] bonus points for entry class and methods and shit

- [ ] Investigate for ways to send notifications more effectively
    - [ ] Phone?
    - [ ] Email for sure, come on...

- [ ] Improve feature-set and user-experience
    - [ ] Cli arguments or Interactive options:
      - [ ] Store multiple credential pairs and select which to use
      - [ ] Possibly, make it so an appointment can be selected and
            booked directly from within software
      - [ ] Maybe one day, GUI
    - [ ] Italian localization
