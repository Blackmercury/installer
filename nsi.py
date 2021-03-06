def generate(dvd, version, human_version, sections, architecture):
    arch_suffix = '-x64' if architecture == '64' else ''

    contents = [
r'''; Copyright 2006 Daniel Wallin
; Copyright 2006 Eric Niebler
; Copyright 2010 Dave Abrahams
; Distributed under the Boost Software License, Version 1.0. (See
; accompanying file LICENSE_1_0.txt or copy at
; http://www.boost.org/LICENSE_1_0.txt)

!define SKIP_FILES

!define MUI_COMPONENTSPAGE_NODESC 
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "boost.bmp"

!include "StrFunc.nsh"
!include "MUI.nsh"
!include "Sections.nsh"
!include "LogicLib.nsh"
!include "path.nsh"

!define VERSION %(human_version)s
!define NORMALIZED_VERSION %(version)s
!define PUBLISHER boostpro.com
!define NAME "Boost C++ Libraries ${VERSION}"

;--------------------------------

Name "${NAME}"

; The file to write
OutFile "boost_${NORMALIZED_VERSION}_setup.exe"

; The default installation directory
InstallDir $PROGRAMFILES%(architecture)s\boost\boost_${NORMALIZED_VERSION}

; Registry key to check for directory (so if you install again, it will
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\${PUBLISHER}\${VERSION}" "InstallRoot"

!define MUI_COMPONENTSPAGE_TEXT_COMPLIST "Select components to install: $\n$\nNote that the libraries available for selection here are built binaries. All header only libraries are always installed."

BrandingText "${PUBLISHER} - Installer created with NSIS (Nullsoft Scriptable Install System)"

!addplugindir plugins

;--------------------------------

; Pages

!define MUI_PAGE_HEADER_TEXT  "Installer License Agreement"
!insertmacro MUI_PAGE_LICENSE "license.txt"
!define MUI_PAGE_HEADER_TEXT  "Boost Libraries License Agreement"
!insertmacro MUI_PAGE_LICENSE "guidelines.rtf"
''' % locals(),
    dvd and ';' or '', 'Page custom selectMirrorPage leaveSelectMirror',
    r'''
Page custom defaultVariantsPage leaveDefaultVariants
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

;--------------------------------

${StrTrimNewLines}
${StrTok}

Var mirror_count
Var mirror_urls
Var mirror_names
Var mirror_selected
Var use_boost_consulting
Var installed_tools

; This is set to true when a mirror fails.
Var select_new_mirror 

Function RandomNumber
    Exch $R0

    IntOp $R0 $R0 * "13"
    IntOp $R0 $R0 + "3"
    IntOp $R0 $R0 % "1048576" # Values goes from 0 to 1048576 (2^20)
 
    Exch $R0
FunctionEnd

Function LimitedRandomNumber
    Exch $R0
    Exch
    Exch $R1
    Push $R2
    Push $R3
 
    StrLen $R2 $R0
    Push $R1
RandLoop:
    Call RandomNumber
    Pop $R1 #Random Number
    IntCmp $R1 $R0 0 NewRnd
    StrLen $R3 $R1
    IntOp $R3 $R3 - $R2
    IntOp $R3 $R3 / "2"
    StrCpy $R3 $R1 $R2 $R3
    IntCmp $R3 $R0 0 RndEnd
NewRnd:
    Push $R1
    Goto RandLoop
RndEnd:
    StrCpy $R0 $R3
    IntOp $R0 $R0 + "0" #removes initial 0's
    Pop $R3
    Pop $R2
    Exch $R1
    Exch
    Exch $R0
FunctionEnd

Function selectMirrorPage
    !insertmacro MUI_HEADER_TEXT "Select Mirror" "Choose which mirror you want to use to download ${NAME}."

    StrCmp $mirror_names "" 0 skip_mirror_download
    inetc::get /NOCANCEL "http://www.boostpro.com/boost-binaries/${NORMALIZED_VERSION}%(arch_suffix)s/mirrors.txt" "$TEMP\mirrors.txt" /END
    Pop $0
    StrCmp $0 "OK" download_ok
    BringToFront
    MessageBox MB_OK "Failed to download mirror list, all downloadable content has been disabled."
    Abort
  download_ok:
    nxs::Destroy
    ; This is a terrible ugly hack to make sure the window is properly
    ; selected after destroying the dialog.    
    BringToFront
    ShowWindow $HWNDPARENT 2
    ShowWindow $HWNDPARENT 1
    StrCpy $mirror_count 0
    FileOpen $0 $TEMP\mirrors.txt r
  read_line:
    FileRead $0 $1
    IfErrors no_more_mirrors
    ${StrTrimNewLines} $1 $1
    StrCpy $mirror_names "$mirror_names|$1"

    FileRead $0 $1
    ${StrTrimNewLines} $1 $1
    StrCpy $mirror_urls "$mirror_urls|$1"

    IntOp $mirror_count $mirror_count + 1
    goto read_line
  no_more_mirrors:
    FileClose $0
    Delete $TEMP\mirrors.txt

  skip_mirror_download:
    StrCpy $0 0
  set_label:
    IntCmp $0 $mirror_count no_more_labels
    ${StrTok} $1 $mirror_names "|" "$0" "1"
    IntOp $2 $0 + 3
    !insertmacro MUI_INSTALLOPTIONS_WRITE "select_mirror.ini" "Field $2" "Text" "$1"
    IntOp $0 $0 + 1
    goto set_label
  no_more_labels:
    !insertmacro MUI_INSTALLOPTIONS_INITDIALOG "select_mirror.ini"
    Pop $0

; Hide unused radio buttons
    StrCpy $0 9
  disable_another:
    IntCmp $0 $mirror_count no_more_disable
    IntOp $1 $0 + 2
    !insertmacro MUI_INSTALLOPTIONS_READ $2 "select_mirror.ini" "Field $1" "HWND"
    ShowWindow $2 ${SW_HIDE}
    IntOp $0 $0 - 1
    goto disable_another
  no_more_disable:

    !insertmacro MUI_INSTALLOPTIONS_SHOW
    Pop $0

    ClearErrors
FunctionEnd

Function leaveSelectMirror
    StrCpy $0 2
  test_another:
    !insertmacro MUI_INSTALLOPTIONS_READ $1 "select_mirror.ini" "Field $0" "State"
    IntCmp $1 1 0 +4
        StrCpy $2 $0
        IntOp $2 $2 - 2
        goto found
    IntOp $0 $0 + 1
    IntCmp $0 9 0 test_another
  found:
    IntCmp $2 0 0 0 not_random
    Push $HWNDPARENT
    Push $mirror_count
    Call LimitedRandomNumber
    Pop $0
    Pop $1
    StrCpy $mirror_selected $0
    goto maybe_skip_to_install
  not_random:
    IntOp $2 $2 - 1
    StrCpy $mirror_selected $2

  maybe_skip_to_install:
    StrCmp $select_new_mirror 1 0 dont_jump
    StrCpy $R9 4
    call RelGotoPage
  dont_jump:
FunctionEnd

Function DisableDownloadSections
    ClearErrors
    StrCpy $0 2 ; Don't disable the first 2 sections
  another_section:
    SectionGetFlags $0 $1
    IfErrors +6
    IntOp $1 $1 & 0xFFFFFFFE
    IntOp $1 $1 | 16
    SectionSetFlags $0 $1
    IntOp $0 $0 + 1
    goto another_section
FunctionEnd

Var no_default_compilers
Var no_default_variants

Function defaultVariantsPage
    !insertmacro MUI_HEADER_TEXT "Select Default Variants" "Each Boost library binary is pre-built in several variants.  Choose the build variants to install by default."

    !insertmacro MUI_INSTALLOPTIONS_INITDIALOG "default_variants.ini"
    Pop $0
    !insertmacro MUI_INSTALLOPTIONS_SHOW
    Pop $0

    !insertmacro MUI_INSTALLOPTIONS_READ $0 "default_variants.ini" "Field 4" "State"
    ${If} $0 == 0
        !insertmacro MUI_INSTALLOPTIONS_READ $0 "default_variants.ini" "Field 5" "State"
    ${EndIf}

    IntOp $0 $0 !
    StrCpy $no_default_compilers $0
    StrCpy $0 6
    StrCpy $1 0
    ClearErrors
  next:
    !insertmacro MUI_INSTALLOPTIONS_READ $2 "default_variants.ini" "Field $0" "State"
    IfErrors bail
    IntOp $1 $1 || $2
    IntOp $0 $0 + 1
    goto next
  bail:
    IntOp $1 $1 !
    StrCpy $no_default_variants $1

    call initSelectionFlags
FunctionEnd

Function leaveDefaultVariants
FunctionEnd

Var selected_libs

Function initSelectionFlags
    StrCpy $selected_libs ""
    ClearErrors
    StrCpy $0 5
  next:
    SectionGetText $0 $1
    IfErrors bail
    StrCpy $2 $1 5
    StrCmp $2 "Boost" 0 not_lib
    Push $0
    call SelectDefaultVariants
    StrCpy $selected_libs "$selected_libs1"
  not_lib:
    IntOp $0 $0 + 1
    goto next
  bail:
FunctionEnd

; Stack 0: compiler name
; Stack 1: variant name
; Stack 2: section

Function MaybeSelectVariant
    Exch $2
    ; c, v, r2
    Exch
    ; c, r2, v
    Exch $1
    ; c, r2, r1
    Exch
    ; c, r1, r2
    Exch 2
    ; r2, r1, c
    Exch $0
    ; r2, r1, r0
    Exch 2
    ; r0, r1, r2

    Push $3
    Push $4

        ${If} $0 == "VC7.1"
            !insertmacro MUI_INSTALLOPTIONS_READ $3 "default_variants.ini" "Field 4" "State"
        ${ElseIf} $0 == "VC8.0"
            !insertmacro MUI_INSTALLOPTIONS_READ $3 "default_variants.ini" "Field 5" "State"
        ${ElseIf} $0 == "VC9.0"
            !insertmacro MUI_INSTALLOPTIONS_READ $3 "default_variants.ini" "Field 6" "State"
        ${Else}
            !insertmacro MUI_INSTALLOPTIONS_READ $3 "default_variants.ini" "Field 7" "State"
        ${EndIf}

    StrCpy $5 0

    ${If} $3 != 0

        StrCpy $3 8
      next:
        !insertmacro MUI_INSTALLOPTIONS_READ $4 "default_variants.ini" "Field $3" "Text"
        IfErrors bail
        ${If} $4 == $1
            !insertmacro MUI_INSTALLOPTIONS_READ $5 "default_variants.ini" "Field $3" "State"
            goto bail
        ${EndIf}
        IntOp $3 $3 + 1
        goto next
      bail:
    ${EndIf}

    ${If} $5 == 0
        !insertmacro UnselectSection $2
    ${Else}
        !insertmacro SelectSection $2
    ${EndIf}

    Pop $4
    Pop $3
    Pop $2
    Pop $1
    Pop $0
FunctionEnd

; Stack 0: top level section index
Function SelectDefaultVariants
    Exch $0
    Push $1
    Push $2
    Push $3
    Push $4

    IntOp $0 $0 + 1

    StrCpy $1 0 ; Last section was group end
    StrCpy $4 "" ; Current compiler
 next:
    SectionGetFlags $0 $2
    IfErrors bail
    IntOp $3 $2 & ${SF_SECGRPEND}
    StrCmp $3 0 not_end
    StrCmp $1 0 0 bail ; two groups in a row means we are backing out
 not_end:
    StrCpy $1 $3
    IntOp $3 $2 & 6
    StrCmp $3 0 0 not_variant
    SectionGetText $0 $2
    Push $4
    Push $2
    Push $0
    call MaybeSelectVariant
    goto variant
 not_variant:
    SectionGetText $0 $4
 variant:
    IntOp $0 $0 + 1
    goto next
 bail:
    Pop $4
    Pop $3
    Pop $2
    Pop $1
    Pop $0
FunctionEnd

Function .onSelChange
    ClearErrors
    StrCpy $0 5 ; Section index
    StrCpy $1 0 ; Lib index
  next:
    SectionGetText $0 $2
    IfErrors bail
    StrCpy $3 $2 5
    StrCmp $3 "Boost" 0 not_lib
    StrCpy $3 $selected_libs 1 $1 ; $3 == old flag
    SectionGetFlags $0 $4 ; $4 == flag
    IntOp $5 $4 & 65
    StrCmp $5 0 not_true
    StrCpy $5 1
  not_true:
    StrCmp $3 $5 not_toggled 0
    StrCpy $6 $selected_libs $1 ; Before
    IntOp $7 $1 + 1
    StrCpy $7 $selected_libs "" $7 ; After
    StrCpy $selected_libs "$6$5$7"
    StrCmp $5 1 0 not_selected
    ; -- New library was selected, select default variants
    Push $0
    call SelectDefaultVariants
  not_selected:
  not_toggled:
    IntOp $1 $1 + 1
  not_lib:
    IntOp $0 $0 + 1
    goto next
  bail:
FunctionEnd

Function .onInit
    !insertmacro MUI_INSTALLOPTIONS_EXTRACT "select_mirror.ini"
    !insertmacro MUI_INSTALLOPTIONS_EXTRACT "default_variants.ini"

    call initSelectionFlags

    StrCpy $use_boost_consulting 0
    StrCpy $installed_tools 0
FunctionEnd

Function CompilerAutoDetect
    !insertmacro MUI_INSTALLOPTIONS_DISPLAY "autodetect.ini"
FunctionEnd

Function RelGotoPage
  IntCmp $R9 0 0 Move Move
    StrCmp $R9 "X" 0 Move
      StrCpy $R9 "120"
 
  Move:
  SendMessage $HWNDPARENT "0x408" "$R9" ""
FunctionEnd

Section -"Installation directory"
  CreateDirectory $INSTDIR

  WriteRegStr HKLM "SOFTWARE\${PUBLISHER}\${VERSION}" "InstallRoot" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\boost_${NORMALIZED_VERSION}" "DisplayName" "${NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\boost_${NORMALIZED_VERSION}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\boost_${NORMALIZED_VERSION}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\boost_${NORMALIZED_VERSION}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
SectionEnd

; The stuff to install''']
    
    def zip_section(title, kb, basename, success_var = None):
        return (r'''
Section "%(title)s"
    AddSize %(kb)d
    StrCpy $0 "%(basename)s.zip"''' % locals()
                + (
                dvd and r'''
    ZipDLL::extractall "$EXEDIR\data\$0" "$INSTDIR"
    Pop $2 ; error message
    StrCmp $2 "success" success 0
    MessageBox MB_OK "Failed to unzip file! $2 $EXEDIR\data\$0 $INSTDIR"
    Quit
  success:'''
                or r'''

    ; Skip if already downloaded
    IfFileExists $INSTDIR\$0 0 +2
    goto success

    ${StrTok} $1 $mirror_urls "|" "$mirror_selected" "1"
    inetc::get "$1$0" "$INSTDIR\$0" /END
    Pop $2
    StrCmp $2 "OK" success
    StrCmp $2 "Cancelled" cancel
    MessageBox MB_OK "Download $1$0 failed: $2"
    StrCmp $select_new_mirror 1 failed_again
    StrCpy $select_new_mirror 1
    StrCpy $R9 -4
    call RelGotoPage
  failed_again:
  cancel:
    Return
  success:
    Push $0
    Push ""''' 
                ) 
                + (success_var and r'''
    StrCpy $%(success_var)s 1''' or '') % locals()
                + r'''
SectionEnd
''')


    contents += [
        zip_section('Boost header files (required)', 4267, 'boost_%s_headers' % version),
        r'''
; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  StrCmp $select_new_mirror 1 0 dont_skip
  Return
 dont_skip:

  CreateDirectory "$SMPROGRAMS\${NAME}"
  CreateShortCut "$SMPROGRAMS\${NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

SectionEnd

;--------------------------------
''']

    def download_file_function(version):
        return (r'''
Function DownloadFile
    IfFileExists $INSTDIR\lib\* +2
    CreateDirectory $INSTDIR\lib
    Pop $0
    StrCpy $0 "$0.zip"'''
                + (dvd and r'''
    ZipDLL::extractall $EXEDIR\data\$0 $INSTDIR\lib
    Pop $2 ; error message
    StrCmp $2 "success" success 0
    MessageBox MB_OK "Failed to unzip file! $2"
    Quit
  success:'''
                   or r'''

    ; Skip if already downloaded
    IfFileExists $INSTDIR\lib\$0 0 +2
    Return

    ${StrTok} $1 $mirror_urls "|" "$mirror_selected" "1"

    ${If} $1 == "http://www.boostpro.com/boost-binaries/%(version)s/"
        StrCpy $use_boost_consulting 1
    ${EndIf}

    ${If} $use_boost_consulting == 1
        StrCpy $1 "http://www.boostpro.com/boost-binaries/%(version)s/"
    ${EndIf}

  try_again:
    inetc::get "$1$0" "$INSTDIR\lib\$0" /END
    Pop $1
    StrCmp $1 "OK" success
    StrCmp $1 "Cancelled" cancel
  failed_again:
    ; failed twice, try boostpro.com
    ${If} $use_boost_consulting == 0
        StrCpy $1 "http://www.boostpro.com/boost-binaries/%(version)s/"
        StrCpy $use_boost_consulting 1
        goto try_again
    ${Else}
        MessageBox MB_OK "File could not be downloaded: $0.zip"
        Abort
    ${EndIf}
  cancel:
    StrCpy $use_boost_consulting 0
    Return
  success:
    StrCpy $use_boost_consulting 0
    Push $0
    Push "lib\"''' % locals())
                   + r'''
FunctionEnd
''')
    
    contents += [ 
        download_file_function(version),
        zip_section('Source and Documentation', 14958, 'boost_%s_doc_src' % version),
        zip_section('Tools (source and binary)', 1122, 'boost_%s_tools' % version, success_var = 'installed_tools'),
        r'''

; ---------------------------------------------------------------------
%(sections)s
; ---------------------------------------------------------------------
''' % locals()]

    if not dvd:
        contents.append(r'''
Section -unzip
  another_file:
    Pop $1
    IfErrors bail
    Pop $0
    ZipDLL::extractall $INSTDIR\$1$0 $INSTDIR\$1
    Pop $2 ; error message
    StrCmp $2 "success" +2 0
    MessageBox MB_OK "Failed to unzip! $2"
    Delete $INSTDIR\$1$0
    Goto another_file
  bail:
SectionEnd

''')

    contents.append(r'''
;--------------------------------

Section "Add to path"
  StrCmp $installed_tools "0" 0 false
  MessageBox MB_YESNO "Boost prebuilt tools were installed to $INSTDIR\bin. Would you like to add that to PATH?" IDYES true IDNO false
true:
  Push "$INSTDIR\bin"
  Call AddToPath
false:
SectionEnd

; Uninstaller

Section "Uninstall"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\boost_${NORMALIZED_VERSION}"
  ; Leave SOFTWARE\${PUBLISHER} in case there is another Boost version installed
  DeleteRegKey HKLM "SOFTWARE\${PUBLISHER}\${VERSION}"

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\${NAME}\*.*"

  Push "$INSTDIR\bin"
  Call un.RemoveFromPath

  ; Remove directories used
  RMDir "$SMPROGRAMS\${NAME}"
  RMDir /r "$INSTDIR"

SectionEnd
''')
    return ''.join(contents)

def test_template(dvd = False):
    return os.path.join('test', ('dvd-' if dvd else '') + 'installer.nsi.template')

if __name__ == '__main__':
    import subprocess, os, sys, re

    # This test attempts to generate the old template files and
    # compares the result with the original.  NOTE: it depends on
    # having a working diff in the PATH.  The output should only
    # differ by blank lines and the occasional comment

    regenerate = '--regenerate-test' in sys.argv[1:]
            
    for dvd in False,True:

        if regenerate:
            f = open(test_template(dvd=dvd), 'w')
        else:
            from tempfile import NamedTemporaryFile
            f = NamedTemporaryFile(mode='w')

        f.write(
            re.sub('(?<!\r)\n', '\r\n',
                   generate(
                    dvd=dvd, 
                    version=r'${NORMALIZED_VERSION}', 
                    human_version=r'%(human_version)s', 
                    sections='%(sections)s',
                    architecture='32'
                    )))
        f.flush()
        
        if not regenerate:
            print subprocess.Popen(
                ['diff', '-wdu', test_template(dvd=dvd), f.name]).communicate()[0]

            if not dvd:
                print
                print '=============================='
                print
    
    
