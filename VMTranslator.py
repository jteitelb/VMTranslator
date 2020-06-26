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
        arg_type = "file"
        if not argv[1].endswith(".vm"):
            print("Error: Expected .vm file!")
            return
        vm_files = [input_arg]
        out_file = input_arg[:-2] + "asm"
    elif os.path.isdir(input_arg):
        arg_type = "directory"
        print("Directory Found!")
        vm_files = [file for file in os.listdir(input_arg) if file.endswith(".vm")]
        # os.path.join(input_arg, file)
        out_file = input_arg + ".asm"
        print("vm files:", vm_files)
        print("output file:", out_file)
        if len(vm_files) < 1:
            print("No vm files found in", input_arg)
            return
        print(len(vm_files), "vm file(s) found.\n\n")
    else:
        print(f"Error: no file or directory found named \"{input_arg}\"")
        return


# create parser and writer

    writer = CodeWriter(out_file)
    print(f"writing to '{out_file}'...")
    if arg_type == "directory":
        print("writing init...\n\n")
        writer.write_init()

    for vm_file in vm_files: 
        parser = Parser(os.path.join(input_arg, vm_file))
        print(f"parsing from '{vm_file}'...")
        writer.set_file_name(vm_file[:-3])

        while parser.has_more_commands():
            parser.advance()
            comType = parser.command_type()
            current = parser.currentCommand
            print(current)

            # this is horrible. Alternatives?
            #   -some kind of map / dict
            #   -CommandType abstract class with writeCommand method?
            #       -writeCommand belongs in CodeWriter

            if comType == CommandType.C_ARITHMETIC:
                writer.write_arithmetic(current)
            elif comType in [CommandType.C_PUSH, CommandType.C_POP]:
                writer.write_push_pop(comType, parser.arg1(), int(parser.arg2()))
            elif comType == CommandType.C_LABEL:
                writer.write_label(parser.arg1())
            elif comType == CommandType.C_GOTO:
                writer.write_goto(parser.arg1())
            elif comType == CommandType.C_IF:
                writer.write_if(parser.arg1())
            elif comType == CommandType.C_FUNCTION:
                writer.write_function(parser.arg1(), parser.arg2())
            elif comType == CommandType.C_CALL:
                writer.write_call(parser.arg1(), parser.arg2())
            elif comType == CommandType.C_RETURN:
                writer.write_return()
            else:
                print("Error: unrecognized command:")
                print(parser.currentCommand)
        parser.close()
        print("done parsing and writing", vm_file, end="\n\n")
        
    print("Translation Complete.")
    writer.close()

if __name__ == "__main__":
    main()
