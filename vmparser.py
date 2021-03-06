from commandtype import CommandType


def is_command(line):
    return not line.startswith('//')


class Parser:
    def __init__(self, file_in):
        self.fileIn = file_in
        self.stream = open(file_in, 'r')

        self.currentCommand = ''
        self.nextCommand = ''
        self.advance()

    def has_more_commands(self):
        return self.nextCommand != ''

    def advance(self):
        self.currentCommand = self.nextCommand
        while True:
            line = self.stream.readline()
            if line == '':
                self.nextCommand = ''
                break
            if is_command(line):
                comment_start = line.find("//")
                if comment_start != -1:
                    line = line[:comment_start]
                if line.endswith('\n'):
                    line = line[:-1]
                if line.endswith('\r'):
                    line = line[:-1]
                if len(line) == 0:
                    continue
                self.nextCommand = " ".join(line.split())
                break
        return self.currentCommand

    def close(self):
        self.stream.close()

    def command_type(self):
        split = self.currentCommand.split()  # splits based on whitespace
        numTokens = len(split)
        if numTokens == 0:
            print("no tokens for command_type to operate on")
            return CommandType.INVALID_COMMAND

        first = split[0]
        commandFirst = {CommandType.C_ARITHMETIC: {"add", "sub", "neg", "eq", "lt", "gt", "and", "or", "not"},
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
        ctype = self.command_type()
        index = 1
        if ctype == CommandType.C_ARITHMETIC:
            index = 0
        split = self.currentCommand.split()
        if len(split) < index + 1:
            return None
        return split[index]

    def arg2(self):
        split = self.currentCommand.split()
        if len(split) < 3:
            return None
        return split[2]
