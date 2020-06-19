from sys import argv
from enum import Enum
import os

'''
arithmetic/logical:
add, sub, neg
eq,gt,lt,and,or,not

stack:
(push|pop) segment i

segments:
local, argument, this, that
constant
static
temp
pointer
'''
INT_MAX = 65535
ADDR_MAX = 32767 # also signed max
RAM_MAX = 16383
KBD = 24576

class CommandType(Enum):
    INVALID_COMMAND = 0
    C_ARITHMETIC = 1
    C_PUSH = 2
    C_POP = 3
    C_LABEL = 4
    C_GOTO = 5
    C_IF = 6
    C_FUNCTION = 7
    C_RETURN = 8
    C_CALL = 9
        
def isCommand(line):
    return not line.startswith('//')

class ASM:
    SEGMENTS = {   "local": "LCL",
                "argument": "ARG",
                    "this": "THIS",
                    "that": "THAT"}
    
    POINTER = {0:"THIS", 1:"THAT"}
    TEMP_BASE = 5
    
    LOAD_SP = "@SP\n" + "A=M\n"
    LOAD_TOP = "@SP\n" + "A=M-1\n"

    LOAD_LCL = "@LCL\n" + "A=M\n"
    
    INC_SP = "@SP\n" + "M=M+1\n"
    PUSH_D = LOAD_SP + "M=D\n" + INC_SP
    
    DEC_DEREF = "AM=M-1\n"
    POP = "@SP\n" + DEC_DEREF
    POP_D = POP + "D=M\n" # post: address in A is where top used to be
    
    # could implement up to INT_MAX with an add
    # could also allow negative numbers by adding them to INT_MAX
        # up to -(ADDR_MAX+1)
    # @staticmethod not required since ASM is not instanced
    def valToD(val):
        if val < 0 or val > ADDR_MAX:
            raise ValueError(f"expected value between 0 and {ADDR_MAX}")
        result = f"@{val}\nD=A\n"
        return result
        
    def getASMLabel(label):
        return f"VM_LABEL_{label}"
        
        

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
        '''
        if numTokens == 1:
            if first == "return":
                return commandType.C_RETURN
            elif first in ["add", "sub", "neg"]:
                return CommandType.C_ARITHMETIC
            else:
                return CommandType.INVALID_COMMAND
        elif numTokens == 2:
            pass
        elif numTokens == 3:
            if first == "push":
                return CommandType.C_PUSH
            if first == "pop":
                return CommandType.C_POP
        '''

    def arg1(self):
        ctype = self.commandType()
        index = 1
        if ctype == CommandType.C_ARITHMETIC:
            index = 0
        return self.currentCommand.split()[index]
    
    def arg2(self):
        return self.currentCommand.split()[2]
    
        
