"""Robustes Einlesen der DACHSER-Frachtrechnungsdateien (.xls/.xlsx, DE/EN)."""
import pandas as pd

# Spalten-Mapping: Deutsch <-> Englisch, da DACHSER beide Varianten exportiert
SPALTEN_MAPPING = {
    "Rechnungsnummer": ["Rechnungsnummer", "Invoice number"],
    "Rechnungsdatum": ["Rechnungsdatum", "Invoice date"],
    "Rechnungssumme": ["Rechnungssumme", "Invoice amount"],
    "Währung": ["Währung", "Currency"],
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
    "Prüfung": ["Prüfung"],
    "Kommentare": ["Kommentare"],
    "Empfänger PLZ": ["Empfänger PLZ", "Post code recipient", "Recipient post code"],
}

SHEET_ALIASE = {
    "uebersicht": ["Übersicht", "Summary"],
    "sendungssummen": ["Sendungssummen", "Shipment-summary"],
    "sendungsdetails": ["Sendungsdetails", "Shipment-Details"],
    "auftragsdetails": ["Auftragsdetails", "Order-details"],
    "pruefung": ["Prüfung"],  # bleibt in beiden Sprachversionen deutsch
    "kond_be": ["Kond_BE"],
    "kond_be_targoflex": ["Kond_BE_Targoflex"],
    "kond_targospeed10": ["Kond_Targospeed10"],
    "kond_targospeed": ["Kond_Targospeed"],
}


def engine_fuer_datei(dateiname: str) -> str:
    """xlrd (>=2.x) kann NUR noch .xls lesen, openpyxl NUR .xlsx."""
    name = dateiname.lower()
    if name.endswith(".xls"):
        return "xlrd"
    if name.endswith(".xlsx"):
        return "openpyxl"
    raise ValueError("Nicht unterstütztes Format. Bitte .xls oder .xlsx hochladen.")


def lade_alle_sheets(datei) -> dict:
    engine = engine_fuer_datei(datei.name)
    try:
        xls = pd.ExcelFile(datei, engine=engine)
    except Exception as e:
        raise RuntimeError(
            f"Datei konnte nicht gelesen werden ({e}). "
            "Bitte prüfen, ob es eine gültige DACHSER-Exportdatei ist."
        )
    return {name: xls.parse(name, header=0) for name in xls.sheet_names}


def finde_sheet(sheets: dict, schluessel: str) -> pd.DataFrame:
    for kandidat in SHEET_ALIASE.get(schluessel, [schluessel]):
        if kandidat in sheets:
            return sheets[kandidat]
    raise KeyError(f"Sheet für '{schluessel}' nicht gefunden. Vorhanden: {list(sheets.keys())}")


def vereinheitliche_spalten(df: pd.DataFrame) -> pd.DataFrame:
    """Benennt DE/EN-Spalten auf einen einheitlichen deutschen Standard um."""
    umbenennung = {}
    for standard, varianten in SPALTEN_MAPPING.items():
        for v in varianten:
            if v in df.columns:
                umbenennung[v] = standard
                break
    return df.rename(columns=umbenennung)
    )
