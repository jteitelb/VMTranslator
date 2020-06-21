import os

import asm
from commandtype import CommandType


class CodeWriter:
    logical = ["eq", "lt", "gt", "and", "or"]

    def __init__(self, file_out):
        self.fileOut = file_out
        self.module = os.path.basename(file_out)[:-4]
        self.stream = open(file_out, 'w')
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

    def get_comparison(self, command):
        jmpLabel = f"JMP_{command.upper()}_{self.labelCount[command]}"
        doneLabel = f"DONE_{command.upper()}_{self.labelCount[command]}"
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

    @staticmethod
    def get_unary(command):
        buffer = asm.LOAD_TOP
        if command == 'neg':
            buffer += "M=-M\n"
        elif command == 'not':
            buffer += "M=!M\n"
        else:
            print("WARNING: unrecognized unary command")
            buffer += "// WARNING: unrecognized unary command"
        return buffer

    @staticmethod
    def get_binary(command):
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

    def write_arithmetic(self, command):
        self.stream.write(f"// {command}\n")

        if command in ["add", "sub", "and", "or"]:
            self.stream.write(self.get_binary(command))

        elif command in ["neg", "not"]:
            self.stream.write(self.get_unary(command))

        elif command in ["eq", "lt", "gt"]:
            self.stream.write(self.get_comparison(command))
        else:
            print("WARNING: unrecognized arithmetic/logical command")
            self.stream.write("// WARNING: unrecognized arithmetic/logical command\n")

    def write_push_pop(self, command_type, segment, index):
        if command_type == CommandType.C_PUSH:
            self.stream.write("// push %s %d\n" % (segment, index))
            if segment == "constant":
                buffer = asm.val_to_d(index)
                buffer += asm.PUSH_D
                self.stream.write(buffer)
            elif segment in asm.SEGMENTS:  # segments local, argument, this, that
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

        elif command_type == CommandType.C_POP:
            self.stream.write("// pop %s %d\n" % (segment, index))
            if segment == "constant":
                print("WARNING: attempted to pop to constant segment")
                self.stream.write("// WARNING: attempted to pop to constant segment\n")
                self.stream.write("//\t\tCurrent stack item will be lost\n")
                self.stream.write(asm.POP)
            elif segment in asm.SEGMENTS:  # local, argument, this, that
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

    def get_label(self, label):
        return f"{self.module}.{self.currentFunction}${label}"

    def get_function_label(self):
        return f"{self.module}.{self.currentFunction}"

    def get_return_label(self):
        self.returnLabelCount += 1
        return f"{self.module}.{self.currentFunction}$ret.{self.returnLabelCount}"

    def write_label(self, label):
        buffer = f"// label {label}\n"
        buffer += f"({self.get_label(label)})\n"
        self.stream.write(buffer)

    def write_goto(self, label):
        buffer = f"// goto {label}\n"
        buffer += f"@{self.get_label(label)}\n"
        buffer += "0;JMP\n"
        self.stream.write(buffer)

    def write_if(self, label):
        buffer = f"// if-goto {label}\n"
        buffer += asm.POP_D
        buffer += f"@{self.get_label(label)}\n"
        buffer += "D;JNE\n"
        self.stream.write(buffer)

    def write_function(self, function_name, num_vars):
        self.currentFunction = function_name
        buffer = f"// function {function_name} {num_vars}\n"
        buffer += "D=0\n"
        for i in range(int(num_vars)):
            buffer += asm.PUSH_D
        self.stream.write(buffer)

    def write_call(self, function_name, num_args):
        buffer = f"// call {function_name} {num_args}\n"

        # push return address
        retLabel = self.get_return_label()
        buffer += asm.load(retLabel)
        buffer += "D=A\n"
        buffer += asm.PUSH_D

        # push LCL, ARG, THIS, THAT
        buffer += asm.push_address("LCL")
        buffer += asm.push_address("ARG")
        buffer += asm.push_address("THIS")
        buffer += asm.push_address("THAT")

        # ARG = SP - (5 + num_args)
        offset = int(num_args) + 5

        buffer += asm.ptr_to_d("SP")  # D = SP
        buffer += f"@{offset}\n"
        buffer += "D=D-A\n"  # D = SP - (5 + num_args)
        buffer += asm.d_to_ptr("ARG")  # ARG = D

        # LCL = SP
        buffer += asm.ptr_to_d("SP")
        buffer += asm.d_to_ptr("LCL")

        # goto function
        buffer += f"@{self.module}.{function_name}\n"
        buffer += "0;JMP\n"

        # write return address label
        buffer += f"({retLabel})\n"
        self.stream.write(buffer)

    def write_return(self):
        buffer = f"// return\n"

        # endFrame = LCL
        buffer += asm.ptr_to_d("LCL")
        buffer += "@R13\n"
        buffer += "M=D\n"
        buffer += "@R15\n"
        buffer += "M=D\n"

        # return address = *(endFrame - 5)
        buffer += "@5\n"
        buffer += "D=D-A\n"
        buffer += "A=M\n"
        buffer += "D=M\n"
        buffer += "@R14\n"
        buffer += "M=D\n"

        # *ARG = pop(), move return to caller
        buffer += asm.POP_D
        buffer += "@ARG\n"
        buffer += "A=M\n"
        buffer += "M=D\n"

        # SP = ARG + 1
        buffer += "@ARG\n"
        buffer += "D=M+1\n"
        buffer += "@SP\n"
        buffer += "M=D\n"

        # THAT = *(endFrame-1)
        buffer += "@R15\n"
        buffer += "AM=M-1\n"
        buffer += "D=M\n"
        buffer += asm.d_to_ptr("THAT")

        # THIS = *(endFrame-2)
        buffer += "@R15\n"
        buffer += "AM=M-1\n"
        buffer += "D=M\n"
        buffer += asm.d_to_ptr("THIS")

        # ARG = *(endFrame-3)
        buffer += "@R15\n"
        buffer += "AM=M-1\n"
        buffer += "D=M\n"
        buffer += asm.d_to_ptr("ARG")

        # LCL = *(endFrame-4)
        buffer += "@R15\n"
        buffer += "AM=M-1\n"
        buffer += "D=M\n"
        buffer += asm.d_to_ptr("LCL")

        # goto return address
        buffer += "@R14\n"
        buffer += "A=M\n"
        buffer += "0;JMP\n"

        self.stream.write(buffer)
        self.currentFunction = ""

    def write_init(self):
        buffer = f"// init\n"
        self.stream.write(buffer)

    def close(self):
        self.stream.close()
