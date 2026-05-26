# Shift2Calendar

---

- [Shift2Calendar](#shift2calendar)
  - [Introduzione](#introduzione)
  - [Origine Del Progetto](#origine-del-progetto)
  - [Funzionalita](#funzionalita)
  - [Requisiti](#requisiti)
  - [Struttura Excel](#struttura-excel)
  - [Configurazione Turni](#configurazione-turni)
  - [Utilizzo](#utilizzo)
  - [Compatibilita Calendari](#compatibilita-calendari)
  - [Output](#output)
  - [Problemi Comuni](#problemi-comuni)
  - [Licenza](#licenza)

---

## Introduzione

Shift2Calendar converte un file Excel con turni di lavoro in un calendario `.ics` importabile su iOS, Android, Google Calendar, Apple Calendar, Outlook e altre app compatibili con lo standard iCalendar.

Il flusso principale e diretto:

```text
turni.xlsx -> calendar.ics
```

Il CSV non e necessario. Puo essere esportato solo quando serve controllare o riutilizzare i dati intermedi.

## Origine Del Progetto

Shift2Calendar nasce dall'unione di due progetti precedenti:

- [TurniCalendar](https://github.com/mauromarzocca/TurniCalendar): conversione da file Excel dei turni a CSV strutturato.
- [CSVtoCalendar](https://github.com/mauromarzocca/CSVtoCalendar): conversione da CSV eventi a calendario ICS.

Questo progetto riunisce le due funzionalita in un unico flusso diretto, mantenendo il CSV come esportazione opzionale.
In questo nuovo progetto, non è più necessario.

## Funzionalita

- Conversione da Excel (`.xlsx`) a calendario ICS
- Supporto a piu mesi nello stesso file
- Riconoscimento del mese tramite prime 3 lettere
- Mapping turni configurabile:
  - `M` -> Mattina
  - `P` -> Pomeriggio
  - `N` -> Notturno
  - `D` -> Diurno
  - `C` -> Corsi
  - `Fe` -> Ferie
- Gestione automatica dei turni notturni che terminano il giorno successivo
- UID stabile per ogni evento, utile quando si reimporta il calendario
- Fuso orario configurabile
- Esportazione CSV opzionale

## Requisiti

- Python 3.8+
- Dipendenze Python:
  - pandas
  - openpyxl
  - ics
  - pytz

Installa le dipendenze:

```bash
pip install -r requirements.txt
```

## Struttura Excel

Lo script si aspetta questa struttura:

| Riga | Contenuto                                   |
|------|---------------------------------------------|
| 0    | Mese, es. "Marzo" o "Aprile"                |
| 1    | Giorni settimana                            |
| 2    | Giorni numerici                             |
| 3    | Turni, es. `M`, `P`, `N`, `D`, `C`, `Fe`    |

Sono supportati anche piu mesi sulla stessa riga: quando lo script trova un nuovo mese, lo usa per le colonne successive.

## Configurazione Turni

Gli orari sono definiti in `shifts.json`:

```json
{
    "Mattina": "06:00 - 14:00",
    "Pomeriggio": "14:00 - 22:00",
    "Notturno": "22:00 - 06:00",
    "Diurno": "09:00 - 17:00",
    "Corsi": "09:00 - 18:00",
    "Ferie": "00:00 - 23:59"
}
```

Il turno notturno viene gestito automaticamente: se l'orario di fine e minore o uguale all'orario di inizio, la fine viene spostata al giorno successivo.

## Utilizzo

Uso standard:

```bash
python main.py
```

Questo comando legge `turni.xlsx` e genera `calendar.ics`.

Con percorsi personalizzati:

```bash
python main.py --input turni.xlsx --output calendar.ics --shifts shifts.json
```

Con anno e fuso orario:

```bash
python main.py --year 2026 --timezone Europe/Rome
```

Esportare anche il CSV:

```bash
python main.py --export-csv
```

Oppure scegliendo il nome del CSV:

```bash
python main.py --export-csv --csv-output events.csv
```

## Compatibilita Calendari

Il file `.ics` generato usa lo standard iCalendar ed e compatibile con:

- Apple Calendar su iPhone, iPad e macOS
- Google Calendar su Android e web
- Outlook
- altre app che importano file `.ics`

Per una buona compatibilita vengono impostati:

- `DTSTART` e `DTEND`
- `SUMMARY`
- `UID` stabile
- `DTSTAMP`
- orari localizzati nel fuso configurato

## Output

Esempio di calendario generato:

```ics
BEGIN:VEVENT
SUMMARY:Mattina
DTSTART:20260417T040000Z
DTEND:20260417T120000Z
UID:...@shift2calendar.local
END:VEVENT
```

Gli orari possono apparire in UTC nel file ICS, ma le app calendario li mostrano nel fuso locale corretto.

## Problemi Comuni

- `turni.xlsx` non trovato: metti il file nella cartella del progetto o usa `--input`.
- Calendario vuoto: controlla che i turni siano nella riga 3 e usino `M`, `P`, `N`, `D`, `C`, `Fe`.
- Turno saltato: aggiungi il turno mancante in `shifts.json`.
- Anno sbagliato: specifica l'anno con `--year`.

## Licenza

MIT
