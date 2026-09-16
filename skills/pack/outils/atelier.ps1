<#
.SYNOPSIS
    Ouvre un classeur dans une NOUVELLE instance d'Excel, sur une cellule, et la laisse a l'utilisateur.

.DESCRIPTION
    Sert aux ateliers avec l'auteur (references/ateliers.md). L'instance est creee par COM et rendue visible ; les
    references COM sont liberees sans quitter Excel, et UserControl passe a vrai : la fenetre appartient desormais a
    l'utilisateur, qui la ferme quand il a fini.

    Aucune autre instance d'Excel n'est reprise, activee ni fermee.

.PARAMETER Chemin
    Le classeur a ouvrir (une copie d'atelier, jamais le fichier que le generateur ecrit).

.PARAMETER Cellule
    Facultatif. La cellule a selectionner, sous la forme Feuille!A1 ; le nom de feuille peut porter des espaces, avec
    ou sans quotes.

.EXAMPLE
    powershell -File atelier.ps1 -Chemin "GS atelier 03 - Cobalt.xlsx" -Cellule "Input_Sheet!E812"
#>
param(
    [Parameter(Mandatory = $true)][string]$Chemin,
    [string]$Cellule = ""
)
$ErrorActionPreference = 'Stop'
$Chemin = (Resolve-Path -LiteralPath $Chemin).Path

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $true
$wb = $xl.Workbooks.Open($Chemin)

if ($Cellule) {
    $i = $Cellule.LastIndexOf('!')
    if ($i -lt 1) { throw "Cellule attendue sous la forme Feuille!A1 : $Cellule" }
    $feuille = $Cellule.Substring(0, $i).Trim("'")
    $adresse = $Cellule.Substring($i + 1)
    $ws = $wb.Worksheets.Item($feuille)
    $ws.Activate()
    $xl.Goto($ws.Range($adresse), $true)
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ws) | Out-Null
}

$xl.UserControl = $true
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($xl) | Out-Null
Write-Output "ouvert : $Chemin $Cellule"
