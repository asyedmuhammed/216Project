.org 0x00          // Start at memory location 00
.text              // Code section
.global _start
_start:

LDR r0, =0x10000   // Instruction #1: Load immediate (replaces MOV)
LDR r1, =0x100     // Instruction #2: LDR (Load Data)
LDR r2, [r1]       
STR r2, [r1]       // Instruction #3: STR (Store Data)
ADD r3, r1, r2     // Instruction #4: ADD (Addition)
SUB r4, r2, r3     // Instruction #5: SUB (Subtraction)
MUL r5, r1, r4     // Instruction #6: MUL (Multiplication)
SUB r5, r4, r5     
CMP r0, r5         // Instruction #7: CMP (Compare)
AND r6, r0, r5     // Instruction #8: AND (AND Logic Gate)
ORR r7, r0, r5     // Instruction #9: ORR (OR Logic Gate)
SUBNE r0, r0, r5   // Instruction #10: NE (Not Equal)
CMP r7, r8         
ADDEQ r6, r7, r8   // Instruction #11: EQ (Equal)
LSL r1, r0, #2     // Instruction #12: LSL (Logical Shift Left)
LSR r2, r0, #2     // Instruction #13: LSR (Logical Shift Right)
ASR r4, r1, #4     // Instruction #14: ASR (Arithmetic Shift Right)
ROR r0, #2         // Instruction #15: ROR (Rotate Right)

_stop:
b _stop

.end
