import os
from sys import argv

from asm import ASM
from commandtype import CommandType
from vmparser import Parser
from codewriter import CodeWriter

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

