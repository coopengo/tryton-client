@echo off
set password=%1
set cert_path=C:\Users\Administrator\Desktop\certificat\coopengo-software-cert.pfx
set current_directory=%cd%
set folder=C:\msys32\home\Administrator\tryton\dist

cd "C:\msys32\home\Administrator\tryton"

if exist %folder% (
  echo Signing coog.exe ...
  "%ProgramFiles(x86)%\Windows Kits\10\bin\10.0.22621.0\x86\signtool.exe" sign /td SHA256 /fdws /f %cert_path% /p %password% /tr http://timestamp.digicert.com "%folder%\coog.exe"
) else (
  FOR /F "tokens=*" %%f in ('dir /b /a-d coog-*.exe') do (
    echo Signing %%f ...
    "%ProgramFiles(x86)%\Windows Kits\10\bin\10.0.22621.0\x86\signtool.exe" sign /td SHA256 /fdws /f %cert_path% /p %password% /tr http://timestamp.digicert.com "%%f"
  )
)

exit
