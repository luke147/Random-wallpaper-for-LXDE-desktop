#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright © 2016 Lukáš Vlček

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Help for executing with cron application:

Export shell variables: EDITOR and VISUAL:
export EDITOR="your editor"
export VISUAL="your editor"

Enter command: crontab -e

Write this text and replace or remove "path with the script":
PATH="/bin:/usr/bin:/usr/local/bin:path with the script"
# minutes    hours    day in month   mounth    day in week    command
      */N        *               *        *              *    random-wallpaper-for-lxde-desktop.py

The desktop background will change every N. minute.
"""

import sys, os
import subprocess, shlex
import random
import tempfile
from six import string_types


try:
    if (sys.version_info[0] != 2): # interpret is Python in version 2
        reload(sys)
        sys.setdefaultencoding("utf-8")
except:
    sys.stderr.write("Error for encoding setting UTF-8")
    sys.stderr.flush()
    # only for Python 3: print("Error for encoding setting UTF-8", file = sys.stderr, flush = True)
    sys.exit(1)


class EError(Exception):
    strError = "Error"
    strValue = ""
    returnCode = 1
    
    def __init__(self, strValue = "", strError = "", returnCode = 1):
        Exception.__init__(self, strValue)
        self.strValue = str(strValue)
        if (strError != ""):
            self.strError = strError
        if (returnCode != self.returnCode):
            self.returnCode = returnCode

def errorPrint(s):
    try:
        s = str(s)
        # only for Python 3: print(s, file = sys.stderr, flush = True)
        sys.stderr.write(s)
        sys.stderr.flush()
        return True
    except:
        return False

def isPython2():
    if (sys.version_info[0] > 2):
        return False
    return True


class Params:
    __showHelp = False
    __showVersion = False
    __picsPath = ""
    __display = ":0"
    __wallpaperMode = "center"
    __helpParam = ("-h", "--help")
    __displayParam = "--display="
    __wallpaperModeParam = "--wallpaper-mode="
    __allWallpaperModes = ("color", "stretch", "fit", "center", "tile")
    __versionParam = ("-v", "--version")
    stringType = None
    
    @property
    def showHelp(self):
        return self.__showHelp
    
    @property
    def showVersion(self):
        return self.__showVersion
    
    @property
    def picsPath(self):
        return self.__picsPath
    
    @property
    def wallpaperMode(self):
        return self.__wallpaperMode
    
    @property
    def display(self):
        return self.__display
    
    @property
    def wallpaperModeParam(self):
        return self.__wallpaperModeParam
    
    @property
    def displayParam(self):
        return self.__displayParam
    
    @property
    def helpParam(self):
        return self.__helpParam
    
    @property
    def versionParam(self):
        return self.__versionParam
    
    def __init__(self, picsPath, display = "", wallpaperMode = "", showHelp = False):
        self.__picsPath = picsPath
        if (display != ""):
            self.__display = display
        if (wallpaperMode != ""):
            self.__wallpaperMode = wallpaperMode
        if (showHelp):
            self.__showHelp = showHelp
    
    @staticmethod
    def paramsAreEqual(enteredParam, savedParam):
        try:
            enteredParamIsString = isinstance(enteredParam, string_types)
            savedParamIsString = isinstance(savedParam, string_types)
            savedParamIsTuple = isinstance(savedParam, tuple)
            if ((savedParamIsTuple == savedParamIsString) or (not enteredParamIsString)):
                raise EError("Internal error for specifiyng parameters.")
            
            if (enteredParamIsString == savedParamIsString):
                if ("=" in enteredParam):
                    if (enteredParam.startswith(savedParam)):
                        return True
                    else:
                        return False
                if (enteredParam == savedParam):
                    return True
                else:
                    return False
            
            if (savedParamIsTuple):
                for savedP in savedParam:
                    if ("=" in savedP):
                        if (enteredParam.startswith(savedP)):
                            return True
                    if (enteredParam == savedP):
                        return True
            
            return False
        except EError as e:
            errorPrint("%s: %s\n" % (e.strError, e.strValue))
            return False
        except BaseException as e:
            errorPrint("Unknown error: %s\n" % e)
            return False
    
    @staticmethod
    def getParams():
        params = None
        try:
            picsPath = ""
            display = ""
            wallpaperMode = ""
            showHelp = False
            
            for i in range(0, len(sys.argv)):
                if (i == 0):
                    continue
                if (Params.paramsAreEqual(sys.argv[i], Params.__helpParam)):
                    showHelp = True
                    break
                if (Params.paramsAreEqual(sys.argv[i], Params.__versionParam)):
                    showVersion = True
                    break
                if (Params.paramsAreEqual(sys.argv[i], Params.__wallpaperModeParam)):
                    wModeFromParam = sys.argv[i][len(Params.__wallpaperModeParam):]
                    for wMode in Params.__allWallpaperModes:
                        if (wMode == wModeFromParam):
                            wallpaperMode = wModeFromParam
                    continue
                
                if (Params.paramsAreEqual(sys.argv[i], Params.__displayParam)):
                    displayFromParam = sys.argv[i][len(Params.__displayParam):]
                    if ( (displayFromParam[0:1]) == ":" and (displayFromParam[1:].isdigit()) ):
                        display = displayFromParam
                    continue
                
                if (not os.path.exists(sys.argv[i])):
                    raise EError("File '%s' doesn't exists." % sys.argv[i])
                picsPath = sys.argv[i]
            
            params = Params(picsPath, display, wallpaperMode, showHelp)
        except EError as e:
            errorPrint("%s: %s\n" % (e.strError, e.strValue))
            params = None
        except BaseException as e:
            errorPrint("Unknown error: %s\n" % e)
            params = None
        finally:
            return params


class App:
    tmpFilename = ""
    lxdeFileManager = 'pcmanfm'
    pcmanfmFindingCmd = ""
    folderWithWallpapers = ""
    defPicturesPath = "XDG_PICTURES_DIR"
    returnCode = 0
    terminalColumns = -1
    scriptVersion = "1.0"
    scriptName = "Random wallpaper for LXDE desktop"
    scriptNameWithExt = ""
    scriptNameWithoutExt = ""
    copyright = "Copyright © 2016 Lukáš Vlček"
    
    def __init__(self):        
        # --------------------------------------------- variables ---------------------------------------------
        self.scriptNameWithExt = os.path.basename(sys.argv[0])
        self.scriptNameWithoutExt, scriptExt = os.path.splitext(self.scriptNameWithExt)
        self.tmpFilename = "%s.tmp" % os.path.join(tempfile.gettempdir(), self.scriptNameWithoutExt)
        self.lxdeFileManager = 'pcmanfm'
        self.pcmanfmFindingCmd = 'which "%s" &> /dev/null' % self.lxdeFileManager
        self.folderWithWallpapers = ""
        self.defPicturesPath = "XDG_PICTURES_DIR"

    def printScriptVersion(self):
        print("%s %s\n%s" % (self.scriptName, self.scriptVersion, self.copyright))

    def getTerminalColumns(self):
        columns = 0
        try:
            if (isPython2()):
                cmd = "stty size 2>/dev/null"
                sizes = subprocess.check_output(cmd, shell = True)
                if (" " in sizes):
                    sizes = sizes.split()
                    if (sizes[1].isdigit()):
                        columns = int(sizes[1])
            else:
                terminalSize = os.get_terminal_size()
                columns = int(terminalSize.columns)
        except:
            columns = 0
        finally:
            return columns

    def printHelpRow(self, s):
        if (self.terminalColumns < 0):
            self.terminalColumns = self.getTerminalColumns()
        spaceCount = 0
        tabPos = s.rfind("\t")
        strBehindTab = s[tabPos + 1:]
        s = s.expandtabs()
        if (tabPos != -1):
            spaceCount = s.find(strBehindTab)
        
        len_entireStr = len(s)
        if (len_entireStr > self.terminalColumns):
            lastSpacePos = 0
            firstPos = spaceCount
            lastPos = self.terminalColumns
            len_residuedStr = len_entireStr
            while (self.terminalColumns < (len_residuedStr)):
                lastSpacePos = s.rfind(" ", firstPos, lastPos)
                if (lastSpacePos == -1):
                    break
                residuedStr = s[lastSpacePos + 1:]
                if (spaceCount > 0):
                    residuedStr = residuedStr.rjust(len(residuedStr) + spaceCount)
                s = "%s\n%s" % (s[0:lastSpacePos], residuedStr)
                firstPos = lastSpacePos
                lastPos = len_entireStr
                if ((firstPos * 2) < lastPos):
                    lastPos = firstPos * 2
                len_residuedStr = len_entireStr - firstPos
        
        print(s)

    def showHelp(self):
        self.printScriptVersion()
        self.printHelpRow("\nUsage:\n%s [[path to picture directory] [--wallpaper-mode=(color|stretch|fit|center|tile)] [--display=:<display number>]]|[-h|--help]|[-v|--version]\n" % self.scriptNameWithExt)
        self.printHelpRow("Set a random wallpaper from default directory with pictures or from your directory.")
        self.printHelpRow("Finding default directory:")
        self.printHelpRow("Application will find the wallpaper in picture directory from '~/.config/user-dirs.dirs' file if no argument is specified.")
        self.printHelpRow("Application will find 'XDG_PICTURES_DIR' variable in the config file.")
        print("\nArguments:")
        self.printHelpRow("  \"path to picture directory\"\tSet a random wallpaper from the picture directory.")
        self.printHelpRow("  --display=:<display number>\tX display to use.")
        self.printHelpRow("  --wallpaper-mode=<mode>\tSet a mode of desktop wallpaper. Value can be: center|color|stretch|fit|crop|tile|sreen Default value is: center" )
        self.printHelpRow("  -h|--help\t\t\tShow this help message.")
        self.printHelpRow("  -v|--version\t\t\tShow script version and copyright.")

    def findPicsDir(self):
        picsPath = ""
        try:
            userDirsFile = "user-dirs.dirs"
            xdgPicsDir = "XDG_PICTURES_DIR"
            if self.defPicturesPath in os.environ:
                picsPath = os.path.expandvars(os.environ[self.defPicturesPath])
                if (os.path.isdir(picsPath)):
                    return picsPath
            
            filenames = ( os.path.join('$XDG_CONFIG_HOME', userDirsFile), os.path.join('$HOME', '.config', userDirsFile) )
            filename = ""
            for f in filenames:
                f = os.path.expandvars(f)
                if (os.path.isfile(f)):
                    filename = f
                    break
            
            if (filename == ""):
                raise EError("File '%s' doesn't exists." % filenames[1])
            
            data = ""
            with open(filename) as fVars:
                while (not xdgPicsDir in data):
                    data = fVars.readline()
            
            if (data == ""):
                raise EError("File '%s' doesn't contains setting of '%s' variable." % (filename, xdgPicsDir))
            
            varName, picsPath = data.split('=')
            picsPath = picsPath.strip()
            picsPath = picsPath.strip('"')
            picsPath = os.path.expandvars(picsPath)
        except EError as e:
            errorPrint("%s: %s" % (e.strError, e.strValue))
            picsPath = ""
        except KeyboardInterrupt:
            errorPrint("\nSkript was terminated by user.\n")
            returnCode = 1
        except BaseException as e:
            errorPrint("Unknown error: %s\n" % e)
            picsPath = ""
        finally:
            return picsPath

    def execute(self):
        try:
            self.returnCode = os.EX_OK
            #----------------------------------------------- information printing -----------------------------------------------
            print('Script for random change of wallpaper in LXDE\n')

            params = Params.getParams()
            if (params == None):
                raise EError("Application will be terminated", "")
            
            if (params.showHelp):
                self.showHelp()
                sys.exit(self.returnCode)
            
            if (params.showVersion):
                self.printScriptVersion()
                sys.exit(self.returnCode)
            
            if (params.picsPath == ""):
                folderWithWallpapers = self.findPicsDir()
            else:
                folderWithWallpapers = params.picsPath
                
            if folderWithWallpapers == "":
                raise EError("Picture folder wasn't found even set.")

            #----------------------------------------------- information printing -----------------------------------------------
            print('wallpaper directory: %s\n' % folderWithWallpapers)

            # --------------------------------------------- elimination of errors ---------------------------------------------
            if not os.path.exists(folderWithWallpapers):
                raise EError("Path '%s' doesn't exist." % folderWithWallpapers)
            if not os.path.isdir(folderWithWallpapers):
                raise EError("Path '%s' isn't folder." % folderWithWallpapers)
            if ( not os.access(folderWithWallpapers, os.R_OK) ) or ( not os.access(folderWithWallpapers, os.X_OK) ):
                raise EError("You're not allowed to access folder: '%s'" % folderWithWallpapers)
            if ( os.system(self.pcmanfmFindingCmd) != 0 ):
                raise EError("'%s' application isn't installed or you haven't application path in PATH variable." % self.lxdeFileManager)

            # --------------------------------------------- selecting the wallpaper ---------------------------------------------
            listWallpapers = os.listdir(folderWithWallpapers)

            for i in range(len(listWallpapers) - 1, -1, -1):
                if os.path.isdir(os.path.join(folderWithWallpapers, listWallpapers[i])):
                    del listWallpapers[i]

            countOfFindedWallpapers = len(listWallpapers)

            countOfRemovedWallpapers = 0
            itemsForRemoving = []
            if (os.path.exists(self.tmpFilename)):
                with open(self.tmpFilename, "r") as fSelectedWallpaperList:
                    listOfWallpaperForRemoving = fSelectedWallpaperList.readlines()
                    if (len(listOfWallpaperForRemoving) > 0):
                        for itemForChecking in range(0, countOfFindedWallpapers):
                            for itemForRemoving in range(0, len(listOfWallpaperForRemoving)):
                                wallpaperForRemoving = listOfWallpaperForRemoving[itemForRemoving]
                                posEndLine = wallpaperForRemoving.rfind("\n")
                                if posEndLine != -1:
                                    wallpaperForRemoving = wallpaperForRemoving[0 : posEndLine]
                                if listWallpapers[itemForChecking] == wallpaperForRemoving:
                                    itemsForRemoving.append(itemForChecking)
                                    countOfRemovedWallpapers += 1
            
            writeMode = "a+"
            if (countOfFindedWallpapers - countOfRemovedWallpapers) < 5:
                writeMode = "w+"

            itemsForRemoving.sort()
            for i in range(len(itemsForRemoving) - 1, -1, -1):
                if i != (len(itemsForRemoving) - 1):
                    if itemsForRemoving[i] == itemsForRemoving[i + 1]:
                        continue
                listWallpapers.pop(itemsForRemoving[i])

            countOfFindedWallpapers = len(listWallpapers)

            indexWallpaper = random.randint(0, countOfFindedWallpapers - 1)
            selectedWallpaper = listWallpapers[indexWallpaper]
            print("Selected walpaper: %s" % selectedWallpaper)

            with open(self.tmpFilename, writeMode) as fSelectedWallpaperList:
                fSelectedWallpaperList.flush()
                fSelectedWallpaperList.write("%s\n" % selectedWallpaper)

            # --------------------------------------------- the wallpaper setting ---------------------------------------------
            commandLine = '%s "--set-wallpaper=%s" "%s%s" "%s%s"' % ( self.lxdeFileManager, os.path.join(folderWithWallpapers, selectedWallpaper), params.wallpaperModeParam, params.wallpaperMode, params.displayParam, params.display )
            args = shlex.split(commandLine)
            process = subprocess.Popen(args)
            process.wait()

            if process.returncode != 0:
                raise EError("Wallpaper setting process failed.")

        except EError as e:
            errorPrint("%s: %s\n" % (e.strError, e.strValue))
            self.returnCode = e.returnCode
        except SystemExit as e:
            self.returnCode = 1
            msg = str(e)
            if (msg.isdigit()):
                self.returnCode = int(msg)
            else:
                errorPrint(msg)
        except KeyboardInterrupt:
            errorPrint("\nSkript was terminated by user.\n")
            self.returnCode = 1
        except BaseException as e:
            errorPrint("Unknown error: %s\nApplication will be terminated.\n" % e)
            self.returnCode = 1
        finally:
            return self.returnCode



returnCode = os.EX_OK
try:
    app = App()
    returnCode = app.execute()
except EError as e:
    errorPrint("%s: %s\n" % (e.strError, e.strValue))
    returnCode = e.returnCode
except SystemExit as e:
    returnCode = 1
    msg = str(e)
    if (msg.isdigit()):
        returnCode = int(msg)
    else:
        errorPrint(msg)
except KeyboardInterrupt:
    errorPrint("\nSkript was terminated by user.\n")
    returnCode = 1
except BaseException as e:
    errorPrint("Unknown error: %s\nApplication will be terminated.\n" % e)
    returnCode = 1
finally:
    sys.exit(returnCode)
