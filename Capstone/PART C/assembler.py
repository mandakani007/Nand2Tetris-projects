import sys
import re
from pathlib import Path

# ==========================================
# 1. PREDEFINED SYMBOL TABLE
# ==========================================

symbols = {}

def initialize_symbols():

    global symbols

    symbols = {
        "SP": 0,
        "LCL": 1,
        "ARG": 2,
        "THIS": 3,
        "THAT": 4,
        "SCREEN": 16384,
        "KBD": 24576
    }

    for i in range(16):
        symbols["R" + str(i)] = i


# ==========================================
# 2. TRANSLATION TABLES
# ==========================================

dest_table = {
    "": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111"
}

comp_table = {
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "M": "1110000",
    "!D": "0001101",
    "!A": "0110001",
    "!M": "1110001",
    "-D": "0001111",
    "-A": "0110011",
    "-M": "1110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "M+1": "1110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "M-1": "1110010",
    "D+A": "0000010",
    "D+M": "1000010",
    "D-A": "0010011",
    "D-M": "1010011",
    "A-D": "0000111",
    "M-D": "1000111",
    "D&A": "0000000",
    "D&M": "1000000",
    "D|A": "0010101",
    "D|M": "1010101"
}

jump_table = {
    "": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111"
}


# ==========================================
# 3. FIRST PASS - LABEL DETECTION
# ==========================================

def first_pass(filename):

    instructions = []
    rom_address = 0

    global custom_symbols

    custom_symbols = {}

    with open(filename, "r") as file:

        for line_number, line in enumerate(file, start=1):

            line = line.split("//")[0].strip()

            if not line:
                continue

            if line.startswith("(") and line.endswith(")"):

                label = line[1:-1].strip()

                if not re.fullmatch(
                    r"[A-Za-z_.$:][A-Za-z0-9_.$:]*", label
                ):
                    raise ValueError(
                        f"Invalid label at line {line_number}"
                    )

                if label in symbols:
                    raise ValueError(
                        f"Duplicate or reserved label: {label}"
                    )

                symbols[label] = rom_address
                custom_symbols[label] = ("LABEL", rom_address)

            else:

                instructions.append((line, line_number))
                rom_address += 1

    return instructions


# ==========================================
# 4. VARIABLE ADDRESS ALLOCATION
# ==========================================

next_ram_address = 16


def allocate_variable(name):

    global next_ram_address

    if name not in symbols:

        if next_ram_address > 16383:
            raise ValueError("Variable RAM address limit exceeded")

        symbols[name] = next_ram_address

        custom_symbols[name] = (
            "VARIABLE",
            next_ram_address
        )

        next_ram_address += 1

    return symbols[name]


# ==========================================
# 5. A-INSTRUCTION TRANSLATION
# ==========================================

def translate_a(instruction):

    value = instruction[1:]

    if not value:
        raise ValueError("Empty A-instruction")

    if value.isdigit():

        address = int(value)

    else:

        if not re.fullmatch(
            r"[A-Za-z_.$:][A-Za-z0-9_.$:]*", value
        ):
            raise ValueError("Invalid symbol: " + value)

        address = allocate_variable(value)

    if address < 0 or address > 32767:
        raise ValueError("Address out of range")

    return format(address, "016b")


# ==========================================
# 6. C-INSTRUCTION TRANSLATION
# ==========================================

def translate_c(instruction):

    jump = ""

    if instruction.count(";") > 1:
        raise ValueError("Invalid C-instruction")

    if ";" in instruction:

        instruction, jump = instruction.split(";", 1)

    dest = ""

    if instruction.count("=") > 1:
        raise ValueError("Invalid C-instruction")

    if "=" in instruction:

        dest, comp = instruction.split("=", 1)

    else:

        comp = instruction

    # Normalize destination order
    if len(set(dest)) != len(dest) or any(
        char not in "ADM" for char in dest
    ):
        raise ValueError("Invalid destination")

    dest = "".join(
        char for char in "ADM" if char in dest
    )

    if dest not in dest_table:
        raise ValueError("Invalid destination")

    if comp not in comp_table:
        raise ValueError("Invalid computation: " + comp)

    if jump not in jump_table:
        raise ValueError("Invalid jump: " + jump)

    return (
        "111"
        + comp_table[comp]
        + dest_table[dest]
        + jump_table[jump]
    )


# ==========================================
# 7. SECOND PASS - MACHINE CODE GENERATION
# ==========================================

def second_pass(instructions):

    machine_code = []

    for instruction, line_number in instructions:

        try:

            instruction = re.sub(r"\s+", "", instruction)

            if instruction.startswith("@"):

                binary = translate_a(instruction)

            else:

                binary = translate_c(instruction)

            machine_code.append(binary)

        except ValueError as error:

            raise ValueError(
                f"Error at line {line_number}: {error}"
            )

    return machine_code


# ==========================================
# 8. SAVE SYMBOL TABLE
# ==========================================

def save_symbols(folder):

    output_file = folder / "symbols.txt"

    with open(output_file, "w") as file:

        file.write("SYMBOL\tTYPE\tADDRESS\n")

        for name, (kind, address) in sorted(
            custom_symbols.items()
        ):

            file.write(
                f"{name}\t{kind}\t{address}\n"
            )

    print("Symbol table saved:", output_file)


# ==========================================
# 9. MAIN ASSEMBLER FUNCTION
# ==========================================

def assemble(filename):

    global next_ram_address
    global custom_symbols

    initialize_symbols()

    next_ram_address = 16
    custom_symbols = {}

    input_path = Path(filename)

    if not input_path.exists():
        raise FileNotFoundError(
            f"File not found: {filename}"
        )

    print("\nStarting assembler...")
    print("Input file:", input_path.name)

    # PASS 1
    instructions = first_pass(input_path)

    print("First pass completed.")
    print("Labels detected:", sum(
        1 for kind, address in custom_symbols.values()
        if kind == "LABEL"
    ))

    # PASS 2
    machine_code = second_pass(instructions)

    print("Second pass completed.")

    # Generate .hack file
    output_path = input_path.with_suffix(".hack")

    with open(output_path, "w") as file:

        for binary in machine_code:

            file.write(binary + "\n")

    # Save symbol table
    save_symbols(input_path.parent)

    print("\nAssembly successful!")
    print("Output:", output_path.name)
    print("Total instructions:", len(machine_code))
    print("Variables allocated:", sum(
        1 for kind, address in custom_symbols.values()
        if kind == "VARIABLE"
    ))


# ==========================================
# 10. PROGRAM EXECUTION
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print("Usage: python3 Assembler.py filename.asm")

    else:

        try:

            assemble(sys.argv[1])

        except (ValueError, FileNotFoundError) as error:

            print("\nAssembler Error:", error)