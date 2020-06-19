INT_MAX = 65535
ADDR_MAX = 32767 # also signed max
RAM_MAX = 16383
KBD = 24576

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

def valToD(val):
    if val < 0 or val > ADDR_MAX:
        raise ValueError(f"expected value between 0 and {ADDR_MAX}")
    buffer = f"@{val}\n"
    buffer += "D=A\n"
    return buffer

def pushAddr(segment):
    if segment in SEGMENTS.values():
        buffer = f"@{segment}\n"
        buffer += "D=M\n"
        buffer += PUSH_D
        return buffer
    print(f"Error: invalid segment '{segment}'\n")
    return f"// invalid segment '{segment}'\n"

# A instruction: constant, label, or variable
def load(a):
    return f"@{a}\n"

def DToPtr(ptr):
    buffer = load(ptr)
    buffer += "M=D\n"
    return buffer

def ptrToD(ptr):
    buffer = load(ptr)
    buffer += "D=M\n"
    return buffer
