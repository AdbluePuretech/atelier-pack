<#
.SYNOPSIS
    Arme le calcul iteratif, recalcule un classeur dans le vrai Excel, et l'ENREGISTRE.

.DESCRIPTION
    `qa-formules.ps1` ouvre en lecture seule et ne sauvegarde jamais : il controle,
    il ne produit rien. Ce script-ci fait l'autre moitie du travail, et c'est celle
    dont un classeur circulaire a besoin.

    openpyxl n'ecrit aucune valeur en cache : un classeur qu'il vient de generer ne
    porte que des formules. Tant qu'Excel ne l'a pas ouvert, recalcule et
    reenregistre, `data_only=True` ne rend que des `None`, et le classeur n'est donc
    pas gradable.

    Le calcul iteratif est arme AVANT l'ouverture. Sans cela Excel signale les
    references circulaires et met les cellules auto-referentes a zero : le modele
    s'ouvre faux, en silence.

    Le reglage d'iteration d'Excel est une preference d'APPLICATION, pas de fichier.
    Le script releve l'etat qu'il a trouve et le remet en partant, pour ne pas
    laisser la machine dans un etat qu'elle n'avait pas.

.PARAMETER Chemin
    Le classeur a recalculer. Il est modifie sur place.

.PARAMETER Iterations
    Nombre maximal d'iterations. Defaut 500, la valeur du corpus.

.PARAMETER Ecart
    Ecart maximal entre deux iterations. Defaut 1e-06, la valeur du corpus.

.PARAMETER Passes
    Nombre de recalculs complets enchaines. Defaut 3 : une boucle profonde ne
    converge pas toujours en une passe, et un second calcul coute peu.

.PARAMETER Visible
    Affiche la fenetre Excel, utile pour comprendre un blocage.

.EXAMPLE
    powershell -File systeme/scripts/excel/recalculer.ps1 -Chemin "GoldenSolution - Denali.xlsx"
#>

param(
    [Parameter(Mandatory = $true)][string]$Chemin,
    [int]$Iterations = 500,
    [double]$Ecart = 0.000001,
    [int]$Passes = 3,
    [switch]$Visible
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Chemin)) {
    Write-Error "Fichier introuvable : $Chemin"
    exit 2
}
$Chemin = (Resolve-Path -LiteralPath $Chemin).Path

$xlCellTypeFormulas = -4123
$xlErrors           = 16
$xlCalculationManual = -4135

$excel = $null
$classeur = $null
$amorce = $null
$avant = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = [bool]$Visible
    $excel.DisplayAlerts = $false
    $excel.ScreenUpdating = $false
    $excel.AskToUpdateLinks = $false

    # Excel refuse de poser Iteration tant qu'aucun classeur n'existe : la
    # propriete leve 0x800A03EC sur une application vide. On ouvre donc un
    # classeur d'amorce, jete des que le reglage est pris.
    $amorce = $excel.Workbooks.Add()

    # L'etat qu'on a trouve, pour le rendre tel quel.
    $avant = [pscustomobject]@{
        Iteration     = $excel.Iteration
        MaxIterations = $excel.MaxIterations
        MaxChange     = $excel.MaxChange
    }

    # Arme AVANT l'ouverture : c'est tout l'interet du script.
    $excel.Iteration     = $true
    $excel.MaxIterations = $Iterations
    $excel.MaxChange     = $Ecart

    Write-Output "=== Recalcul ==="
    Write-Output "classeur   : $(Split-Path -Leaf $Chemin)"
    Write-Output "iteration  : armee a $Iterations passages, ecart $Ecart"

    $amorce.Close($false)
    $amorce = $null

    $classeur = $excel.Workbooks.Open($Chemin, 0, $false)

    for ($p = 1; $p -le $Passes; $p++) {
        $excel.CalculateFullRebuild()
        Write-Output "passe $p    : recalcul complet effectue"
    }

    # Les erreurs qui subsistent apres convergence.
    $total = 0
    foreach ($feuille in $classeur.Worksheets) {
        $formules = $null
        try { $formules = $feuille.UsedRange.SpecialCells($xlCellTypeFormulas, $xlErrors) } catch { }
        if ($formules -and $formules.Count -gt 0) {
            Write-Output "  $($feuille.Name) : $($formules.Count) cellule(s) en erreur"
            $montrees = 0
            foreach ($cellule in $formules) {
                if ($montrees -ge 5) { break }
                Write-Output "      $($cellule.Address($false, $false))  $($cellule.Text)  <- $($cellule.Formula)"
                $montrees++
            }
            $total += $formules.Count
        }
    }

    $classeur.Save()
    Write-Output "enregistre : valeurs en cache ecrites"
    Write-Output "erreurs    : $total"

    $classeur.Close($false)
    $classeur = $null
    exit ($(if ($total -gt 0) { 1 } else { 0 }))
}
finally {
    if ($amorce) { try { $amorce.Close($false) } catch { } }
    if ($classeur) { try { $classeur.Close($false) } catch { } }
    if ($excel) {
        if ($avant) {
            try {
                $excel.Iteration     = $avant.Iteration
                $excel.MaxIterations = $avant.MaxIterations
                $excel.MaxChange     = $avant.MaxChange
            } catch { }
        }
        try { $excel.Quit() } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch { }
    }
}
