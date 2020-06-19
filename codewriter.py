import os

import asm
from commandtype import CommandType

class CodeWriter:
    logical = ["eq","lt","gt","and","or"]
    def __init__(self, fileOut):
        self.fileOut = fileOut
        self.module = os.path.basename(fileOut)[:-4]
        self.stream = open(fileOut, 'w')
        self.labelCount = dict((s, 0) for s in self.logical)
        self.returnLabelCount = 0
        self.currentFunction = ""
        
    
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

        buffer = asm.POP_D
        buffer += "A=A-1\n"
        buffer += "D=M-D\n"
        buffer += f"@{jmpLabel}\n"
        buffer += f"D;J{command.upper()}\n"
        buffer += asm.LOAD_TOP
        buffer += "M=0\n"
        buffer += f"@{doneLabel}\n"
        buffer += "0;JMP\n"
        buffer += f"({jmpLabel})\n"
        buffer += asm.LOAD_TOP
        buffer += "M=-1\n"
        buffer += f"({doneLabel})\n"
        return buffer
    
    def getUnary(self, command):
        buffer = asm.LOAD_TOP
        if command == 'neg':
            buffer += "M=-M\n"
        elif command == 'not':
            buffer += "M=!M\n"
        else:
            print("WARNING: unrecognized unary command")
            buffer += "// WARNING: unrecognized unary command"
        return buffer

    
    def getBinary(self, command):
        buffer = asm.POP_D
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
                buffer = asm.val_to_d(index)
                buffer += asm.PUSH_D
                self.stream.write(buffer)
            elif segment in asm.SEGMENTS: # segments local, argument, this, that
                buffer = asm.val_to_d(index)
                buffer += f"@{asm.SEGMENTS[segment]}\n"
                buffer += "D=D+M\n"
                buffer += "A=D\n"
                buffer += "D=M\n"
                buffer += asm.PUSH_D
                self.stream.write(buffer)
            elif segment == "static":
                buffer = f"@{self.module}.{index}\n"
                buffer += "D=M\n"
                buffer += asm.PUSH_D
                self.stream.write(buffer)
            elif segment == "temp":
                if index > 8:
                    print("WARNING: temp index > 7")
                    self.stream.write("// WARNING: temp index > 7\n")
                buffer = asm.val_to_d(index)
                buffer += "@5\n"
                buffer += "D=D+A\n"
                buffer += "A=D\n"
                buffer += "D=M\n"
                buffer += asm.PUSH_D
                self.stream.write(buffer)
            elif segment == "pointer":
                buffer = f"@{asm.POINTER[index]}\n"
                buffer += "D=M\n"
                buffer += asm.PUSH_D
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
                self.stream.write(asm.POP)
            elif segment in asm.SEGMENTS: # local, argument, this, that
                buffer = asm.val_to_d(index)
                buffer += f"@{asm.SEGMENTS[segment]}\n"
                buffer += "D=D+M\n"
                buffer += "@R13\n"
                buffer += "M=D\n"
                buffer += asm.POP_D
                buffer += "@R13\n"
                buffer += "A=M\n"
                buffer += "M=D\n"
                self.stream.write(buffer)
            elif segment == "static":
                buffer = asm.POP_D
                buffer += f"@{self.module}.{index}\n"
                buffer += "M=D\n"
                self.stream.write(buffer)
            elif segment == "temp":
                if index > 8:
                    print("WARNING: temp index > 7")
                    self.stream.write("// WARNING: temp index > 7\n")
                '''
                buffer = asm.valToD(index)
                buffer += "@5\n"
                buffer += "D=D+A\n"
                buffer += "@R13\n"
                buffer += "M=D\n"
                '''
                buffer = asm.POP_D
                '''
                buffer += "@R13\n"
                buffer += "A=M\n"
                '''
                buffer += f"@{index + asm.TEMP_BASE}\n"
                buffer += "M=D\n"
                self.stream.write(buffer)
            elif segment == "pointer":
                buffer = asm.POP_D
                buffer += f"@{asm.POINTER[index]}\n"
                buffer += "M=D\n"
                self.stream.write(buffer)

            else:
                print("WARNING: attempted to push to unknown segment")
                self.stream.write("// WARNING: attempted to push to unknown segment")

    def getLabel(self, label):
        return f"{self.module}.{self.currentFunction}${label}"

    def getFunctionLabel(self):
        return f"{self.module}.{self.currentFunction}"

    def getReturnLabel(self):
        self.returnLabelCount += 1
        return f"{self.module}.{self.currentFunction}$ret.{self.returnLabelCount}"
    
    def writeLabel(self, label):
        buffer = f"// label {label}\n"
        buffer += f"({self.getLabel(label)})\n"
        self.stream.write(buffer)
        
    def writeGoto(self, label):
        buffer = f"// goto {label}\n"
        buffer += f"@{self.getLabel(label)}\n"
        buffer += "0;JMP\n"
        self.stream.write(buffer)
        
    def writeIf(self, label):
        buffer = f"// if-goto {label}\n"
        buffer += asm.POP_D
        buffer += f"@{self.getLabel(label)}\n"
        buffer += "D;JNE\n"
        self.stream.write(buffer)

    
    def writeFunction(self, functionName, numVars):
        self.currentFunction = functionName
        buffer = f"// function {functionName} {numVars}\n"
        self.stream.write(buffer)
        
    def writeCall(self, functionName, numArgs):
        buffer = f"// call {functionName} {numArgs}\n"

        # push return address
        retLabel = self.getReturnLabel()
        buffer += asm.load(retLabel)
        buffer += "D=A\n"
        buffer += asm.PUSH_D
        
        #push LCL, ARG, THIS, THAT
        buffer += asm.push_address("LCL")
        buffer += asm.push_address("ARG")
        buffer += asm.push_address("THIS")
        buffer += asm.push_address("THAT")

        # ARG = SP - (5 + numArgs)
        offset = int(numArgs) + 5
        
        buffer += asm.ptr_to_d("SP") # D = SP
        buffer += f"@{offset}\n"
        buffer += "D=D-A\n" # D = SP - (5 + numArgs)
        buffer += asm.d_to_ptr("ARG") # ARG = D
        
        # LCL = SP
        buffer += asm.ptr_to_d("SP")
        buffer += asm.d_to_ptr("LCL")
        
        # goto function
        buffer += f"@{self.module}.{functionName}\n"
        buffer += "0;JMP\n"

        # write return address label
        buffer += f"({retLabel})\n"
        self.stream.write(buffer)
        
    def writeReturn(self):
        buffer = f"// return\n"
        self.stream.write(buffer)
        self.currentFunction = ""
        
    def writeInit(self):
        buffer = f"// init\n"
        self.stream.write(buffer)        
        
    def close(self):
        self.stream.close()
