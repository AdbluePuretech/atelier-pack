# -*- coding: utf-8 -*-
"""Balayage d'integrite : les defauts que la profession cherche en premier.

Ce sont les controles d'un model audit classique, ceux qui remplissent
l'issues log d'Operis ou de Mazars. Ils ne disent pas si le modele calcule
la bonne chose - ca, c'est la revue des familles - ils disent si le classeur
est sain comme objet.

Chaque controle rend une liste de cellules fautives, jamais un avis. Un
controle qui ne trouve rien affiche OK ; un controle qui trouve affiche le
compte, la ventilation et un echantillon.

Usage :
    python integrite.py "Classeur.xlsx" [--json rapport.json] [--inputs "01. Input_Sheet"]
"""
import argparse
import collections
import json
import re
import sys

import noyau

# Litteraux tolerables dans une formule : les constantes mathematiques et
# calendaires qu'on n'exige de personne qu'il parametre.
LITTERAUX_OK = {"0", "1", "2", "-1", "0.5", "100", "12", "365", "365.25", "360", "4", "3", "1e-06", "1e-07"}

VOLATILES = re.compile(r"\b(NOW|TODAY|RAND|RANDBETWEEN|OFFSET|INDIRECT|CELL|INFO)\s*\(", re.I)
MASQUE_ERREUR = re.compile(r"\b(IFERROR|IFNA|ISERROR|ISERR)\s*\(", re.I)
NUM_LITTERAL = re.compile(r"(?<![A-Za-z0-9_.$!])(-?[0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?)(?![0-9A-Za-z_.])")
ERREURS_XL = ("#REF!", "#VALUE!", "#DIV/0!", "#N/A", "#NAME?", "#NULL!", "#NUM!", "#SPILL!", "#CALC!")
SOMME = re.compile(r"\bSUM\s*\(", re.I)


class Rapport:
    def __init__(self):
        self.controles = []

    def poser(self, cle, libelle, fautifs, gravite="significatif", note="", ventilation=None):
        self.controles.append({
            "cle": cle,
            "libelle": libelle,
            "gravite": gravite,
            "compte": len(fautifs),
            "ok": not fautifs,
            "note": note,
            # la ventilation se calcule sur la liste COMPLETE, l'echantillon
            # seul est tronque : un decompte fait sur un echantillon ment.
            "ventilation": ventilation if ventilation is not None else dict(
                collections.Counter(
                    x.split("!")[0] if isinstance(x, str) and "!" in x else "-"
                    for x in fautifs).most_common(10)),
            "fautifs": fautifs[:60],
        })

    def afficher(self):
        larg = max(len(c["libelle"]) for c in self.controles)
        ko = 0
        for c in self.controles:
            etat = "OK  " if c["ok"] else "FAUT"
            if not c["ok"]:
                ko += 1
            n = "" if c["ok"] else f"{c['compte']:>7,}"
            print(f"  [{etat}] {c['cle']:<5} {c['libelle']:<{larg}} {n}")
            if c["note"]:
                print(f"           {c['note']}")
        print()
        print(f"  {len(self.controles) - ko}/{len(self.controles)} controles passes")
        return ko

    def detail(self, n=6):
        for c in self.controles:
            if c["ok"] or not c["fautifs"]:
                continue
            print()
            print(f"--- {c['cle']} {c['libelle']}  ({c['gravite']}, {c['compte']:,})")
            for f, k in c["ventilation"].items():
                print(f"      {f:<34} {k:>6}")
            print("      -- echantillon --")
            for x in c["fautifs"][:n]:
                print(f"      {x}")


