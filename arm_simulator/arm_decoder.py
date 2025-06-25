import struct

class ARMInstruction:
    def __init__(self, binary_word):
        self.binary_word = binary_word
        self.instruction_type = None
        self.opcode = None
        self.operands = {}
        self.condition_code = None
        self.set_flags = False

    def decode(self):
        self.condition_code = (self.binary_word >> 28) & 0xF

        # Check for Multiply (MUL) instruction first as it has a distinct pattern
        # Format: Cond(4) 0000 00A S Rd Rs 1001 Rm
        # Bits 27-24 are 0000, bits 7-4 are 1001
        if ((self.binary_word >> 24) & 0xF) == 0b0000 and ((self.binary_word >> 4) & 0xF) == 0b1001:
            self.instruction_type = 'MUL'
            self.set_flags = bool((self.binary_word >> 20) & 0x1)
            self.rd = (self.binary_word >> 16) & 0xF
            self.rm = self.binary_word & 0xF
            self.rs = (self.binary_word >> 8) & 0xF
            self.operands = {'rd': self.rd, 'rm': self.rm, 'rs': self.rs}
            return

        # Check for Data Processing Instructions (including MOV, ADD, SUB, AND, ORR, CMP, TST, TEQ, CMN)
        # Format: Cond(4) 00 I Opcode S Rn Rd Operand2
        # Bits 27-26 are 00
        if ((self.binary_word >> 26) & 0b11) == 0b00:
            self.set_flags = bool((self.binary_word >> 20) & 0x1)
            self.opcode = (self.binary_word >> 21) & 0xF
            self.rn = (self.binary_word >> 16) & 0xF
            self.rd = (self.binary_word >> 12) & 0xF

            # Check I bit (bit 25) for immediate vs register operand
            if (self.binary_word >> 25) & 0x1: # Immediate operand
                # Immediate value is 8-bit immediate rotated right by 2 * rotate_imm
                rotate_imm = (self.binary_word >> 8) & 0xF
                imm8 = self.binary_word & 0xFF
                # Perform ROR on imm8 by 2 * rotate_imm
                self.operand2 = (imm8 >> (2 * rotate_imm)) | (imm8 << (32 - (2 * rotate_imm))) & 0xFFFFFFFF
                self.operands = {'rd': self.rd, 'rn': self.rn, 'operand2': self.operand2}

                # Map opcodes to instruction types for Data Processing Immediate
                if self.opcode == 0b0100: # ADD
                    self.instruction_type = 'ADD'
                elif self.opcode == 0b0010: # SUB
                    self.instruction_type = 'SUB'
                elif self.opcode == 0b1101: # MOV
                    self.instruction_type = 'MOV'
                elif self.opcode == 0b1010: # CMP (always sets flags)
                    self.instruction_type = 'CMP'
                    self.set_flags = True
                elif self.opcode == 0b0000: # AND
                    self.instruction_type = 'AND'
                elif self.opcode == 0b1100: # ORR
                    self.instruction_type = 'ORR'
                else:
                    self.instruction_type = 'UNKNOWN_DATA_PROCESSING_IMM'

            else: # Register operand (shifted register)
                self.rm = self.binary_word & 0xF
                shift_type_bits = (self.binary_word >> 5) & 0b11
                
                # Check bit 4 for immediate shift (0) or register shift (1)
                if not ((self.binary_word >> 4) & 0x1): # Immediate shift amount
                    shift_amount = (self.binary_word >> 7) & 0b11111
                    
                    # Special case for ROR #Imm: MOV Rd, Rm, ROR #Imm where Rm is Rd
                    # This is how `ROR Rd, #Imm` is encoded.
                    if self.opcode == 0b1101 and shift_type_bits == 0b11 and self.rn == 0 and self.rm == self.rd:
                        self.instruction_type = 'ROR'
                        self.operands = {'rd': self.rd, 'rm': self.rm, 'shift_amount': shift_amount, 'shift_type': shift_type_bits, 'rn': 0}
                        return

                    # Check for standalone shift instructions (Rn is R0, opcode is MOV)
                    # This is a special case where MOV Rd, Rm, Shift #Imm is a shift instruction
                    if self.rn == 0 and self.opcode == 0b1101: # MOV
                        if shift_type_bits == 0b00: # LSL
                            self.instruction_type = 'LSL'
                        elif shift_type_bits == 0b01: # LSR
                            self.instruction_type = 'LSR'
                        elif shift_type_bits == 0b10: # ASR
                            self.instruction_type = 'ASR'
                        elif shift_type_bits == 0b11: # ROR
                            self.instruction_type = 'ROR'
                        self.operands = {'rd': self.rd, 'rm': self.rm, 'shift_amount': shift_amount, 'shift_type': shift_type_bits, 'rn': 0}
                        return

                    # If not a standalone shift, it's a data processing instruction with immediate shift
                    self.operands = {'rd': self.rd, 'rn': self.rn, 'rm': self.rm, 'shift_amount': shift_amount, 'shift_type': shift_type_bits}

                else: # Register-specified shift amount
                    rs = (self.binary_word >> 8) & 0xF
                    
                    # Check for standalone shift instructions (Rn is R0, opcode is MOV)
                    # This is a special case where MOV Rd, Rm, Shift Rs is a shift instruction
                    if self.rn == 0 and self.opcode == 0b1101: # MOV
                        if shift_type_bits == 0b00: # LSL
                            self.instruction_type = 'LSL'
                        elif shift_type_bits == 0b01: # LSR
                            self.instruction_type = 'LSR'
                        elif shift_type_bits == 0b10: # ASR
                            self.instruction_type = 'ASR'
                        elif shift_type_bits == 0b11: # ROR
                            self.instruction_type = 'ROR'
                        self.operands = {'rd': self.rd, 'rm': self.rm, 'rs': rs, 'shift_type': shift_type_bits, 'rn': 0}
                        return

                    # If not a standalone shift, it's a data processing instruction with register shift
                    self.operands = {'rd': self.rd, 'rn': self.rn, 'rm': self.rm, 'rs': rs, 'shift_type': shift_type_bits}

                # Map opcodes to instruction types for Data Processing Register
                if self.opcode == 0b0100: # ADD
                    self.instruction_type = 'ADD'
                elif self.opcode == 0b0010: # SUB
                    self.instruction_type = 'SUB'
                elif self.opcode == 0b1101: # MOV
                    self.instruction_type = 'MOV'
                elif self.opcode == 0b1010: # CMP (always sets flags)
                    self.instruction_type = 'CMP'
                    self.set_flags = True
                elif self.opcode == 0b0000: # AND
                    self.instruction_type = 'AND'
                elif self.opcode == 0b1100: # ORR
                    self.instruction_type = 'ORR'
                else:
                    self.instruction_type = 'UNKNOWN_DATA_PROCESSING_REG'

            # Handle conditional instructions (SUBNE, ADDEQ) - these override the base instruction type
            if self.condition_code == 0b0001 and self.instruction_type == 'SUB': # NE
                self.instruction_type = 'SUBNE'
            elif self.condition_code == 0b0000 and self.instruction_type == 'ADD': # EQ
                self.instruction_type = 'ADDEQ'
            return

        # Load/Store Word/Byte (LDR, STR)
        # Format: Cond(4) 01 I P U B W L Rn Rd Offset
        # Bits 27-26 are 01
        if ((self.binary_word >> 26) & 0b11) == 0b01:
            self.l_bit = (self.binary_word >> 20) & 0x1 # 1 for LDR, 0 for STR
            self.rn = (self.binary_word >> 16) & 0xF
            self.rd = (self.binary_word >> 12) & 0xF
            self.offset = self.binary_word & 0xFFF

            if self.l_bit == 1:
                self.instruction_type = 'LDR'
            else:
                self.instruction_type = 'STR'
            self.operands = {'rd': self.rd, 'rn': self.rn, 'offset': self.offset}
            return

        # Branch (B, BL)
        # Format: Cond(4) 101 L Offset
        # Bits 27-25 are 101
        if ((self.binary_word >> 25) & 0b111) == 0b101:
            self.l_bit = (self.binary_word >> 24) & 0x1
            self.offset = self.binary_word & 0xFFFFFF # 24-bit offset

            if self.l_bit == 1:
                self.instruction_type = 'BL'
            else:
                self.instruction_type = 'B'
            self.operands = {'offset': self.offset}
            return

        self.instruction_type = 'UNKNOWN'

    def __str__(self):
        if self.instruction_type == 'UNKNOWN':
            return f"UNKNOWN Instruction: {self.binary_word:08X}"
        elif self.instruction_type.startswith('UNKNOWN'):
            return f"{self.instruction_type} Instruction: {self.binary_word:08X}"
        else:
            operand_str = ', '.join([f'{k}: {v}' for k, v in self.operands.items()])
            return f"Type: {self.instruction_type}, Cond: {self.condition_code:X}, Set Flags: {self.set_flags}, Operands: {{{operand_str}}}"

def decode_instructions(binary_data):
    instructions = []
    for i in range(0, len(binary_data), 4):
        word_bytes = binary_data[i:i+4]
        if len(word_bytes) == 4:
            binary_word = struct.unpack('>I', word_bytes)[0]
            instruction = ARMInstruction(binary_word)
            instruction.decode()
            instructions.append(instruction)
    return instructions

class ThumbInstruction(ARMInstruction):
    def __init__(self, binary_word):
        super().__init__(binary_word)
        self.binary_word = binary_word & 0xFFFF

    def decode(self):
        self.instruction_type = 'UNKNOWN_THUMB'
        self.operands = {'binary_word': self.binary_word}


    def __str__(self):
        return f"Type: {self.instruction_type}, Operands: {self.operands}"