class CodeWriter:
    logical = ["eq","lt","gt","and","or"]
    def __init__(self, fileOut):
        self.fileOut = fileOut
        self.module = os.path.basename(fileOut)[:-4]
        self.stream = open(fileOut, 'w')
        self.labelCount = dict((s, 0) for s in self.logical)
    
    # TODO: subtraction broken unless same sign (and < 2^15):
    # subtract only when same sign
    # else neg < pos
    '''
    if arg2 < 0
        if arg1 <= 0:
            subtract
        else:
            arg2 < arg1
    else:
        if arg1 >= 0:
            subtract
        else:
            arg1 < arg2           
    '''
    def getComparison(self, command):
        jmpLabel = f"JMP_{command.upper()}_{self.labelCount[command]}"
        doneLabel= f"DONE_{command.upper()}_{self.labelCount[command]}"
        self.labelCount[command] += 1

        buffer = ASM.POP_D
        buffer += "A=A-1\n"
        buffer += "D=M-D\n"
        buffer += f"@{jmpLabel}\n"
        buffer += f"D;J{command.upper()}\n"
        buffer += ASM.LOAD_TOP
        buffer += "M=0\n"
        buffer += f"@{doneLabel}\n"
        buffer += "0;JMP\n"
        buffer += f"({jmpLabel})\n"
        buffer += ASM.LOAD_TOP
        buffer += "M=-1\n"
        buffer += f"({doneLabel})\n"
        return buffer
    
    def getUnary(self, command):
        buffer = ASM.LOAD_TOP
        if command == 'neg':
            buffer += "M=-M\n"
        elif command == 'not':
            buffer += "M=!M\n"
        else:
            print("WARNING: unrecognized unary command")
            buffer += "// WARNING: unrecognized unary command"
        return buffer

    
    def getBinary(self, command):
        buffer = ASM.POP_D
        buffer += "A=A-1\n"  
        if command == "add":
            buffer += "M=D+M\n"                       
        elif command == "sub":
            buffer += "M=M-D\n"
        elif command == "and":
            buffer += "M=M&D\n"           
        elif command == "or":
            buffer += "M=M|D\n"
        else:
            print("WARNING: unrecognized binary command")
            buffer += "// WARNING: unrecognized binary command\n" + "M=0\n"
        return buffer

    def writeArithmetic(self, command):
        self.stream.write(f"// {command}\n")
    
        if command in ["add", "sub", "and", "or"]:
            self.stream.write(self.getBinary(command))
            
        elif command in ["neg", "not"]:
            self.stream.write(self.getUnary(command))   
        
        elif command in ["eq", "lt", "gt"]:
            self.stream.write(self.getComparison(command))  
        else:
            print("WARNING: unrecognized arithmetic/logical command")
            self.stream.write("// WARNING: unrecognized arithmetic/logical command\n")

    def writePushPop(self, commandType, segment, index):        
        if commandType == CommandType.C_PUSH:
            self.stream.write("// push %s %d\n" % (segment, index))
            if segment == "constant":
                buffer = ASM.valToD(index)
                buffer += ASM.PUSH_D
                self.stream.write(buffer)
            elif segment in ASM.SEGMENTS: # segments local, argument, this, that
                buffer = ASM.valToD(index)
                buffer += f"@{ASM.SEGMENTS[segment]}\n"
                buffer += "D=D+M\n"
                buffer += "A=D\n"
                buffer += "D=M\n"
                buffer += ASM.PUSH_D
                self.stream.write(buffer)
            elif segment == "static":
                buffer = f"@{self.module}.{index}\n"
                buffer += "D=M\n"
                buffer += ASM.PUSH_D
                self.stream.write(buffer)
            elif segment == "temp":
                if index > 8:
                    print("WARNING: temp index > 7")
                    self.stream.write("// WARNING: temp index > 7\n")
                buffer = ASM.valToD(index)
                buffer += "@5\n"
                buffer += "D=D+A\n"
                buffer += "A=D\n"
                buffer += "D=M\n"
                buffer += ASM.PUSH_D
                self.stream.write(buffer)
            elif segment == "pointer":
                buffer = f"@{ASM.POINTER[index]}\n"
                buffer += "D=M\n"
                buffer += ASM.PUSH_D
                self.stream.write(buffer)
            else:
                print("WARNING: unrecognized segment name")
                self.stream.write("// WARNING: unrecognized segment name\n")
                   
        elif commandType == CommandType.C_POP:
            self.stream.write("// pop %s %d\n" % (segment, index))
            if segment == "constant":
                print("WARNING: attempted to pop to constant segment")
                self.stream.write("// WARNING: attempted to pop to constant segment\n")
                self.stream.write("//\t\tCurrent stack item will be lost\n")
                self.stream.write(ASM.POP)
            elif segment in ASM.SEGMENTS: # local, argument, this, that
                buffer = ASM.valToD(index)
                buffer += f"@{ASM.SEGMENTS[segment]}\n"
                buffer += "D=D+M\n"
                buffer += "@R13\n"
                buffer += "M=D\n"
                buffer += ASM.POP_D
                buffer += "@R13\n"
                buffer += "A=M\n"
                buffer += "M=D\n"
                self.stream.write(buffer)
            elif segment == "static":
                buffer = ASM.POP_D
                buffer += f"@{self.module}.{index}\n"
                buffer += "M=D\n"
                self.stream.write(buffer)
            elif segment == "temp":
                if index > 8:
                    print("WARNING: temp index > 7")
                    self.stream.write("// WARNING: temp index > 7\n")
                '''
                buffer = ASM.valToD(index)
                buffer += "@5\n"
                buffer += "D=D+A\n"
                buffer += "@R13\n"
                buffer += "M=D\n"
                '''
                buffer = ASM.POP_D
                '''
                buffer += "@R13\n"
                buffer += "A=M\n"
                '''
                buffer += f"@{index + ASM.TEMP_BASE}\n"
                buffer += "M=D\n"
                self.stream.write(buffer)
            elif segment == "pointer":
                buffer = ASM.POP_D
                buffer += f"@{ASM.POINTER[index]}\n"
                buffer += "M=D\n"
                self.stream.write(buffer)

            else:
                print("WARNING: attempted to push to unknown segment")
                self.stream.write("// WARNING: attempted to push to unknown segment")
    
    def writeLabel(self, label):
        buffer = f"// label {label}\n"
        buffer += f"({ASM.getASMLabel(label)})\n"
        self.stream.write(buffer)
        
    def writeGoto(self, label):
        buffer = f"// goto {label}\n"
        buffer += f"@{ASM.getASMLabel(label)}\n"
        buffer += "0;JMP\n"
        self.stream.write(buffer)
        
    def writeIf(self, label):
        buffer = f"// if-goto {label}\n"
        buffer += ASM.POP_D
        buffer += f"@{ASM.getASMLabel(label)}\n"
        buffer += "D;JNE\n"
        self.stream.write(buffer)
    
    def writeFunction(self, functionName, numVars):
        buffer = f"// function {functionName} {numVars}\n"
        self.stream.write(buffer)
    def writeCall(self, functionName, numArgs):
        buffer = f"// call {functionName} {numArgs}\n"
        self.stream.write(buffer)
    def writeReturn(self):
        buffer = f"// return\n"
        self.stream.write(buffer)
        
    def writeInit(self):
        buffer = f"// init\n"
        self.stream.write(buffer)        
        
    def close(self):
        self.stream.close()