def deduire_feuille_inputs(chemin, defaut="01. Input_Sheet"):
    """La feuille d'hypotheses, reconnue a ce qu'elle EST.

    Se caler sur un NOM ne marche que sur le classeur qui a inspire la
    constante. Mesure une fois : l'outil cherchait `01. Input_Sheet`, le
    classeur portait `01. Input Sheet` -- une espace au lieu d'un souligne --
    et les 372 hypotheses legitimes sont ressorties en 372 defauts critiques,
    pendant que I18 rendait vert sans avoir rien regarde. Un vert obtenu sans
    avoir essaye.

    La regle qui tient : une feuille d'hypotheses, c'est celle ou pointent les
    plages nommees. A defaut de plages nommees, celle qui porte le plus de
    valeurs en dur. Le nom ne sert que de dernier recours.
    """
    import re as _re
    from collections import Counter
    import openpyxl as _ox
    try:
        wb = _ox.load_workbook(chemin, read_only=False, data_only=True)
    except Exception as exc:
        # Ne PAS retomber en silence : un defaut choisi faute de mieux se lit
        # ensuite comme un choix, et c'est ce genre de silence qui a produit
        # 372 faux defauts.
        print(f"  deduction impossible ({exc}) -- on retombe sur {defaut}")
        return defaut
    noms = Counter()
    try:
        items = list(wb.defined_names.items())
    except AttributeError:
        items = [(d.name, d) for d in wb.defined_names.definedName]
    for _, dn in items:
        texte = getattr(dn, "attr_text", "") or ""
        m = _re.match(r"^'?([^'!]+)'?!", texte)
        if m and m.group(1) in wb.sheetnames:
            noms[m.group(1)] += 1
    if noms:
        return noms.most_common(1)[0][0]
    durs = Counter()
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, (int, float)):
                    durs[ws.title] += 1
    if durs:
        return durs.most_common(1)[0][0]
    return defaut


def autotest():
    """Les motifs sur lesquels reposent les vingt controles.

    Chacun a deja rendu un faux verdict au moins une fois : I13 quand une ligne
    de controle etait prise pour une SUM tronquee, I2 quand un litteral dans une
    adresse comptait comme une constante enfouie.
    """
    cas = [
        (MASQUE_ERREUR, "=IFERROR(A1/B1,0)", True, "I4 ne voit plus un IFERROR"),
        (MASQUE_ERREUR, "=A1/B1", False, "I4 crie sur une division saine"),
        (VOLATILES, "=OFFSET(A1,1,0)", True, "I5 ne voit plus une fonction volatile"),
        (VOLATILES, "=SUM(A1:A9)", False, "I5 crie sur une somme"),
        (SOMME, "=SUM(D8:D15)", True, "I13 ne voit plus une SUM"),
        (NUM_LITTERAL, "=A1*0.15", True, "I2 ne voit plus un litteral enfoui"),
    ]
    for motif, formule, attendu, message in cas:
        if bool(motif.search(formule)) != attendu:
            raise SystemExit("ARRET - le controle est casse : " + message
                             + "  (" + formule + ")")


