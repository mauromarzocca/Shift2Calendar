import argparse
import csv
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd
import pytz
from ics import Calendar, Event


DEFAULT_INPUT_FILE = "turni.xlsx"
DEFAULT_ICS_FILE = "calendar.ics"
DEFAULT_CSV_FILE = "events.csv"
DEFAULT_SHIFTS_FILE = "shifts.json"
DEFAULT_TIMEZONE = "Europe/Rome"

MONTHS = {
    "gen": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "mag": "05",
    "giu": "06",
    "lug": "07",
    "ago": "08",
    "set": "09",
    "ott": "10",
    "nov": "11",
    "dic": "12",
}

SHIFT_MAP = {
    "m": "Mattina",
    "p": "Pomeriggio",
    "n": "Notturno",
    "d": "Diurno",
    "c": "Corsi",
    "fe": "Ferie",
}


@dataclass(frozen=True)
class ShiftEvent:
    name: str
    date: str
    shift: str


def parse_args():
    parser = argparse.ArgumentParser(
        description="Converte un file Excel con turni di lavoro in un calendario ICS."
    )
    parser.add_argument("-i", "--input", default=DEFAULT_INPUT_FILE, help="File Excel dei turni.")
    parser.add_argument("-o", "--output", default=DEFAULT_ICS_FILE, help="File ICS da generare.")
    parser.add_argument("--shifts", default=DEFAULT_SHIFTS_FILE, help="File JSON con gli orari dei turni.")
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE, help="Fuso orario del calendario.")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Anno da usare per le date.")
    parser.add_argument("--export-csv", action="store_true", help="Esporta anche il CSV degli eventi.")
    parser.add_argument("--csv-output", default=DEFAULT_CSV_FILE, help="File CSV da generare con --export-csv.")
    return parser.parse_args()


def detect_month(cell_value, current_month):
    if pd.isna(cell_value):
        return current_month

    text = str(cell_value).lower()
    words = text.replace("-", " ").replace("/", " ").replace(":", " ").split()

    for word in words:
        key = word[:3]
        if key in MONTHS:
            return MONTHS[key]

    return current_month


def events_from_excel(input_file, year):
    df = pd.read_excel(input_file, header=None)

    months_row = df.iloc[0]
    days = df.iloc[2]
    shifts = df.iloc[3]

    current_month = None
    short_year = str(year)[-2:]
    events = []

    for index in range(len(days)):
        current_month = detect_month(months_row[index], current_month)
        if not current_month:
            continue

        day = days[index]
        if pd.isna(day):
            continue

        try:
            day = int(day)
        except (TypeError, ValueError):
            continue

        raw_shift = str(shifts[index]).strip().lower()
        if raw_shift not in SHIFT_MAP:
            continue

        shift = SHIFT_MAP[raw_shift]
        name = "Notte" if shift == "Notturno" else shift
        date = f"{day:02d}/{current_month}/{short_year}"
        events.append(ShiftEvent(name=name, date=date, shift=shift))

    return events


def load_shifts(shift_file):
    with open(shift_file, "r", encoding="utf-8") as file:
        return json.load(file)


def stable_uid(shift_event):
    value = f"{shift_event.name}|{shift_event.date}|{shift_event.shift}"
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return f"{digest}@shift2calendar.local"


def create_calendar(events, shifts, timezone_name):
    calendar = Calendar()
    local_timezone = pytz.timezone(timezone_name)
    now = datetime.now(local_timezone)

    for shift_event in events:
        shift_times = shifts.get(shift_event.shift)
        if not shift_times:
            print(f"Attenzione: turno '{shift_event.shift}' non trovato. Salto '{shift_event.name}'.")
            continue

        start_time, end_time = shift_times.split(" - ")
        start_datetime = local_timezone.localize(
            datetime.strptime(f"{shift_event.date} {start_time}", "%d/%m/%y %H:%M")
        )
        end_datetime = local_timezone.localize(
            datetime.strptime(f"{shift_event.date} {end_time}", "%d/%m/%y %H:%M")
        )

        if end_datetime <= start_datetime:
            end_datetime += timedelta(days=1)

        event = Event()
        event.name = shift_event.name
        event.begin = start_datetime
        event.end = end_datetime
        event.uid = stable_uid(shift_event)
        event.created = now
        event.dtstamp = now

        calendar.events.add(event)

    return calendar


def write_ics(calendar, output_file):
    with open(output_file, "w", encoding="utf-8") as file:
        file.writelines(calendar)


def write_csv(events, output_file):
    with open(output_file, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Nome", "Data", "Turno"])
        for event in events:
            writer.writerow([event.name, event.date, event.shift])


def main():
    args = parse_args()

    if not os.path.exists(args.input):
        print(f"Errore: {args.input} non trovato.")
        return 1

    if not os.path.exists(args.shifts):
        print(f"Errore: {args.shifts} non trovato.")
        return 1

    shifts = load_shifts(args.shifts)
    events = events_from_excel(args.input, args.year)
    calendar = create_calendar(events, shifts, args.timezone)
    write_ics(calendar, args.output)

    print(f"ICS generato: {args.output} ({len(calendar.events)} eventi)")

    if args.export_csv:
        write_csv(events, args.csv_output)
        print(f"CSV generato: {args.csv_output} ({len(events)} record)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
