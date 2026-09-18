!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "WinMessages.nsh"

; ============================================================
; Duster Installer
; ============================================================

Name "Duster"
OutFile "duster-installer.exe"

InstallDir "$LOCALAPPDATA\Duster"

RequestExecutionLevel user

!define MUI_ABORTWARNING

; ============================================================
; Modern UI
; ============================================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"


; ============================================================
; INSTALLER
; ============================================================

Section "Duster" SecDuster

    SectionIn RO

    ; Create installation directory
    SetOutPath "$INSTDIR"

    ; Install executable
    File "duster.exe"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; --------------------------------------------------------
    ; Add Duster to the user's PATH
    ; --------------------------------------------------------

    ReadRegStr $0 HKCU "Environment" "Path"

    ${If} $0 == ""

        ; PATH doesn't exist yet
        WriteRegExpandStr HKCU "Environment" "Path" "$INSTDIR"

    ${Else}

        ; Don't add Duster again if the exact path is already there
        StrCmp $0 "$INSTDIR" path_done

        ; Check whether it already exists at the beginning
        StrCpy $1 "$INSTDIR;"
        StrLen $2 "$1"
        StrCpy $3 $0 $2

        StrCmp $3 $1 path_done

        ; Check whether it already exists at the end
        StrCpy $1 ";$INSTDIR"
        StrLen $2 "$1"
        StrLen $3 $0
        IntOp $3 $3 - $2
        StrCpy $4 $0 $2 $3

        StrCmp $4 $1 path_done

        ; Otherwise append it
        WriteRegExpandStr HKCU "Environment" "Path" "$0;$INSTDIR"

    ${EndIf}

path_done:

    ; Tell Windows that the environment changed
    System::Call 'Kernel32::SendMessageTimeout(i 0xffff, i ${WM_SETTINGCHANGE}, i 0, t "Environment", i 0x0002, i 5000, *i .r1)'

SectionEnd


; ============================================================
; UNINSTALLER PATH HELPER
; ============================================================

Function un.RemoveDusterFromPath

    ReadRegStr $0 HKCU "Environment" "Path"

    ${If} $0 == ""
        Return
    ${EndIf}

    ; --------------------------------------------------------
    ; PATH is exactly Duster
    ; --------------------------------------------------------

    StrCmp $0 "$INSTDIR" 0 +3
        DeleteRegValue HKCU "Environment" "Path"
        Return


    ; --------------------------------------------------------
    ; Duster is at the beginning:
    ;
    ; C:\Duster;C:\Something
    ; --------------------------------------------------------

    StrCpy $1 "$INSTDIR;"
    StrLen $2 $1
    StrCpy $3 $0 $2

    StrCmp $3 $1 0 check_end

        StrCpy $0 $0 "" $2
        WriteRegExpandStr HKCU "Environment" "Path" "$0"
        Return


check_end:

    ; --------------------------------------------------------
    ; Duster is at the end:
    ;
    ; C:\Something;C:\Duster
    ; --------------------------------------------------------

    StrCpy $1 ";$INSTDIR"
    StrLen $2 $1

    StrLen $3 $0
    IntOp $3 $3 - $2

    StrCpy $4 $0 $2 $3

    StrCmp $4 $1 0 check_middle

        StrCpy $0 $0 $3
        WriteRegExpandStr HKCU "Environment" "Path" "$0"
        Return


check_middle:

    ; --------------------------------------------------------
    ; Duster is somewhere in the middle:
    ;
    ; C:\A;C:\Duster;C:\B
    ;
    ; Search for:
    ;
    ; ;C:\Duster;
    ; --------------------------------------------------------

    StrCpy $1 ";$INSTDIR;"
    StrLen $2 $1

    ; Start searching at position 0
    StrCpy $R0 0

find_middle:

    StrLen $3 $0

    ; Stop when we've reached the end
    ${If} $R0 >= $3
        Return
    ${EndIf}

    ; Compare substring at current position
    StrCpy $4 $0 $2 $R0

    StrCmp $4 $1 found_middle

    ; Move forward one character
    IntOp $R0 $R0 + 1
    Goto find_middle


found_middle:

    ; Prefix = everything before ;Duster;
    StrCpy $5 $0 $R0

    ; Skip over ;Duster;
    IntOp $6 $R0 + $2

    ; Suffix = everything after ;Duster;
    StrCpy $7 $0 "" $6

    ; Rebuild PATH
    StrCmp $5 "" 0 have_prefix

        ; No prefix
        StrCpy $0 $7
        Goto write_middle

have_prefix:

    StrCmp $7 "" 0 prefix_and_suffix

        ; No suffix
        StrCpy $0 $5
        Goto write_middle

prefix_and_suffix:

    StrCpy $0 "$5;$7"

write_middle:

    WriteRegExpandStr HKCU "Environment" "Path" "$0"

FunctionEnd


; ============================================================
; UNINSTALLER
; ============================================================

Section "Uninstall"

    ; Remove Duster from user's PATH
    Call un.RemoveDusterFromPath

    ; Remove files
    Delete "$INSTDIR\duster.exe"
    Delete "$INSTDIR\uninstall.exe"

    ; Remove installation directory
    RMDir "$INSTDIR"

    ; Tell Windows that the environment changed
    System::Call 'Kernel32::SendMessageTimeout(i 0xffff, i ${WM_SETTINGCHANGE}, i 0, t "Environment", i 0x0002, i 5000, *i .r1)'

SectionEnd