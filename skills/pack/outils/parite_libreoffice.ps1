<#
.SYNOPSIS
    Recalcule un classeur sous LibreOffice et le compare au cache Excel.

.DESCRIPTION
    Le service QA note en recalculant sous LibreOffice. Un classeur peut donc
    s'ouvrir juste dans Excel, re-noter 100 % sur sa rubric, et se faire noter
    faux par le service. Ce script ferme cet angle mort.

    Il leve un LibreOffice sans interface qui ecoute sur un socket UNO, lui fait
    ouvrir le classeur, releve le reglage d'iteration TEL QUE LE FICHIER LE
    PORTE — c'est ce que verra le correcteur, et un modele circulaire dont le
    fichier ne porte pas l'iteration rend `Err:522` partout — puis force un
    recalcul complet et exporte chaque cellule pour comparaison.

.PARAMETER Chemin
    Le classeur a controler. Il n'est jamais modifie.
#>
param(
    [Parameter(Mandatory = $true)][string]$Chemin,
    [string]$Sortie = "lo-valeurs.json",
    [int]$Port = 2002
)
$ErrorActionPreference = 'Stop'
$LO = "C:\Program Files\LibreOffice\program"
if (-not (Test-Path $LO)) { Write-Error "LibreOffice introuvable : $LO"; exit 2 }
$Chemin = (Resolve-Path -LiteralPath $Chemin).Path

$deja = Get-Process soffice -ErrorAction SilentlyContinue
if (-not $deja) {
    Start-Process "$LO\soffice.exe" -ArgumentList `
        '--headless', '--norestore', '--invisible', '--nologo', '--nolockcheck', `
        "--accept=socket,host=localhost,port=$Port;urp;"
    Start-Sleep -Seconds 12
}
& "$LO\python.exe" (Join-Path $PSScriptRoot 'lo_dump.py') $Chemin $Sortie
& python (Join-Path $PSScriptRoot 'lo_parite.py') $Chemin $Sortie
