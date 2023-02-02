@echo off
set password=%1
set cert_path=C:\Users\Administrator\Desktop\certificat\coopengo-software-cert.pfx
set current_directory=%cd%
set folder=C:\msys32\home\Administrator\tryton\dist

if exist %folder% (
  echo Signing coog.exe ...
  "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x86\signtool.exe" sign /f %cert_path% /p %password% /tr http://timestamp.digicert.com /td SHA256 /fd SHA256 %folder%\coog.exe"
) else (
  FOR /F "tokens=*" %%f in ('dir /b /a-d coog-*.exe') do (
    echo Signing %%f ...
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x86\signtool.exe" sign /f %cert_path% /p %password% /tr http://timestamp.digicert.com /td SHA256 /fd SHA256 %%f
  )
)

exit
