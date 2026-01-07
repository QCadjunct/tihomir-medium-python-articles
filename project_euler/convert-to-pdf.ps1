# convert-to-pdf.ps1 - Professional Markdown to PDF with Mermaid Support
param(
    [Parameter(Mandatory=$false)]
    [string]$InputFile = "Python_Class-Based_Decorators_-_When_Functions_Are_Not_Enough.md",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputFile = $null
)

# Auto-generate output filename if not specified
if (!$OutputFile) {
    $OutputFile = [System.IO.Path]::ChangeExtension($InputFile, ".pdf")
}

# Setup paths
$filterPath = "C:\Users\pheller\AppData\Roaming\npm\mermaid-filter.cmd"
$npmBin = npm config get prefix
$env:Path += ";$npmBin"

# Verify input exists
if (!(Test-Path $InputFile)) {
    Write-Host " File not found: $InputFile" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Markdown  PDF Converter" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "Input:  $InputFile" -ForegroundColor White
Write-Host "Output: $OutputFile`n" -ForegroundColor White
Write-Host "Converting... (may take 30-60 seconds)" -ForegroundColor Yellow

# Convert
$startTime = Get-Date

pandoc $InputFile `
    -o $OutputFile `
    --filter $filterPath `
    --pdf-engine=xelatex `
    -V geometry:margin=1in `
    -V linkcolor:blue `
    -V fontsize:11pt `
    --toc `
    --toc-depth:3 `
    --number-sections `
    2>&1 | Out-Null

$elapsed = ((Get-Date) - $startTime).TotalSeconds

# Result
if (Test-Path $OutputFile) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "   SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Created: $OutputFile" -ForegroundColor White
    Write-Host "Time: $([math]::Round($elapsed, 1)) seconds`n" -ForegroundColor White
    Invoke-Item $OutputFile
} else {
    Write-Host "`n Conversion failed" -ForegroundColor Red
    exit 1
}
