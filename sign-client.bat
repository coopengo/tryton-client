@echo off
set password="%1"
set cert_path="C:\Users\Administrator\Desktop\certificat\coopengo-software-cert.pfx"
set current_directory="%cd%"

dir %current_directory%

FOR /F "tokens=*" %%f in ('dir /b /a-d coog-*') do (
  echo %%f
  start signtool sign /f "%cert_path%" /p "%password%" /tr http://timestamp.digicert.com /td SHA256 /fd SHA256 "%%f"
)
