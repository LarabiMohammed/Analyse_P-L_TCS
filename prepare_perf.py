"""
Extrait les indicateurs de performance depuis "Mise à plat base de données CDT.xlsx"
et génère data_perf_2025.csv prêt à croiser avec data_synthese.csv
"""
import openpyxl, csv, sys, re

# ── Mapping noms de sites (Base de données → P&L) ───────────────────────────
SITE_MAP = {
    'Coueron':             'Nantes',
    'Paris XV':            'Paris 15',
    'Portes les Valences': 'Portes les Valences',
    'Saran':               'Saran',
    'Le Havre':            'Le Havre',
    'Amiens':              'Amiens',
    'Sevran':              'Sevran',
    'Chézy':               'Chézy',
    'Bègles':              'Bègles',
    'Montpellier':         'Montpellier',
    'Millau':              'Millau',
}
SKIP_SITES = {'Vaux le Pénil'}

# ── Indicateurs à extraire (label exact dans colonne A → nom colonne CSV) ───
# Format : (label_substring, nom_csv, type)
# type = 'pct' | 'float' | 'int'
INDICATORS = [
    ('Tonnages entrants (t)',                    'Tonnage_entrant',          'float'),
    ('Heure de fonctionnement',                  'Heures_fonctionnement',    'float'),
    ('Dispo globale',                            'Dispo_globale',            'pct'),
    ('Dispo process',                            'Dispo_process',            'pct'),
    ('Taux de refus sortant',                    'Taux_refus_sortant',       'pct'),
    ('Taux de valorisable dans',                 'Taux_valorisable',         'pct'),
    ('capacité réglemnatire',                    'Capacite_reglementaire',   'float'),
    ('Débit Nominal',                            'Debit_nominal_t_h',        'float'),
    ('Elec (kWh/an) / T',                        'Elec_kWh_par_t',           'float'),
    ('GNR L/T triée',                            'GNR_L_par_t',              'float'),
    ('Nombre de postes',                         'Nb_postes',                'int'),
    ('Nombre de TOs',                            'Nb_TOs',                   'int'),
    ('Nombre de robots',                         'Nb_robots',                'int'),
    ('Fin du contrat en cours',                  'Fin_contrat',              'float'),
]

def parse_val(raw, typ):
    """Convertit une valeur brute (str ou numérique) selon le type attendu."""
    if raw is None:
        return ''
    s = str(raw).strip().replace('\xa0', '').replace(' ', '')
    # Pourcentage : '81,5%' ou '0.815' ou '0,815'
    if typ == 'pct':
        s = s.replace('%', '').replace(',', '.')
        try:
            v = float(s)
            # Si déjà en décimal (ex: 0.91) → convertir en %
            if v <= 1.5:
                v *= 100
            return round(v, 2)
        except:
            return ''
    elif typ in ('float', 'int'):
        s = s.replace(',', '.')
        try:
            v = float(s)
            return int(v) if typ == 'int' else round(v, 4)
        except:
            return ''
    return s

def main():
    wb = openpyxl.load_workbook(
        'Mise à plat base de données CDT.xlsx',
        read_only=True, data_only=True
    )
    sh = wb['Base de données']
    rows = list(sh.iter_rows(values_only=True))

    # ── Lire l'en-tête (ligne 1) pour récupérer les sites ──────────────────
    header = rows[0]
    site_cols = {}   # col_index → nom normalisé
    for ci, cell in enumerate(header):
        if cell is None:
            continue
        name = str(cell).strip()
        if name in SKIP_SITES:
            continue
        if name in SITE_MAP:
            site_cols[ci] = SITE_MAP[name]

    print(f"Sites trouvés : {list(site_cols.values())}")

    # ── Construire un dict indicateur → ligne ──────────────────────────────
    ind_rows = {}   # nom_csv → (row_index, type)
    for ri, row in enumerate(rows):
        if row[0] is None:
            continue
        label = str(row[0]).strip()
        for substr, nom_csv, typ in INDICATORS:
            if substr.lower() in label.lower() and nom_csv not in ind_rows:
                ind_rows[nom_csv] = (ri, typ)
                break

    print(f"Indicateurs trouvés : {list(ind_rows.keys())}")
    missing = [n for _, n, _ in INDICATORS if n not in ind_rows]
    if missing:
        print(f"⚠️  Indicateurs non trouvés : {missing}")

    # ── Construire les lignes de sortie ────────────────────────────────────
    output = []
    for ci, site in site_cols.items():
        rec = {'Site': site, 'Annee': 2025}
        for nom_csv, (ri, typ) in ind_rows.items():
            raw = rows[ri][ci] if ci < len(rows[ri]) else None
            rec[nom_csv] = parse_val(raw, typ)

        # Calculer taux d'utilisation capacité
        tn = rec.get('Tonnage_entrant', '')
        cap = rec.get('Capacite_reglementaire', '')
        if tn != '' and cap != '' and cap > 0:
            rec['Taux_utilisation_capacite'] = round(float(tn) / float(cap) * 100, 1)
        else:
            rec['Taux_utilisation_capacite'] = ''

        output.append(rec)

    # ── Écrire le CSV ──────────────────────────────────────────────────────
    cols = ['Site', 'Annee'] + [n for _, n, _ in INDICATORS] + ['Taux_utilisation_capacite']
    out_file = 'data_perf_2025.csv'
    with open(out_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(output)

    print(f"\n✅  {out_file} — {len(output)} sites")
    print("\nAperçu :")
    for rec in output:
        print(f"  {rec['Site']:22} | Dispo={rec.get('Dispo_globale','?'):5}% | "
              f"Refus={rec.get('Taux_refus_sortant','?'):5}% | "
              f"Utilisation={rec.get('Taux_utilisation_capacite','?'):5}% | "
              f"Elec={rec.get('Elec_kWh_par_t','?'):6} kWh/t")

if __name__ == '__main__':
    main()
