;This file is part of Tryton.  The COPYRIGHT file at the top level of
;this repository contains the full copyright notices and license terms.

;Check version
!ifndef VERSION
    !error "Missing VERSION! Specify it with '/DVERSION=<VERSION>'"
!endif

;Include Modern UI
!include "MUI.nsh"

;General
Name "Coog ${VERSION}"
OutFile "coog-setup-${VERSION}.exe"
SetCompressor lzma
SetCompress auto

;Default installation folder
InstallDir "$PROGRAMFILES\coog-${VERSION}"

;Get installation folder from registry if available
InstallDirRegKey HKCU "Software\coog-${VERSION}" ""

BrandingText "Coog ${VERSION}"

;Vista redirects $SMPROGRAMS to all users without this
RequestExecutionLevel admin

;Variables
Var MUI_TEMP
Var STARTMENU_FOLDER

;Interface Settings
!define MUI_ABORTWARNING

;Language Selection Dialog Settings
;Remember the installer language
!define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
!define MUI_LANGDLL_REGISTRY_KEY "Software\Modern UI Test"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

;Pages

!define MUI_ICON "tryton\data\pixmaps\tryton\tryton.ico"
!define MUI_LICENSEPAGE_TEXT_BOTTOM "$(LicenseText)"
!define MUI_LICENSEPAGE_BUTTON "$(LicenseNext)"

!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $STARTMENU_FOLDER
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;Languages

!insertmacro MUI_LANGUAGE "English" ; First is the default
!include "english.nsh"
!insertmacro MUI_LANGUAGE "French"
!include "french.nsh"
!insertmacro MUI_LANGUAGE "German"
!include "german.nsh"
!insertmacro MUI_LANGUAGE "Farsi"
!include "farsi.nsh"
!insertmacro MUI_LANGUAGE "Slovenian"
!include "slovenian.nsh"
!insertmacro MUI_LANGUAGE "Spanish"
!include "spanish.nsh"
!insertmacro MUI_LANGUAGE "Russian"
!include "russian.nsh"

;Reserve Files

;If you are using solid compression, files that are required before
;the actual installation should be stored first in the data block,
;because this will make your installer start faster.
!insertmacro MUI_RESERVEFILE_LANGDLL

;Installer Sections
Function .onInit
    ClearErrors
    ReadRegStr $0 HKCU "Software\coog-${VERSION}" ""
    IfErrors DoInstall 0
        MessageBox MB_OK "$(PreviousInstall)"
        Quit
    DoInstall:
FunctionEnd

Section $(SecCoogName) SecCoog
SectionIn 1 2 RO
    ;Set output path to the installation directory
    SetOutPath "$INSTDIR"

    ;Put file
    File /r "dist\*"
    File "COPYRIGHT"
    File "INSTALL"
    File "LICENSE"
    File "README"
    File "CHANGELOG"

    SetOutPath "$INSTDIR\doc"
    File /r "doc\*"

    ;Register URL protocol
    WriteRegStr HKCR "coog" "" "URL:Coog Protocol"
    WriteRegStr HKCR "coog" "URL Protocol" ""
    WriteRegStr HKCR "coog\DefaultIcon" "" "$INSTDIR\coog.exe,1"
    WriteRegStr HKCR "coog\shell\open\command" "" '$INSTDIR\coog.exe "%1"'

    ;Write the installation path into the registry
    WriteRegStr HKCU "Software\coog-${VERSION}" "" $INSTDIR
    WriteRegStr HKLM "Software\coog-${VERSION}" "" $INSTDIR

    ;Write the uninstall keys for Windows
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\coog-${VERSION}" "DisplayName" "Coog ${VERSION} (remove only)"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\coog-${VERSION}" "UninstallString" "$INSTDIR\uninstall.exe"

    ;Create the uninstaller
    WriteUninstaller uninstall.exe
SectionEnd

Section $(SecStartMenuName) SecStartMenu
SectionIn 1 2

    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
        SetShellVarContext all

        CreateDirectory "$SMPROGRAMS\$STARTMENU_FOLDER"
        CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
        CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Coog-${VERSION}.lnk" "$INSTDIR\coog.exe" "" "$INSTDIR\coog.exe" 0
        CreateShortCut "$DESKTOP\Coog-${VERSION}.lnk" "$INSTDIR\coog.exe" "" "$INSTDIR\coog.exe" 0

    !insertmacro MUI_STARTMENU_WRITE_END

SectionEnd

;Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCoog} $(SecCoogDesc)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(SecStartMenuDesc)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
    ;Add your stuff here
    RMDIR /r "$INSTDIR"

    ;remove registry keys
    DeleteRegKey HKCU "Software\coog-${VERSION}"
    DeleteRegKey HKLM "Software\coog-${VERSION}"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\coog-${VERSION}"

    SetShellVarContext all
    Delete "$DESKTOP\Coog-${VERSION}.lnk"

    !insertmacro MUI_STARTMENU_GETFOLDER Application $MUI_TEMP

    StrCmp $MUI_TEMP "" noshortcuts
        Delete "$SMPROGRAMS\$MUI_TEMP\Uninstall.lnk"
        Delete "$SMPROGRAMS\$MUI_TEMP\Coog-${VERSION}.lnk"
        RMDir "$SMPROGRAMS\$MUI_TEMP"
    noshortcuts:


SectionEnd
