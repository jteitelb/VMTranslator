from commandtype import CommandType

def isCommand(line):
    return not line.startswith('//')

class Parser:
    def __init__(self, fileIn):
        self.fileIn = fileIn
        self.stream = open(fileIn, 'r')
        
        self.currentCommand = ''
        self.nextCommand = ''
        self.advance()
            
    def hasMoreCommands(self):
        return self.nextCommand != ''
    
    def advance(self):
        self.currentCommand = self.nextCommand
        while True:
            line = self.stream.readline()
            if line == '':
                self.nextCommand = ''
                break
            if isCommand(line):
                if (line.endswith('\n')):
                    line = line[:-1]
                if (line.endswith('\r')):
                    line = line[:-1]
                if len(line) == 0:
                    continue
                self.nextCommand = line
                break
        return self.currentCommand
     
    def close(self):
        self.stream.close()

    def commandType(self):
        split = self.currentCommand.split() # splits based on whitespace
        numTokens = len(split)
        if numTokens == 0:
            print("no tokens for commandType to operate on")
            return CommandType.INVALID_COMMAND
        
        first = split[0]
        commandFirst = {CommandType.C_ARITHMETIC: {"add", "sub", "neg","eq","lt","gt","and","or"},
                        CommandType.C_PUSH: {"push"},
                        CommandType.C_POP: {"pop"},
                        CommandType.C_LABEL: {"label"},
                        CommandType.C_GOTO: {"goto"},
                        CommandType.C_IF: {"if-goto"},
                        CommandType.C_FUNCTION: {"function"},
                        CommandType.C_RETURN: {"return"},
                        CommandType.C_CALL: {"call"}}
        
        for cType in commandFirst:
            if first in commandFirst[cType]:
                return cType

        return CommandType.INVALID_COMMAND


    def arg1(self):
        ctype = self.commandType()
        index = 1
        if ctype == CommandType.C_ARITHMETIC:
            index = 0
        return self.currentCommand.split()[index]
    
    def arg2(self):
        return self.currentCommand.split()[2]