def main():
    #argv = ["VMTranslator", "test.vm"]
    argc = len(argv)
    if argc != 2:
        print("Usage: %s <File or Directory>" % argv[0])
        return
    
    inFile = argv[1]
    
    if os.path.isfile(inFile):
        if not argv[1].endswith(".vm"):
            print("Error: Expected .vm file!")
            return
        outFile = inFile[:-2] + "asm"
    elif os.path.isdir(inFile):
        print("Directory Found!")
        vmFiles = [os.path.join(inFile, file) for file in os.listdir(inFile) if file.endswith(".vm")]
        if len(vmFiles) < 1:
            print("No vm files found in", inFile)
            return
        print(len(vmFiles), "vm file(s) found.")
        return
    else:
        print(f"Error: no file or directory found named \"{inFile}\"")
        return

# create parser and writer

    parser = Parser(inFile)
    print(f"parsing from '{inFile}'...")
    writer = CodeWriter(outFile)
    print(f"writing to '{outFile}'...")
    while(parser.hasMoreCommands()):
        parser.advance()
        comType = parser.commandType()
        current = parser.currentCommand
        if comType == CommandType.C_ARITHMETIC:
            writer.writeArithmetic(current)
        elif comType in [CommandType.C_PUSH, CommandType.C_POP]:
            writer.writePushPop(comType, parser.arg1(), int(parser.arg2()))
        elif comType == CommandType.C_LABEL:
            writer.writeLabel(parser.arg1())
        elif comType == CommandType.C_GOTO:
            writer.writeGoto(parser.arg1())
        elif comType == CommandType.C_IF:
            writer.writeIf(parser.arg1())
        elif comType == CommandType.C_FUNCTION:
            writer.writeFunction(parser.arg1(), parser.arg2())
        elif comType == CommandType.C_CALL:
            writer.writeCall(parser.arg1(), parser.arg2())
        elif comType == CommandType.C_RETURN:
            writer.writeReturn()
        else:
            print("Error: unrecognized command")
      
    parser.close()
    writer.close()
    print("done.")


if __name__ == "__main__":
    main()

