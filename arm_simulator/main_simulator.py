import struct
from arm_decoder import decode_instructions, ARMInstruction, ThumbInstruction
from arm_executor import ARMCpu

def run_simulation(binary_file_path):
    cpu = ARMCpu()
    
    # Initialize some registers for testing purposes
    cpu.registers[0] = 0x10
    cpu.registers[1] = 0x20
    cpu.registers[2] = 0x05
    cpu.registers[3] = 0x02
    cpu.registers[4] = 0x0A
    cpu.registers[5] = 0x03
    cpu.registers[7] = 0x0F # For ADDEQ test
    cpu.registers[8] = 0x0F # For ADDEQ test

    print("--- Initial CPU State ---")
    print(cpu)
    print("-------------------------")

    try:
        with open(binary_file_path, "rb") as f:
            binary_data = f.read()
    except FileNotFoundError:
        print(f"Error: Binary file not found at {binary_file_path}")
        return

    instructions = decode_instructions(binary_data)

    for i, instruction in enumerate(instructions):
        print(f"\n--- Executing Instruction {i+1} ---")
        print(f"Decoded: {instruction}")
        cpu.execute_instruction(instruction)
        print("--- CPU State After Execution ---")
        print(cpu)
        print("---------------------------------")

if __name__ == "__main__":
    run_simulation("test_instructions.bin")



