@echo off
chcp 65001
cd /d e:\OpenCVProjects\tansyqinyrproj
echo Starting push...
git config --local http.sslBackend schannel
git config --local http.sslVerify false
git config --local http.postBuffer 524288000
echo Configured git settings
git remote -v
echo Pushing to origin...
git push -f origin main
echo Push completed. Checking remote...
git ls-remote origin main
pause