def balayer(chemin, feuille_inputs="01. Input_Sheet"):
    C = noyau.Classeur(chemin)
    R = Rapport()
    L = noyau.libelle

    # --- I1 valeurs en dur hors feuille d'hypotheses ---------------------
    durs = [L(k) for k in C.durs if k[0] != feuille_inputs]
    R.poser("I1", "aucune valeur en dur hors de la feuille d'hypotheses", durs,
            "critique", "une constante saisie dans le calcul echappe a toute sensibilite")

    # --- I2 litteraux enfouis dans les formules ---------------------------
    # Le compte de cellules ne dit rien d'utile : une constante repetee sur
    # 1 800 cellules reste UNE constante a tracer. On ventile donc par valeur.
    enfouis = []
    par_valeur = collections.Counter()
    for k, f in C.formules.items():
        for m in NUM_LITTERAL.finditer(f):
            t = m.group(1)
            if t in LITTERAUX_OK or abs(float(t)) < 1e-5:
                continue
            par_valeur[t] += 1
            enfouis.append(f"{L(k)}  ->  {t}  dans  {f[:70]}")
            break
    R.poser("I2", "aucun litteral non trivial enfoui dans une formule", enfouis,
            "significatif",
            f"{len(par_valeur)} constantes distinctes ; un parametre code en dur "
            f"ne se flexe pas et ne se trace pas",
            ventilation=dict(par_valeur.most_common(12)))

    # --- I3 valeurs d'erreur en cache -------------------------------------
    err = [f"{L(k)} = {v}" for k, v in C.valeurs.items()
           if isinstance(v, str) and v in ERREURS_XL]
    R.poser("I3", "aucune valeur d'erreur dans le cache de calcul", err, "critique")

    # --- I4 masquage d'erreur ---------------------------------------------
    masques = [L(k) for k, f in C.formules.items() if MASQUE_ERREUR.search(f)]
    R.poser("I4", "aucun masquage d'erreur (IFERROR, IFNA, ISERROR)", masques,
            "critique", "un IFERROR cache le defaut au lieu de le signaler")

    # --- I5 fonctions volatiles ou fragiles --------------------------------
    vol = [f"{L(k)}  {VOLATILES.search(f).group(1).upper()}"
           for k, f in C.formules.items() if VOLATILES.search(f)]
    R.poser("I5", "aucune fonction volatile ou indirecte", vol, "significatif",
            "NOW, TODAY, RAND rendent le classeur non reproductible ; OFFSET et "
            "INDIRECT le rendent non auditable")

    # --- I6 liens externes --------------------------------------------------
    ext = [L(k) for k, f in C.formules.items() if "[" in f and "]" in f.split("!")[0]]
    try:
        ext += [f"lien de classeur : {x.Target}" for x in C.wf._external_links]
    except Exception:
        pass
    R.poser("I6", "aucun lien vers un classeur externe", ext, "critique")

    # --- I7 references vers une cellule vide ---------------------------------
    connues = set(C.formules) | set(C.durs) | set(C.textes) | set(C.dates)
    vides = []
    for k, f in C.formules.items():
        for r in C.references(k, f):
            if r[0] in C.feuilles and r not in connues:
                vides.append(f"{L(k)}  ->  {L(r)} (vide)")
                break
    R.poser("I7", "aucune formule ne lit une cellule vide", vides, "significatif",
            "une reference vide vaut zero en silence : c'est le defaut le plus "
            "frequent apres une insertion de ligne")

    # --- I8 nombres stockes en texte -----------------------------------------
    txt_num = [f"{L(k)} = {v!r}" for k, v in C.textes.items()
               if re.fullmatch(r"\s*-?[0-9][0-9 .,]*%?\s*", v or "")]
    R.poser("I8", "aucun nombre stocke en texte", txt_num, "significatif")

    # --- I9 plages nommees mortes ou vides -------------------------------------
    utilises = set()
    for f in C.formules.values():
        for m in noyau.JETON.finditer(f):
            if m.lastgroup == "nom":
                utilises.add(m.group())
    mortes = [n for n in C.noms if n not in utilises]
    R.poser("I9", "aucune plage nommee inutilisee", mortes, "presentationnel")
    creuses = [n for n, cibles in C.noms.items() if not cibles]
    R.poser("I10", "aucune plage nommee non resolue", creuses, "critique")

    # --- I11 feuilles, lignes, colonnes masquees --------------------------------
    caches = []
    for ws in C.wf.worksheets:
        if ws.sheet_state != "visible":
            caches.append(f"feuille masquee : {ws.title}")
        for dim in list(ws.row_dimensions.values()):
            if dim.hidden:
                caches.append(f"{ws.title} ligne {dim.index} masquee")
        for dim in list(ws.column_dimensions.values()):
            if dim.hidden:
                caches.append(f"{ws.title} colonne {dim.index} masquee")
    R.poser("I11", "rien de masque dans le classeur", caches, "significatif",
            "on n'audite pas ce qu'on ne voit pas")

    # --- I12 cellules fusionnees dans une zone de calcul -------------------------
    fus = []
    for ws in C.wf.worksheets:
        for plage in list(ws.merged_cells.ranges):
            for l in range(plage.min_row, plage.max_row + 1):
                for c in range(plage.min_col, plage.max_col + 1):
                    if (ws.title, l, c) in C.formules:
                        fus.append(f"{ws.title}!{plage}")
                        break
    R.poser("I12", "aucune cellule fusionnee sur une zone de calcul", sorted(set(fus)),
            "significatif")

    # Le libelle d'une ligne, lu dans la premiere colonne de texte a sa gauche.
    # Partage par I13, I17 et I19 : les trois ne se prononcent qu'en sachant si
    # la ligne annonce un controle. La logique etait ecrite deux fois ; elle
    # manquait a I13, et c'est ce qui lui faisait rendre des fausses alertes.
    MOTS_CONTROLE = ("must be nil", "violation", "controlled to nil", "tie -",
                     "check", "residual", "target nil")

    def etiquette_de(k):
        for col in (3, 2, 4):
            v = C.textes.get((k[0], k[1], col))
            if v and not str(v).startswith("="):
                return str(v)
        return ""

    def est_ligne_de_controle(k):
        e = etiquette_de(k).lower()
        return any(m in e for m in MOTS_CONTROLE)

    # --- I13 SUM qui s'arrete avant la fin d'un bloc contigu ----------------------
    # Une ligne de CONTROLE exclut deliberement une cellule de son total :
    # `=SUM(D8:D15)-D16` retranche le 16 expres, et le signaler comme plage
    # tronquee est une fausse alerte. Elles sont exemptees et comptees a part,
    # jamais silencieusement ignorees.
    courts = []
    exemptes = 0
    for k, f in C.formules.items():
        if not SOMME.search(f):
            continue
        if est_ligne_de_controle(k):
            exemptes += 1
            continue
        for m in re.finditer(r"SUM\(\s*(\$?[A-Z]{1,3}\$?[0-9]+):(\$?[A-Z]{1,3}\$?[0-9]+)\s*\)", f, re.I):
            try:
                l1, c1 = noyau._pos(m.group(1))
                l2, c2 = noyau._pos(m.group(2))
            except Exception:
                continue
            if c1 != c2:
                continue
            haut, bas = min(l1, l2), max(l1, l2)
            voisin_haut = (k[0], haut - 1, c1)
            voisin_bas = (k[0], bas + 1, c1)
            for v, sens in ((voisin_haut, "au-dessus"), (voisin_bas, "en dessous")):
                if v in C.formules or v in C.durs:
                    if v != k:
                        courts.append(f"{L(k)}  SUM({m.group(1)}:{m.group(2)}) "
                                      f"laisse {L(v)} {sens} hors du total")
                        break
    R.poser("I13", "aucune plage SUM qui laisse une cellule du bloc dehors",
            sorted(set(courts)), "critique",
            "le defaut classique : une ligne ajoutee que le total n'atteint pas"
            + (f" ; {exemptes} formule(s) exemptee(s) sur des lignes de controle, "
               "qui retranchent une cellule expres" if exemptes else ""))

    # --- I18 hypotheses mortes : posees sur la feuille, lues par personne -----
    # Une entree que rien ne consomme ment sur ce que le modele prend en
    # compte. Le lecteur la flexe, rien ne bouge, et il conclut que le modele
    # y est insensible - alors qu'il ne la lit tout simplement pas.
    # Le controle porte sur la CELLULE, pas sur la plage nommee : une entree
    # peut etre lue par reference directe sans que son nom serve jamais.
    # On compte par LIGNE, pas par cellule. Une hypothese s'etale souvent sur
    # plusieurs colonnes - une valeur par cas, ou une colonne d'affichage a
    # cote de la colonne lue. Compter les cellules gonfle le chiffre d'un
    # ordre de grandeur et noie les vraies hypotheses mortes : seule une ligne
    # dont AUCUNE cellule n'est lue en est une.
    lues = set()
    for k, f in C.formules.items():
        for r in C.references(k, f):
            lues.add(r)
    par_ligne = collections.defaultdict(lambda: {"lues": 0, "mortes": []})
    for k, v in C.durs.items():
        if k[0] != feuille_inputs:
            continue
        e = par_ligne[k[1]]
        if k in lues:
            e["lues"] += 1
        else:
            e["mortes"].append((k, v))
    mortes = []
    for ligne, e in sorted(par_ligne.items()):
        if e["lues"] or not e["mortes"]:
            continue
        etiquette = ""
        for col in (3, 2, 4):
            w = C.textes.get((feuille_inputs, ligne, col))
            if w and not str(w).startswith("="):
                etiquette = str(w)
                break
        if not etiquette:
            continue          # sans libelle, c'est une case de tableau, pas une hypothese
        vals = ", ".join(f"{L(k)}={v!r}" for k, v in sorted(e["mortes"])[:3])
        mortes.append(f"[{etiquette.strip()[:52]}]  {vals}")
    R.poser("I18", "aucune hypothese posee que le modele ne lit pas", mortes,
            "significatif",
            "une entree que rien ne consomme ment sur ce que le modele prend "
            "en compte : on la flexe, rien ne bouge, et on croit le modele "
            "insensible alors qu'il ne la lit pas")

    # --- I17 une ligne de controle neutralisee par une multiplication par zero
    # `0*x` est un idiome legitime : il tient une dependance sans changer la
    # valeur - une tranche bullet qui n'amortit pas, un breaker qui gele une
    # boucle. Il devient un defaut grave sur une ligne de CONTROLE : le
    # compteur de violations ne peut alors plus jamais se declencher, et il
    # rend vert sans avoir rien mesure.
    neutralise = re.compile(r"\*\s*0\s*(?:\)|$)|\*\s*\(\s*0\s*\)|(?<![0-9.A-Za-z_])0\s*\*")
    mots = MOTS_CONTROLE
    cables = []
    for k, f in C.formules.items():
        if not neutralise.search(f):
            continue
        etiquette = ""
        for col in (3, 2, 4):
            v = C.textes.get((k[0], k[1], col))
            if v and not str(v).startswith("="):
                etiquette = str(v)
                break
        if any(m in etiquette.lower() for m in mots):
            cables.append(f"{L(k)}  [{etiquette.strip()[:50]}]  {f[:80]}")
    R.poser("I17", "aucune ligne de controle neutralisee par une multiplication "
            "par zero", cables, "critique",
            "un compteur de violations multiplie par zero ne peut plus se "
            "declencher : il rend vert sans avoir rien mesure")

    # --- I19 une ligne de controle SAISIE au lieu d'etre calculee -------------
    # Le frere jumeau de I17. La ou I17 attrape un controle annule par une
    # multiplication, celui-ci attrape un controle simplement tape a la main.
    # Le cas typique est une seule colonne en dur au milieu d'une ligne de
    # formules : la periode ou le controle n'aurait pas ferme.
    saisies = []
    for k, v in sorted(C.durs.items()):
        if k[0] == feuille_inputs:
            continue
        etiquette = ""
        for col in (3, 2, 4):
            w = C.textes.get((k[0], k[1], col))
            if w and not str(w).startswith("="):
                etiquette = str(w)
                break
        if not any(m in etiquette.lower() for m in mots):
            continue
        # une ligne de controle entierement en dur est une ligne vide de sens ;
        # une seule colonne en dur au milieu de formules est un masquage.
        soeurs = sum(1 for kk in C.formules if kk[0] == k[0] and kk[1] == k[1])
        saisies.append(f"{L(k)} = {v!r}   [{etiquette.strip()[:44]}]"
                       f"   {soeurs} formule(s) sur la meme ligne")
    R.poser("I19", "aucune ligne de controle saisie au lieu d'etre calculee",
            saisies, "critique",
            "un controle tape a la main ne controle rien ; une seule colonne "
            "en dur au milieu d'une ligne de formules est un masquage")

    # --- I20 une ligne de controle dont la FORMULE est une constante ---------
    # Le troisieme membre de la famille, et le plus retors. I19 attrape une
    # cellule SAISIE, I17 une cellule annulee par une multiplication. Celle-ci
    # porte bien une formule - donc elle passe les deux - mais cette formule
    # est un litteral : `=0`. Le compteur de violations affiche zero parce
    # qu'on le lui a demande, pas parce qu'il a compte.
    litteral = re.compile(r"^=\s*-?[0-9]+(?:\.[0-9]+)?\s*$")
    constantes = []
    for k, f in C.formules.items():
        if not litteral.match(f.strip()):
            continue
        etiquette = ""
        for col in (3, 2, 4):
            w = C.textes.get((k[0], k[1], col))
            if w and not str(w).startswith("="):
                etiquette = str(w)
                break
        if not any(m in etiquette.lower() for m in mots):
            continue
        # Un `=0` sur les periodes ou un controle NON PERIODIQUE ne s'applique
        # pas est legitime - c'est meme la bonne facon d'eviter qu'il lise une
        # cellule vide. Le defaut n'existe que si la ligne ne calcule RIEN
        # nulle part : le controle n'est alors pas « inapplicable ici », il est
        # absent partout.
        soeurs = sum(1 for kk, ff in C.formules.items()
                     if kk[0] == k[0] and kk[1] == k[1] and not litteral.match(ff.strip()))
        if soeurs:
            continue
        constantes.append(f"{L(k)}  {f.strip()}   [{etiquette.strip()[:46]}]")
    R.poser("I20", "aucune ligne de controle entierement constante", constantes,
            "critique",
            "`=0` sur un compteur de violations passe I17 et I19 - c'est bien "
            "une formule - mais elle ne compte rien. Le defaut n'est retenu que "
            "si AUCUNE colonne de la ligne ne calcule quoi que ce soit")

    # --- I14 le classeur a-t-il seulement ete calcule par Excel ? ----------
    # Un generateur Python ecrit les formules ET un cache qu'il a calcule
    # lui-meme. Le fichier s'ouvre, s'affiche, et ses valeurs n'ont jamais
    # ete produites par Excel. Sur un classeur circulaire c'est fatal : le
    # point fixe d'Excel n'est pas celui de Python.
    faits = []
    try:
        import zipfile
        z = zipfile.ZipFile(chemin)
        noms = z.namelist()
        if "xl/calcChain.xml" not in noms:
            faits.append("xl/calcChain.xml absent : Excel n'a jamais construit "
                         "de chaine de calcul pour ce fichier")
        try:
            app = re.search(r"<Application>([^<]*)</Application>",
                            z.read("docProps/app.xml").decode("utf-8", "ignore"))
            if app and "openpyxl" in app.group(1).lower():
                faits.append(f"derniere application : {app.group(1)} - "
                             f"le cache vient du generateur, pas d'Excel")
        except KeyError:
            pass
        wbx = z.read("xl/workbook.xml").decode("utf-8", "ignore")
        m = re.search(r"<calcPr[^>]*>", wbx)
        if m and 'iterate="1"' not in m.group(0) and 'iterate="true"' not in m.group(0):
            faits.append(f"calcul iteratif non arme dans le fichier : {m.group(0)}")
        z.close()
    except Exception as e:
        faits.append(f"lecture du conteneur impossible : {e}")
    R.poser("I14", "le classeur a bien ete calcule par Excel", faits, "critique",
            "un cache ecrit par un generateur n'est pas un resultat de calcul")

    # --- I15 le cache est-il compatible avec les formules ? -----------------
    # Un ROUND a d decimales ne peut rendre qu'un multiple de 10^-d. Un cache
    # qui viole cette contrainte prouve, sans rien recalculer, qu'il n'a pas
    # ete produit par la formule qu'il accompagne.
    incoherents = []
    rond = re.compile(r"ROUND\s*\(.*,\s*(\d+)\s*\)\s*$", re.I | re.S)
    for k, f in C.formules.items():
        m = rond.search(f.strip())
        if not m:
            continue
        v = C.valeurs.get(k)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        pas = 10.0 ** (-int(m.group(1)))
        if v != 0 and abs(v) < pas * 0.499:
            incoherents.append(f"{L(k)} = {v!r} alors que la formule arrondit "
                               f"a {m.group(1)} decimales")
    R.poser("I15", "le cache est compatible avec les formules d'arrondi",
            incoherents, "critique",
            "un ROUND a d decimales ne peut rendre qu'un multiple de 10^-d")

    # --- I16 chaque formule porte-t-elle une valeur en cache ? ---------------
    muettes = [L(k) for k in C.formules if k not in C.valeurs]
    R.poser("I16", "chaque formule porte une valeur en cache", muettes,
            "significatif",
            "une valeur notee se lit dans le cache : une cellule muette n'est "
            "pas lisible sans recalculer, et recalculer un classeur circulaire "
            "sans iteration armee le corrompt")

    return C, R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("classeur")
    ap.add_argument("--inputs", default=None,
                    help="feuille d'hypotheses ; deduite si omise")
    ap.add_argument("--json")
    ap.add_argument("--detail", action="store_true")
    a = ap.parse_args()
    autotest()
    feuille = a.inputs or deduire_feuille_inputs(a.classeur)
    if not a.inputs:
        print(f"feuille d'hypotheses deduite : {feuille}")
    C, R = balayer(a.classeur, feuille)
    print(f"BALAYAGE D'INTEGRITE - {len(C.formules):,} formules, "
          f"{len(C.durs):,} valeurs en dur, {len(C.noms)} plages nommees\n")
    ko = R.afficher()
    if a.detail:
        R.detail()
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(R.controles, fh, ensure_ascii=False, indent=2)
        print(f"\necrit : {a.json}")
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(main())
