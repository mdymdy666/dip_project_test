# PowerShell script to push to GitHub
$ErrorActionPreference = "Continue"
$projectDir = "e:\OpenCVProjects\tansyqinyrproj"

Set-Location $projectDir

Write-Host "Current directory: $(Get-Location)"
Write-Host "Git status:"
git status

Write-Host "`nConfiguring Git SSL settings..."
git config --local http.sslBackend schannel
git config --local http.sslVerify false
git config --local http.postBuffer 524288000

Write-Host "`nGit config:"
git config --local --list

Write-Host "`nPushing to origin main..."
$result = git push -f origin main 2>&1
Write-Host $result

Write-Host "`nChecking remote status..."
git ls-remote origin main

Write-Host "`nDone."
