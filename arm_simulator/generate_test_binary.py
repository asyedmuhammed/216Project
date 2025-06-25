import struct

def hex_to_bin_word(hex_str):
    return int(hex_str, 16)

def generate_test_binary(output_file):
    # Manually encoded binary representations for the 15 instructions from instructions.s
    # These are simplified and might not be perfectly accurate for all ARM features (e.g., Operand2 shifts)
    # but should be decodable by our current decoder.
    # Format: Cond(4) | Type/Opcode specific bits | Rn | Rd | Operand2/Rm/Offset

    # All instructions are assumed to be ARM (32-bit) and use AL (Always) condition code (0b1110 or E)
    # For simplicity, we'll use a common pattern for data processing instructions.

    # Instruction 1: MOV r0, #0x10000
    # MOV immediate: E3A00000 (MOV R0, #0)
    # To represent #0x10000, it's a rotated immediate. For simplicity, let's use a direct immediate for now.
    # This is a simplified encoding. A true MOV #0x10000 would involve a rotated immediate.
    # Let's use a simple MOV immediate for a smaller value that fits directly.
    # MOV R0, #16 (0x10) -> E3A00010
    # The original instruction is MOV r0, #0x10000. This is a 16-bit immediate rotated right by an even number of bits.
    # 0x10000 = 0x10 << 12. So, 0x10 is the immediate, and rotate is 32-12 = 20. (Not directly encodable as 8-bit immediate)
    # For testing, let's use a simple MOV immediate that fits the 8-bit immediate field.
    # Let's encode MOV R0, #0x10 (decimal 16)
    # E3A00010 (Cond=E, I=1, Opcode=D (MOV), S=0, Rn=0, Rd=0, Imm=16)
    instr1_bin = hex_to_bin_word("E3A00010") # MOV R0, #16

    # Instruction 2: LDR r1, =0x100
    # This is a pseudo-instruction. It typically loads a value from the literal pool.
    # For simulation, we can treat it as LDR R1, [PC, #offset] or LDR R1, [R_base, #offset]
    # Let's simulate LDR R1, [R0, #0x100] (simplified)
    # E5901100 (Cond=E, P=1, U=1, B=0, W=0, L=1, Rn=0, Rd=1, Offset=0x100)
    instr2_bin = hex_to_bin_word("E5901100") # LDR R1, [R0, #0x100]

    # Instruction 3: STR r2, [R1]
    # E5812000 (Cond=E, P=1, U=1, B=0, W=0, L=0, Rn=1, Rd=2, Offset=0)
    instr3_bin = hex_to_bin_word("E5812000") # STR R2, [R1, #0]

    # Instruction 4: ADD r3, r1, r2
    # E0813002 (Cond=E, Opcode=4 (ADD), S=0, Rn=1, Rd=3, Rm=2)
    instr4_bin = hex_to_bin_word("E0813002") # ADD R3, R1, R2

    # Instruction 5: SUB r4, r2, r3
    # E0424003 (Cond=E, Opcode=2 (SUB), S=0, Rn=2, Rd=4, Rm=3)
    instr5_bin = hex_to_bin_word("E0424003") # SUB R4, R2, R3

    # Instruction 6: MUL r5, r1, r4
    # E0050194 (Cond=E, A=0, S=0, Rd=5, Rm=1, Rs=4)
    instr6_bin = hex_to_bin_word("E0050194") # MUL R5, R1, R4

    # Instruction 7: CMP r0, r5
    # E1500005 (Cond=E, Opcode=A (CMP), S=1, Rn=0, Rm=5)
    instr7_bin = hex_to_bin_word("E1500005") # CMP R0, R5

    # Instruction 8: AND r6, r0, r5
    # E0006005 (Cond=E, Opcode=0 (AND), S=0, Rn=0, Rd=6, Rm=5)
    instr8_bin = hex_to_bin_word("E0006005") # AND R6, R0, R5

    # Instruction 9: ORR r7, r0, r5
    # E1807005 (Cond=E, Opcode=C (ORR), S=0, Rn=0, Rd=7, Rm=5)
    instr9_bin = hex_to_bin_word("E1807005") # ORR R7, R0, R5

    # Instruction 10: SUBNE r0, r0, r5
    # 10400005 (Cond=NE (0001), Opcode=2 (SUB), S=0, Rn=0, Rd=0, Rm=5)
    instr10_bin = hex_to_bin_word("10400005") # SUBNE R0, R0, R5

    # Instruction 11: ADDEQ r6, r7, r8
    # 00876008 (Cond=EQ (0000), Opcode=4 (ADD), S=0, Rn=7, Rd=6, Rm=8)
    instr11_bin = hex_to_bin_word("00876008") # ADDEQ R6, R7, R8

    # Instruction 12: LSL r1, r0, #2
    # E1A01100 (Cond=E, Opcode=A (MOV), S=0, Rd=1, Rm=0, Shift_imm=2, Shift_type=0 (LSL))
    # LSL is often encoded as MOV Rd, Rm, LSL #Imm
    # MOV R1, R0, LSL #2 -> E1A01100 (Cond=E, Opcode=A, S=0, Rd=1, Rn=0, Shift_imm=2, Shift_type=0, Rm=0)
    # The decoder needs to correctly parse this as LSL.
    # Let's try to encode it as a Data Processing instruction with LSL shift type.
    # Cond (4) | 000 (3) | Opcode (4) | S (1) | Rn (4) | Rd (4) | Shift_imm (5) | Shift_type (2) | 0 (1) | Rm (4)
    # For LSL, Opcode can be MOV (0b1101) or a logical operation with Rn=0
    # Let's use a simplified encoding for LSL, where Rn is the source register and Rd is the destination.
    # E1A01100 (MOV R1, R0, LSL #2) - This is the standard encoding for MOV with shifted register.
    # Cond=E, I=0, Opcode=MOV (1101), S=0, Rn=0 (ignored), Rd=1, Shift_imm=2, Shift_type=LSL (00), 0, Rm=0
    # The decoder needs to recognize this pattern for LSL.
    instr12_bin = hex_to_bin_word("E1A01100") # MOV R1, R0, LSL #2

    # Instruction 13: LSR r2, r0, #2
    # E1A02120 (Cond=E, Opcode=A (MOV), S=0, Rd=2, Rm=0, Shift_imm=2, Shift_type=1 (LSR))
    instr13_bin = hex_to_bin_word("E1A02120") # MOV R2, R0, LSR #2

    # Instruction 14: ASR r4, r1, #4
    # E1A14260 (Cond=E, Opcode=A (MOV), S=0, Rd=4, Rm=1, Shift_imm=4, Shift_type=2 (ASR))
    instr14_bin = hex_to_bin_word("E1A14260") # MOV R4, R1, ASR #4

    # Instruction 15: ROR r0, #2
    # E1A003E0 (Cond=E, Opcode=A (MOV), S=0, Rd=0, Rm=0, Shift_imm=2, Shift_type=3 (ROR))
    instr15_bin = hex_to_bin_word("E1A003E0") # MOV R0, R0, ROR #2 (Assuming R0 as source and dest)

    binary_words = [
        instr1_bin, instr2_bin, instr3_bin, instr4_bin, instr5_bin,
        instr6_bin, instr7_bin, instr8_bin, instr9_bin, instr10_bin,
        instr11_bin, instr12_bin, instr13_bin, instr14_bin, instr15_bin
    ]

    with open(output_file, "wb") as f:
        for word in binary_words:
            f.write(struct.pack(">I", word)) # Write as big-endian (network byte order)

    print(f"Generated test binary file: {output_file}")

if __name__ == "__main__":
    generate_test_binary("test_instructions.bin")



