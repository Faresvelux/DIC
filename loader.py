"""Robustes Einlesen der DACHSER-Frachtrechnungsdateien (.xls/.xlsx, DE/EN)."""
import pandas as pd

SPALTEN_MAPPING = {
    "Rechnungsnummer": ["Rechnungsnummer", "Invoice number"],
    "Rechnungsdatum": ["Rechnungsdatum", "Invoice date"],
    "Rechnungssumme": ["Rechnungssumme", "Invoice amount"],
    "Wahrung": ["Wahrung", "Currency"],
    "Rechnungsposition": ["Rechnungsposition", "Invoice position"],
    "Erstauftragsnummer": ["Erstauftragsnummer", "First order number"],
    "Leistungsart": ["Leistungsart", "Service type"],
    "Abrechnungsbasis-1": ["Abrechnungsbasis-1", "Billing basis-1"],
    "Wert Basis-1": ["Wert Basis-1", "Billing basis-1 value"],
    "Abrechnungsbasis-2": ["Abrechnungsbasis-2", "Billing basis-2"],
    "Wert Basis-2": ["Wert Basis-2", "Billing basis-2 value"],
    "Tarif": ["Tarif"],
    "Betrag": ["Betrag", "Amount"],
    "CBM": ["CBM"],
    "kg/cbm runden": ["kg/cbm runden"],
    "Produkt": ["Produkt"],
    "Produktname": ["Produktname"],
    "PLZ": ["PLZ"],
    "Prufung": ["Prufung"],
    "Kommentare": ["Kommentare"],
    "Empfanger PLZ": ["Empfanger PLZ", "Post code recipient", "Recipient post code"],
}

SHEET_ALIASE = {
    "uebersicht": ["Ubersicht", "Summary"],
    "sendungssummen": ["Sendungssummen", "Shipment-summary"],
    "sendungsdetails": ["Sendungsdetails", "Shipment-Details"],
    "auftragsdetails": ["Auftragsdetails", "Order-details"],
    "pruefung": ["Prufung"],
    "kond_be": ["Kond_BE"],
    "kond_be_targoflex": ["Kond_BE_Targoflex"],
    "kond_targospeed10": ["Kond_Targospeed10"],
    "kond_targospeed": ["Kond_Targospeed"],
}


def engine_fuer_datei(dateiname):
    name = dateiname.lower()
    if name.endswith(".xls"):
        return "xlrd"
    if name.endswith(".xlsx"):
        return "openpyxl"
    raise ValueError("Nicht unterstuetztes Format. Bitte .xls oder .xlsx hochladen.")


def lade_alle_sheets(datei):
    engine = engine_fuer_datei(datei.name)
    try:
        xls = pd.ExcelFile(datei, engine=engine)
    except Exception as e:
        raise RuntimeError(
            "Datei konnte nicht gelesen werden (" + str(e) + "). "
            "Bitte pruefen, ob es eine gueltige DACHSER-Exportdatei ist."
        )
    return {name: xls.parse(name, header=0) for name in xls.sheet_names}


def finde_sheet(sheets, schluessel):
    for kandidat in SHEET_ALIASE.get(schluessel, [schluessel]):
        if kandidat in sheets:
            return sheets[kandidat]
    raise KeyError("Sheet fuer '" + schluessel + "' nicht gefunden. Vorhanden: " + str(list(sheets.keys())))


def vereinheitliche_spalten(df):
    umbenennung = {}
    for standard, varianten in SPALTEN_MAPPING.items():
        for v in varianten:
            if v in df.columns:
                umbenennung[v] = standard
                break
    return df.rename(columns=umbenennung)
