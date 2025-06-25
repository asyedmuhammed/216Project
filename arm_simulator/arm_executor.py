import struct

class ARMCpu:
    def __init__(self):
        self.registers = [0] * 16  # R0-R15, R15 is PC
        self.cpsr = {
            'N': 0,  # Negative
            'Z': 0,  # Zero
            'C': 0,  # Carry
            'V': 0   # Overflow
        }
        self.memory = bytearray(1024)  # 1KB of memory for now

    def _update_flags(self, result, op1=None, op2=None, carry_out=None, overflow=None):
        # Ensure result is treated as a 32-bit unsigned integer for N and Z flags
        result_32bit = result & 0xFFFFFFFF
        self.cpsr['N'] = 1 if (result_32bit >> 31) & 0x1 else 0  # Check MSB for negative
        self.cpsr['Z'] = 1 if result_32bit == 0 else 0
        if carry_out is not None:
            self.cpsr['C'] = 1 if carry_out else 0
        if overflow is not None:
            self.cpsr['V'] = 1 if overflow else 0

    def _get_operand2(self, instruction):
        if 'operand2' in instruction.operands: # Immediate operand
            return instruction.operands['operand2']
        elif 'rm' in instruction.operands: # Register operand (possibly shifted)
            rm_value = self.registers[instruction.operands['rm']]
            
            shift_type = instruction.operands.get('shift_type')
            shift_amount = instruction.operands.get('shift_amount')
            rs = instruction.operands.get('rs')

            if shift_type is not None:
                if shift_amount is not None: # Immediate shift amount
                    actual_shift_amount = shift_amount
                elif rs is not None: # Register-specified shift amount
                    actual_shift_amount = self.registers[rs]
                else:
                    actual_shift_amount = 0 # No shift amount specified, default to 0

                # Ensure shift amount is within 0-31 for 32-bit registers
                actual_shift_amount &= 0x1F

                if shift_type == 0b00: # LSL
                    return rm_value << actual_shift_amount
                elif shift_type == 0b01: # LSR
                    return rm_value >> actual_shift_amount
                elif shift_type == 0b10: # ASR
                    # ASR preserves the sign bit
                    # Python's >> operator for negative numbers performs arithmetic shift right
                    # For positive numbers, it's logical shift right
                    # So, we need to handle this carefully for 32-bit signed integers
                    if rm_value & 0x80000000: # If MSB is 1 (negative number)
                        # Convert to signed 32-bit for ASR
                        signed_rm_value = struct.unpack('<i', struct.pack('<I', rm_value & 0xFFFFFFFF))[0]
                        return (signed_rm_value >> actual_shift_amount) & 0xFFFFFFFF
                    else:
                        return rm_value >> actual_shift_amount
                elif shift_type == 0b11: # ROR
                    # ROR: (value >> shift) | (value << (32 - shift))
                    # The result should be masked to 32 bits
                    return ((rm_value >> actual_shift_amount) | (rm_value << (32 - actual_shift_amount))) & 0xFFFFFFFF
                else:
                    return rm_value # Should not happen if shift_type is correctly decoded
            else:
                return rm_value # No shift specified, just return register value
        else:
            return 0 # Default or error case

    def execute_instruction(self, instruction):
        # Condition check (simplified: only checks Z flag for EQ/NE)
        execute_conditionally = True
        if instruction.condition_code == 0b0001: # NE
            if self.cpsr['Z'] == 1:
                execute_conditionally = False
        elif instruction.condition_code == 0b0000: # EQ
            if self.cpsr['Z'] == 0:
                execute_conditionally = False

        if not execute_conditionally:
            print(f"Instruction {instruction.instruction_type} skipped due to condition.")
            return

        if instruction.instruction_type == 'MOV':
            rd = instruction.operands['rd']
            operand2 = self._get_operand2(instruction)
            self.registers[rd] = operand2 & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                self._update_flags(operand2)
        elif instruction.instruction_type == 'LDR':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            offset = instruction.operands['offset']
            address = self.registers[rn] + offset
            if 0 <= address < len(self.memory) - 3:
                value = struct.unpack('<I', self.memory[address:address+4])[0]
                self.registers[rd] = value
            else:
                print(f"Memory access out of bounds for LDR at address {address}")
        elif instruction.instruction_type == 'STR':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            offset = instruction.operands['offset']
            address = self.registers[rn] + offset
            value = self.registers[rd]
            if 0 <= address < len(self.memory) - 3:
                self.memory[address:address+4] = struct.pack('<I', value)
            else:
                print(f"Memory access out of bounds for STR at address {address}")
        elif instruction.instruction_type == 'ADD':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2 = self._get_operand2(instruction)
            val_rn = self.registers[rn]
            result = val_rn + operand2
            self.registers[rd] = result & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                # Carry out for addition: if result > 2^32 - 1
                carry_out = (result > 0xFFFFFFFF)
                # Overflow for addition: (Rn_sign == Op2_sign) and (Rn_sign != Result_sign)
                # Sign bit is MSB (bit 31)
                rn_sign = (val_rn >> 31) & 0x1
                op2_sign = (operand2 >> 31) & 0x1
                result_sign = (result >> 31) & 0x1
                overflow = (rn_sign == op2_sign) and (rn_sign != result_sign)
                self._update_flags(result, carry_out=carry_out, overflow=overflow)
        elif instruction.instruction_type == 'SUB':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2 = self._get_operand2(instruction)
            val_rn = self.registers[rn]
            result = val_rn - operand2
            self.registers[rd] = result & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                # Carry out for subtraction: if no borrow (Rn >= Op2)
                carry_out = (val_rn >= operand2)
                # Overflow for subtraction: (Rn_sign != Op2_sign) and (Rn_sign != Result_sign)
                rn_sign = (val_rn >> 31) & 0x1
                op2_sign = (operand2 >> 31) & 0x1
                result_sign = (result >> 31) & 0x1
                overflow = (rn_sign != op2_sign) and (rn_sign != result_sign)
                self._update_flags(result, carry_out=carry_out, overflow=overflow)
        elif instruction.instruction_type == 'MUL':
            rd = instruction.operands['rd']
            rm = instruction.operands['rm']
            rs = instruction.operands['rs']
            result = self.registers[rm] * self.registers[rs]
            self.registers[rd] = result & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                self._update_flags(result)
        elif instruction.instruction_type == 'AND':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2 = self._get_operand2(instruction)
            result = self.registers[rn] & operand2
            self.registers[rd] = result & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                self._update_flags(result)
        elif instruction.instruction_type == 'ORR':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2 = self._get_operand2(instruction)
            result = self.registers[rn] | operand2
            self.registers[rd] = result & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                self._update_flags(result)
        elif instruction.instruction_type == 'CMP':
            rn = instruction.operands['rn']
            operand2 = self._get_operand2(instruction)
            val_rn = self.registers[rn]
            result = val_rn - operand2
            # Carry out for subtraction: if no borrow (Rn >= Op2)
            carry_out = (val_rn >= operand2)
            # Overflow for subtraction: (Rn_sign != Op2_sign) and (Rn_sign != Result_sign)
            rn_sign = (val_rn >> 31) & 0x1
            op2_sign = (operand2 >> 31) & 0x1
            result_sign = (result >> 31) & 0x1
            overflow = (rn_sign != op2_sign) and (rn_sign != result_sign)
            self._update_flags(result, carry_out=carry_out, overflow=overflow)
        elif instruction.instruction_type == 'SUBNE':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2 = self._get_operand2(instruction)
            val_rn = self.registers[rn]
            result = val_rn - operand2
            self.registers[rd] = result & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                carry_out = (val_rn >= operand2)
                rn_sign = (val_rn >> 31) & 0x1
                op2_sign = (operand2 >> 31) & 0x1
                result_sign = (result >> 31) & 0x1
                overflow = (rn_sign != op2_sign) and (rn_sign != result_sign)
                self._update_flags(result, carry_out=carry_out, overflow=overflow)
        elif instruction.instruction_type == 'ADDEQ':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2 = self._get_operand2(instruction)
            val_rn = self.registers[rn]
            result = val_rn + operand2
            self.registers[rd] = result & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                carry_out = (result > 0xFFFFFFFF)
                rn_sign = (val_rn >> 31) & 0x1
                op2_sign = (operand2 >> 31) & 0x1
                result_sign = (result >> 31) & 0x1
                overflow = (rn_sign == op2_sign) and (rn_sign != result_sign)
                self._update_flags(result, carry_out=carry_out, overflow=overflow)
        elif instruction.instruction_type == 'LSL':
            rd = instruction.operands['rd']
            shifted_value = self._get_operand2(instruction)
            self.registers[rd] = shifted_value & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                self._update_flags(shifted_value)
        elif instruction.instruction_type == 'LSR':
            rd = instruction.operands['rd']
            shifted_value = self._get_operand2(instruction)
            self.registers[rd] = shifted_value & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                self._update_flags(shifted_value)
        elif instruction.instruction_type == 'ASR':
            rd = instruction.operands['rd']
            shifted_value = self._get_operand2(instruction)
            self.registers[rd] = shifted_value & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                self._update_flags(shifted_value)
        elif instruction.instruction_type == 'ROR':
            rd = instruction.operands['rd']
            shifted_value = self._get_operand2(instruction)
            self.registers[rd] = shifted_value & 0xFFFFFFFF # Mask to 32 bits
            if instruction.set_flags:
                self._update_flags(shifted_value)
        elif instruction.instruction_type == 'B' or instruction.instruction_type == 'BL':
            print(f"Branch instruction {instruction.instruction_type} with offset {instruction.operands['offset']}")
        else:
            print(f"Unknown instruction type for execution: {instruction.instruction_type}")

    def __str__(self):
        reg_str = ", ".join([f"R{i}: {self.registers[i]:08X}" for i in range(16)])
        cpsr_str = ", ".join([f"{k}: {v}" for k, v in self.cpsr.items()])
        return f"Registers: {reg_str}\nCPSR: {cpsr_str}"


