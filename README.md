# SaniDrive
Hai prenotato una visita specialistica al CUP ma è tutto pieno?
Con SaniDrive, inserisci Codice Fiscale e NRE nel file `credentials.txt` e controlla automaticamente ogni 30 secondi se si è liberato un posto.

## Requirements
Per usare SaniDrive, devi scaricare ChromeDriver, che trovi [qui](https://googlechromelabs.github.io/chrome-for-testing/). Se non ce l'hai, installa anche Chrome. Assicurati di scaricare la versione di ChromeDriver che corrisponde a quella del browser Chrome che hai installato!
Metti `chromedriver.exe` nella stessa directory in cui si trova `SaniDrive.py`.

Nella stessa directory crea anche il file di testo `credentials.txt` che deve rigorosamente contenere solo due righe: nella prima il tuo Codice Fiscale, nella seconda l'NRE della dua prescrizione.

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