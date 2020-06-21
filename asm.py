INT_MAX = 65535
ADDRESS_MAX = 32767  # also signed max
RAM_MAX = 16383
KBD = 24576

SEGMENTS = {"local": "LCL",
            "argument": "ARG",
            "this": "THIS",
            "that": "THAT"}

POINTER = {0: "THIS", 1: "THAT"}
TEMP_BASE = 5

LOAD_SP = "@SP\n" + "A=M\n"
LOAD_TOP = "@SP\n" + "A=M-1\n"

LOAD_LCL = "@LCL\n" + "A=M\n"

INC_SP = "@SP\n" + "M=M+1\n"
PUSH_D = LOAD_SP + "M=D\n" + INC_SP

DEC_DEREF = "AM=M-1\n"
POP = "@SP\n" + DEC_DEREF
POP_D = POP + "D=M\n"  # post: address in A is where top used to be


# A instruction: constant, label, or variable
def load(a):
    return f"@{a}\n"

# could implement up to INT_MAX with an add
# could also allow negative numbers by adding them to INT_MAX
#   up to -(ADDRESS_MAX+1)
def val_to_d(val):
    if val < 0 or val > ADDRESS_MAX:
        raise ValueError(f"expected value between 0 and {ADDRESS_MAX}")
    buffer = f"@{val}\n"
    buffer += "D=A\n"
    return buffer

def d_to_ptr(ptr):
    buffer = load(ptr)
    buffer += "M=D\n"
    return buffer

def val_to_ptr(val, ptr):
    buffer = val_to_d(val)
    buffer += d_to_ptr(ptr)
    return buffer

def ptr_to_d(ptr):
    buffer = load(ptr)
    buffer += "D=M\n"
    return buffer

def push_address(segment):
    if segment in SEGMENTS.values():
        buffer = f"@{segment}\n"
        buffer += "D=M\n"
        buffer += PUSH_D
        return buffer
    print(f"Error: invalid segment '{segment}'\n")
    return f"// invalid segment '{segment}'\n"







