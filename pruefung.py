"""Soll-Ist-Vergleich für DACHSER-Frachtrechnungen (JTJ Sonneborn / Velux).

Erkenntnisse aus echten Monatsdateien:
- Leistungsart 107 = Fracht ab Werk bis Empfangsort [2][3]
- Leistungsart 283 = Treibstoffzuschlag [2][3]
- Der Treibstoffzuschlag-Satz ist NICHT konstant: 7,60% im August [1], 10,97% im Mai [3].
  -> Prozentsatz wird je Rechnung dynamisch aus dem Tarif-Feld gelesen, nicht hartcodiert!
- Positionen ohne Tarif-Code und mit Kommentar wie "SOFA" sind Sonderfälle
  (Pauschalpreise, kein Tarifvergleich, kein Dieselzuschlag).
- Tarif-Code "Minimum" markiert Mindestgebühren (z.B. Produktzuschlag 328).
"""
import re
import pandas as pd
from tarife import ermittle_zone, ermittle_soll_mit_fallback

TOLERANZ_EUR = 0.05


def parse_prozentsatz(tarif_feld: str) -> float | None:
    """Extrahiert z.B. '7,60%' -> 0.076 oder '10,97%' -> 0.1097."""
    if not isinstance(tarif_feld, str):
        return None
    m = re.match(r"^\s*([\d,.]+)\s*%\s*$", tarif_feld)
    if not m:
        return None
    zahl = m.group(1).replace(",", ".")
    return float(zahl) / 100.0


def pruefe_rechnung(pruefung_df: pd.DataFrame, matrizen: dict) -> pd.DataFrame:
    """Führt den vollständigen Soll-Ist-Vergleich auf dem 'Prüfung'-Sheet durch."""
    ergebnisse = []

    # Gruppieren nach Rechnungsposition, um Fracht (107) und Zuschlag (283) zu verknüpfen
    gruppen = pruefung_df.groupby("Rechnungsposition")

    for pos, gruppe in gruppen:
        fracht_zeile = gruppe[gruppe["Leistungsart"] == "107"]
        zuschlag_zeile = gruppe[gruppe["Leistungsart"] == "283"]

        for _, row in fracht_zeile.iterrows():
            tarif = row.get("Tarif", "")
            cbm_gerundet = row.get("kg/cbm runden", 0)
            produktname = row.get("Produktname", "")
            betrag_ist = row.get("Betrag", 0)
            kommentar_original = row.get("Kommentare", "")

            # Sonderfall: kein Tarif-Code -> Pauschalpreis (z.B. "SOFA"), nicht prüfbar
            if not tarif or str(tarif).strip() == "":
                ergebnisse.append({
                    "Rechnungsposition": pos,
                    "Leistungsart": "107 (Fracht)",
                    "Produkt": produktname,
                    "Ist-Betrag": betrag_ist,
                    "Soll-Betrag": None,
                    "Differenz": None,
                    "Verwendete Matrix": None,
                    "Status": "Sonderfall",
                    "Kommentar": kommentar_original or "Pauschalpreis ohne Tarif-Code – manuelle Prüfung",
                })
                continue

            try:
                zone = ermittle_zone(row.get("PLZ") or row.get("Empfänger PLZ"))
            except KeyError:
                zone = None

            soll, verwendete_matrix = (None, None)
            if zone is not None:
                soll, verwendete_matrix = ermittle_soll_mit_fallback(
                    cbm_gerundet, zone, produktname, matrizen
                )

            if soll is None:
                status, kommentar = "Nicht prüfbar", "Keine passende Tarifstaffel gefunden (ggf. >25 QBM = 1 FTL-Sonderregel)"
                diff = None
            else:
                diff = round(betrag_ist - soll, 2)
                if abs(diff) <= TOLERANZ_EUR:
                    status, kommentar = "OK", ""
                else:
                    status, kommentar = "Abweichung", f"Ist weicht {diff:+.2f} € vom Tarif ({verwendete_matrix}) ab"

            ergebnisse.append({
                "Rechnungsposition": pos,
                "Leistungsart": "107 (Fracht)",
                "Produkt": produktname,
                "Ist-Betrag": betrag_ist,
                "Soll-Betrag": round(soll, 2) if soll is not None else None,
                "Differenz": diff,
                "Verwendete Matrix": verwendete_matrix,
                "Status": status,
                "Kommentar": kommentar,
            })

            # --- Dieselzuschlag (283) separat prüfen: dynamischer Prozentsatz je Rechnung ---
            if not zuschlag_zeile.empty:
                z_row = zuschlag_zeile.iloc[0]
                z_tarif = z_row.get("Tarif", "")
                z_betrag_ist = z_row.get("Betrag", 0)
                prozentsatz = parse_prozentsatz(z_tarif)

                if prozentsatz is None:
                    z_status, z_kommentar = "Sonderfall", "Kein prozentualer Tarif – manuell prüfen"
                    z_diff = None
                else:
                    z_soll = round(betrag_ist * prozentsatz, 2)
                    z_diff = round(z_betrag_ist - z_soll, 2)
                    if abs(z_diff) <= TOLERANZ_EUR:
                        z_status, z_kommentar = "OK", ""
                    else:
                        z_status, z_kommentar = (
                            "Abweichung",
                            f"Dieselzuschlag {z_tarif} ergibt Soll={z_soll:.2f} €, Ist={z_betrag_ist:.2f} €",
                        )

                ergebnisse.append({
                    "Rechnungsposition": pos,
                    "Leistungsart": "283 (Diesel)",
                    "Produkt": produktname,
                    "Ist-Betrag": z_betrag_ist,
                    "Soll-Betrag": round(betrag_ist * prozentsatz, 2) if prozentsatz else None,
                    "Differenz": z_diff,
                    "Verwendete Matrix": f"{tarif}% (dynamisch aus Rechnung)" if prozentsatz else None,
                    "Status": z_status,
                    "Kommentar": z_kommentar,
                })

    return pd.DataFrame(ergebnisse)
