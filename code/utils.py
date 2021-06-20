import sys
import os
import copy

def currentFuncName(n=0): return sys._getframe(n + 1).f_code.co_name

def openFile(filePath):
    _file = None
    try:
        absFilePath = os.path.abspath(filePath)
        _file = open(absFilePath, "r")
    except Exception as exc:
        print exc
    return _file

def deepCopy(*arguments):
    returnArguments = []
    for argument in arguments:
        returnArguments.append(copy.deepcopy(argument))
    return tuple(returnArguments)