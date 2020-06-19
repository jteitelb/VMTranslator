import os
from sys import argv

from commandtype import CommandType
from vmparser import Parser
from codewriter import CodeWriter


def main():
    # argv = ["VMTranslator", "test.vm"]
    argc = len(argv)
    if argc != 2:
        print("Usage: %s <File or Directory>" % argv[0])
        return
    
    input_arg = argv[1]
    
    if os.path.isfile(input_arg):
        if not argv[1].endswith(".vm"):
            print("Error: Expected .vm file!")
            return
        out_file = input_arg[:-2] + "asm"
    elif os.path.isdir(input_arg):
        print("Directory Found!")
        vmFiles = [os.path.join(input_arg, file) for file in os.listdir(input_arg) if file.endswith(".vm")]
        if len(vmFiles) < 1:
            print("No vm files found in", input_arg)
            return
        print(len(vmFiles), "vm file(s) found.")
        return
    else:
        print(f"Error: no file or directory found named \"{input_arg}\"")
        return

# create parser and writer

    parser = Parser(input_arg)
    print(f"parsing from '{input_arg}'...")
    writer = CodeWriter(out_file)
    print(f"writing to '{out_file}'...")
    while parser.hasMoreCommands():
        parser.advance()
        comType = parser.commandType()
        current = parser.currentCommand

        # this is ugly. Alternatives?
        #   -some kind of map / dict
        #   -CommandType abstract class with writeCommand method?
        #       -writeCommand belongs in CodeWriter

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
