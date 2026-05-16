# În tvm.py, adăugăm o clasă pentru accelerator

import mmap
import os

class ParadoxAccelerator:
    def __init__(self, mem_base=0x43C00000, mem_size=0x10000):
        self.mem_fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self.mem = mmap.mmap(self.mem_fd, mem_size, 
                             offset=mem_base, 
                             prot=mmap.PROT_READ | mmap.PROT_WRITE)
        
    def write_reg(self, offset, value):
        self.mem[offset:offset+4] = value.to_bytes(4, 'little')
        
    def read_reg(self, offset):
        return int.from_bytes(self.mem[offset:offset+4], 'little')
    
    def generate_paradox(self, seed, length=3):
        self.write_reg(0x10, length)
        self.write_reg(0x08, seed)
        self.write_reg(0x00, 0x01)  # start generate
        while not (self.read_reg(0x04) & 0x02):  # wait for done
            pass
        return self.read_reg(0x0C)
    
    def verify_paradox(self, challenge, response):
        self.write_reg(0x0C, response)
        self.write_reg(0x00, 0x03)  # start verify (mode=1)
        while not (self.read_reg(0x04) & 0x02):
            pass
        return bool(self.read_reg(0x04) & 0x04)  # valid bit