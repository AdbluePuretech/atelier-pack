<#
.SYNOPSIS
    Pose des valeurs dans un classeur par le VRAI Excel, sans le reecrire.

.DESCRIPTION
    Les controles dynamiques de l'audit posent des entrees avant de recalculer :
    flexer une hypothese, basculer un commutateur, corrompre une cellule.

    Ces ecritures passaient par un aller-retour openpyxl - `load_workbook` puis
    `save`. Sur un petit classeur c'est indolore ; sur un gros c'est destructeur.
    Mesure faite sur un classeur reel : 883 Ko tombes a 447 Ko, 17 366 formules
    partagees mises a plat, `sharedStrings`, `calcChain` et les metadonnees
    perdus. Le recalcul echouait ensuite, et l'outil imputait l'echec au
    classeur audite : `erreurs = -1`, qui n'est pas un compte d'erreurs mais la
    sentinelle d'un recalcul rate.

    Excel, lui, ouvre et enregistre son propre format sans rien perdre. Ce
    script fait donc l'ecriture, et rien d'autre : il ne recalcule pas et
    n'arme pas l'iteration - c'est le travail de `recalculer.ps1`, appele juste
    apres.

    Le classeur est modifie SUR PLACE. L'appelant travaille toujours sur une
    copie : le classeur audite est gele, et un audit qui modifie sa cible ne
    prouve rien.

.PARAMETER Chemin
    Le classeur a modifier, sur place.

.PARAMETER Entrees
    Les cellules a poser, separees par des points-virgules, chacune sous la
    forme `Feuille!Cellule=Valeur`. Un nom de feuille peut porter des espaces ;
    il n'a pas besoin de quotes. Une valeur qui se lit comme un nombre est
    posee en nombre, sinon en texte.

.PARAMETER Visible
    Affiche la fenetre Excel, utile pour comprendre un blocage.

.EXAMPLE
    powershell -File poser.ps1 -Chemin "copie.xlsx" -Entrees "Input_Sheet!D12=0.35;Input_Sheet!D13=1"

.OUTPUTS
    Une ligne par cellule posee, puis "poses : N / M". Code de sortie 0 si tout
    a ete pose, 3 si une adresse n'a pas pu etre resolue, 4 si Excel a leve.
    Un echec DOIT se voir dans le code : sans cela l'appelant croit avoir pose
    des entrees et mesure ensuite un classeur intact.
#>

param(
    [Parameter(Mandatory = $true)][string]$Chemin,
    [Parameter(Mandatory = $true)][string]$Entrees,
    [switch]$Visible
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Chemin)) {
    Write-Error "Fichier introuvable : $Chemin"
    exit 2
}
$Chemin = (Resolve-Path -LiteralPath $Chemin).Path

$paires = @()
foreach ($morceau in $Entrees.Split(';')) {
    if ([string]::IsNullOrWhiteSpace($morceau)) { continue }
    $i = $morceau.IndexOf('=')
    if ($i -lt 1) { Write-Error "Entree mal formee : $morceau"; exit 2 }
    $cible = $morceau.Substring(0, $i).Trim()
    $valeur = $morceau.Substring($i + 1)
    $j = $cible.LastIndexOf('!')
    if ($j -lt 1) { Write-Error "Adresse sans feuille : $cible"; exit 2 }
    $paires += [pscustomobject]@{
        Feuille = $cible.Substring(0, $j).Trim("'")
        Cellule = $cible.Substring($j + 1).Replace('$', '')
        Valeur  = $valeur
    }
}

$excel = $null
$wb = $null
$rates = 0
$echec = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = [bool]$Visible
    $excel.DisplayAlerts = $false

    $wb = $excel.Workbooks.Open($Chemin, 0, $false)

    # Ne pas recalculer pendant qu'on ecrit : chaque affectation declencherait
    # un calcul complet, et sur un classeur circulaire un calcul lance sans
    # iteration armee met les cellules auto-referentes a zero.
    # Cette propriete n'existe QU'UNE FOIS un classeur ouvert : la poser avant
    # leve 0x800A03EC, et l'erreur ne dit pas pourquoi.
    $excel.Calculation = -4135          # xlCalculationManual

    foreach ($p in $paires) {
        $ws = $null
        foreach ($feuille in $wb.Worksheets) {
            if ($feuille.Name -eq $p.Feuille) { $ws = $feuille; break }
        }
        if ($null -eq $ws) {
            Write-Output "NON RESOLU  $($p.Feuille)!$($p.Cellule) - feuille absente"
            $rates++
            continue
        }
        $nombre = 0.0
        if ([double]::TryParse($p.Valeur,
                [Globalization.NumberStyles]::Float,
                [Globalization.CultureInfo]::InvariantCulture,
                [ref]$nombre)) {
            $ws.Range($p.Cellule).Value2 = $nombre
        } else {
            $ws.Range($p.Cellule).Value2 = $p.Valeur
        }
        Write-Output "pose  $($p.Feuille)!$($p.Cellule) = $($p.Valeur)"
    }

    $wb.Save()
    Write-Output "poses : $($paires.Count - $rates) / $($paires.Count)"
}
catch {
    # Sans ce catch, une exception COM laissait le script sortir en 0 : l'appelant
    # croyait avoir pose des entrees, et mesurait ensuite un classeur intact.
    $echec = $_
    Write-Output "ECHEC  $($_.Exception.Message)"
}
finally {
    if ($wb) { $wb.Close($false) | Out-Null }
    if ($excel) {
        $excel.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}

if ($echec) { exit 4 }
if ($rates -gt 0) { exit 3 }
exit 0
