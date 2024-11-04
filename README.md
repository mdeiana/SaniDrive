# SaniDrive
Le liste di attesa per la sanità pubblica sono proibitivamente lunghe. Il prossimo appuntamento libero può essere lontano mesi, spesso e volentieri anche più di un anno.

E' però anche vero che c'è sempre la speranza che un posto si liberi perché qualcuno ha disdetto il suo appuntamento, se anche con poco preavviso. Il problema è che per trovarlo, uno dovrebbe controllare costantemente la pagina degli appuntamenti.

Per questo esiste SaniDrive.

Con SaniDrive, puoi impostare interattivamente i dati necessari alla prenotazione di una visita specialistica con ricetta dematerializzata, lasciare che sia SaniDrive a controllare ripetutamente se è disponibile un posto libero, e avere la certezza che appena uno si sarà liberato riceverai un avviso e potrai prenotarlo.

## Requisiti
Per usare SaniDrive devi scaricare ed installare l'ultima versione di Google Chrome.

Sanidrive è un programma scritto con Python. Per poterlo usare, devi installare la suite Python ed accertarti che siano installate tutte le dipendenze di cui SaniDrive necessita. Le dipendenze sono dei pacchetti che potrai installare con un comando una volta che avrai installato Python.

Installa i seguenti pacchetti con `pip install`:
```
plyer, selenium, shutil, requests, bs4
```

SaniDrive funziona grazie a un programma che si chiama ChromeDriver, che deve essere scaricato sul tuo computer ed essere della stessa versione di Google Chrome; normalmente non c'è bisogno che tu te ne preoccupi, perché SaniDrive rileverà la sua assenza e potrà scaricare automaticamente l'ultima versione.

Esegui SaniDrive con `py sanidrive.py` e vai a fare altro!

## Configurazione
E' possibile configurare varie opzioni per ottenere comportamenti diversi da quelli che SaniDrive usa di default. Tieni in mente che tutto ciò che è fondamentale per usare SaniDrive è richiesto interattivamente se le opzioni non sono specificate.

Se si desidera specificare alcune opzioni è possibile ottenere una lista esaustiva di tutto ciò che è configurabile chiamado SaniDrive con l'opzione `--help` o `--aiuto`.

Di seguito è comunque riportato l'output di `py sanidrive.py --aiuto`:
```
Uso: SaniDrive [-h] [--file FILE] [--driver FILE] [--visibile] [--log FILE] [--intervallo SECONDI]
                 [--data [DATA ...]] [--nonstop] [--exec FILE] [--aiuto]

Tieni traccia e avverti automaticamente di posti liberi per una prenotazione al CUP Sardegna

Opzioni:
  -h, --help            show this help message and exit

  --file FILE, -f FILE  Specifica il percorso del file con le credenziali. E' bene usare un percorso assoluto per
                        garantire l'uso del file corretto. Il percorso di default e' "data/credenziali.json",
                        relativamente alla directory da cui e' eseguito SaniDrive.

  --driver FILE         Specifica il percorso dell'eseguibile di ChromeDriver. E' bene usare un percorso assoluto per
                        garantire l'uso del file corretto. Il percorso di default e' "data/chromedriver-
                        win64/chromedriver.exe", relativamente alla directory da cui e' eseguito SaniDrive. Scarica la
                        versione di ChromeDriver che combacia a quella del tuo browser Chrome da
                        https://googlechromelabs.github.io/chrome-for-testing/

  --visibile, --visible, -v
                        Di default, il driver e' eseguito in modalita' headless, ovvero la finestra del browser e'
                        nascosta per evitare di interagirci accidentalmente. Specificare questa opzione la rende
                        visible.

  --log FILE, -l FILE   Specifica il percorso del file in cui salvare il log di ChromeDriver. Se il parametro non e'
                        specificato, i log non sono salvati. Questo parametro e' correntemente disabilitato per un bug
                        in Selenium.

  --intervallo SECONDI, -i SECONDI, --timer SECONDI, -t SECONDI
                        Specifica quanti secondi far passare tra un aggiornamento e il prossimo. L'intervallo di
                        default e' di 30 secondi. Impostare un'attesa troppo breve potrebbe risultare in
                        malfunzionamenti.

  --data [DATA ...], --date [DATA ...], -d [DATA ...], --primadi [DATA ...], --primadel [DATA ...], -p [DATA ...]
                        Specifica una data in uno dei seguenti formati: GG MM AAAA, GG-MM-AAAA, GG/MM/AAAA, oppure GG
                        Mese AAAA. Puoi anche usare AA anziche' AAAA. Ad esempio, date valide sono: 01 01 2025,
                        29-02-2028, 3/4/25, 19 settembre 2025, 7 Ottobre 25, ma NON lo sono 28-02/25 o 28-ottobre-25.
                        Se questa opzione e' usata ed una data e' specificata, solo gli appuntamenti disponibili prima
                        di tale data produrranno una notifica e metteranno in pausa SaniDrive per permettere di
                        procedere con la prenotazione, a meno che l'opzione --nonstop sia specificata. Se invece
                        l'opzione e' usata da sola senza una data, una notifica sara' prodotta ogni volta che viene
                        trovato un appuntamento per un giorno piu' vicino di tutti quelli trovati in precedenza, ma la
                        finestra di ChromeDriver non sara' aperta e SaniDrive continuera' a cercare. Infine, se
                        l'opzione non e' specificata, la data potra' essere scelta interattivamente dopo aver
                        selezionato un'impegnativa da monitorare.

  --nonstop, --nostop, -n
                        Non fermare il programma quando un appuntamento precedente la data scelta con --data e'
                        trovato. La notifica verra' prodotta comunque.

  --exec FILE, -e FILE, --suono FILE, --suoneria FILE, -s FILE, --avviso FILE
                        Specifica il percorso di un file da eseguire quando un appuntamento precedente la data scelta
                        con --data e' trovato. L'utilizzo inteso e' quello di riprodurre un file audio o aprire un
                        collegamento a un video, ma eseguire un file arbitrario puo' essere un modo di estendere le
                        funzionalita' di SaniDrive.

  --aiuto, -a           Scrivi questo messaggio di aiuto ed esci.
```
