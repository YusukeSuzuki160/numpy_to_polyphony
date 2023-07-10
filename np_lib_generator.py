import os
import re
import math

class NpLibGenerator: # run at the super directory of polyphony-numpy
    def __init__(self, func_dict):
        self.func_dict = func_dict
        self.import_stm = 'from polyphony.typing import int8, int16, int32, int64, uint8, uint16, uint32, uint64, float16, float32, float64, complex64, complex128, bool_, List, Tuple\nfrom polyphony.timing import clkfence\n\n\n'
        self.func_list = []
        self.code = ''
        self.lib_name = '_numpy.py'
        self.lib_path = 'polyphony-numpy/polyphony/_internal/'
        self.exec_command = 'pip install polyphony-numpy/'
        self.precision = 16

    def generate(self):
        self.generate_import()
        for func_name, func in self.func_dict.items():
            if func_name == 'main':
                continue
            elif func_name == 'array':
                self.generate_array(func)
            elif func_name == 'fft':
                self.generate_fft(func)
            elif func_name == 'array_equal':
                self.generate_array_equal(func)
            elif func_name == 'matmult':
                self.generate_matmult(func)
            elif 'print' in func_name:
                self.generate_print(func)
            elif re.search('fixed', func_name):
                func_type = func_name.split('_')[1]
                self.generate_fixed(func, func_type)
            elif re.search('complex', func_name):
                func_type = func_name.split('_')[1]
                self.generate_complex(func, func_type)
        with open(self.lib_path + self.lib_name, 'w') as f:
            f.write(self.code)
        os.system(self.exec_command)

    def generate_import(self):
        self.code += self.import_stm
    
    def generate_array(self, func):
        arg_list = ''
        shape = func['shape']
        length = shape[0] * shape[1]
        dtype = func['dtype']
        for i in range(length):
            arg_list += 'a_' + str(i) + ', '
        return_stm = 'return ' + arg_list
        return_type = 'Tuple['
        for i in range(length):
            return_type += dtype + ', '
        return_type = return_type[:-2] + ']'
        function_name = 'array' + '_' + str(length) + '_' + dtype
        func_str = 'def ' + function_name + '(' + arg_list + ') -> ' + return_type + ':\n'
        func_str += '\t' + return_stm
        self.func_list.append(function_name)
        self.code += func_str + '\n\n\n'

    def generate_fft(self, func):
        arg_list = ''
        shape = func['shape']
        length = shape[0] * shape[1]
        dtype = func['dtype']
        for i in range(length):
            arg_list += 'a_' + str(i) + ', '
        return_stm = 'return ' + arg_list
        return_type = 'Tuple['
        for i in range(length):
            return_type += dtype + ', '
        return_type = return_type[:-2] + ']'
        function_name = 'fft' + '_' + str(length) + '_' + dtype
        func_str = 'def ' + function_name + '(' + arg_list + ') -> ' + return_type + ':\n'
        w_real = []
        w_imag = []
        for i in range(length):
            w_real.append(self.fixed_to_int(math.cos(2 * math.pi * i / length)))
            w_imag.append(self.fixed_to_int(math.sin(2 * math.pi * i / length)))
        stage = int(math.log(shape[1], 2))
        dataset_num = shape[0]
        func_str += '\t' + return_stm
        self.func_list.append(function_name)
        self.code += func_str + '\n\n\n'

    def generate_array_equal(self, func):
        arg_list = ''
        shape = func['shape']
        length = shape[0] * shape[1]
        dtype = func['dtype']
        for i in range(length):
            arg_list += 'a_' + str(i) + ', '
        for i in range(length):
            arg_list += 'b_' + str(i) + ', '
        return_stm = 'return '
        for i in range(length):
            return_stm += 'a_' + str(i) + ' == b_' + str(i) + ' and '
        return_stm = return_stm[:-5]
        return_type = 'bool'
        function_name = 'array_equal' + '_' + str(length) + '_' + dtype
        func_str = 'def ' + function_name + '(' + arg_list + ') -> ' + return_type + ':\n'
        func_str += '\t' + return_stm
        self.func_list.append(function_name)
        self.code += func_str + '\n\n\n'
    
    def generate_matmult(self, func):
        arg_list = ''
        left_shape = func['shape1']
        right_shape = func['shape2']
        dtype = func['dtype']
        return_shape = (left_shape[0], right_shape[1])
        length = return_shape[0] * return_shape[1]
        for i in range(length):
            arg_list += 'a_' + str(i) + ', '
        for i in range(length):
            arg_list += 'b_' + str(i) + ', '
        return_args = ''
        return_type = 'Tuple['
        for i in range(length):
            return_args += 'c_' + str(i) + ', '
            return_type += dtype + ', '
        return_stm = 'return ' + return_args
        shapes = '_' + 'l' + str(left_shape[0]) + '_' + str(left_shape[1]) + '_' + 'r' + str(right_shape[0]) + '_' + str(right_shape[1])
        func_name = 'matmult' + shapes + '_' + dtype
        func_str = 'def ' + func_name + '(' + arg_list + ') -> ' + return_type[:-2] + ']:\n'
        for i in range(return_shape[0] * return_shape[1]):
            func_str += '\tc_' + str(i) + ' = 0\n'
        count = 0
        for i in range(return_shape[0]):
            for j in range(return_shape[1]):
                for k in range(left_shape[1]):
                    func_str += '\td_' + str(count) + ' = 0\n'
                    count += 1
        count = 0

        func_str += '\tclkfence()\n'
        for i in range(return_shape[0]):
            for j in range(return_shape[1]):
                for k in range(left_shape[1]):
                    func_str += '\td_' + str(count) + ' = a_' + str(i * left_shape[1] + k) + ' * b_' + str(k * right_shape[1] + j) + '\n'
                    count += 1
        count = 0
        func_str += '\tclkfence()\n'
        for i in range(return_shape[0]):
            for j in range(return_shape[1]):
                func_str += '\tc_' + str(i * return_shape[1] + j) + ' = '
                for k in range(left_shape[1]):
                    func_str += 'd_' + str(count) + ' + '
                    count += 1
                func_str = func_str[:-3] + '\n'
        func_str += '\t' + return_stm
        self.func_list.append(func_name)
        self.code += func_str + '\n\n\n'

    def generate_print(self, func):
        if 'shape' in func.keys():
            arg_list = ''
            shape = func['shape']
            length = shape[0] * shape[1]
            dtype = func['dtype']
            for i in range(length):
                arg_list += 'a_' + str(i) + ', '
            func_name = '_print' + '_' + str(length) + '_' + dtype
            func_str = 'def ' + func_name + '(' + arg_list + ') -> None:\n'
            for i in range(length):
                func_str += '\tprint(a_' + str(i) + ')\n'
            self.func_list.append(func_name)
            self.code += func_str + '\n\n\n'
        elif 'complex' in func['dtype']:
            bit = str(int(func['dtype'].split('complex')[1]) // 2)
            int_type = 'int' + bit
            func_name = '_print' + '_' + func['dtype']
            func_str = 'def ' + func_name + '(a_real: ' + int_type + ', a_imag: ' + int_type + ') -> None:\n'
            func_str += '\tprint(a_real)\n\tprint(a_imag)\n'
            self.func_list.append(func_name)
            self.code += func_str + '\n\n\n'

    def generate_fixed(self, func, func_type):
        type = func['dtype']
        functon_name = type + '_' + func_type
        if functon_name in self.func_list:
            return
        if func_type == 'mult':
            self.fixed_mul(type)
        
    def fixed_mul(self, type):
        if type == 'fixed64':
            self.code += 'def fixed64_mult(a: int64, b: int64) -> int64:\n\
    temp = a * b\n\
    # Shift right by precision to bring it back to the correct scale\n\
    return temp >> ' + str(self.precision) + '\n\n\n'
            
    def generate_complex(self, func, func_type):
        type = func['dtype']
        if func_type == 'add':
            func_str = self.complex_add(type)
        elif func_type == 'sub':
            func_str = self.complex_sub(type)
        elif func_type == 'mult':
            func_str = self.complex_mul(type)
    
    def complex_add(self, type):
        if type == 'complex64':
            self.code += 'def complex64_add(a_real: int32, a_imag: int32, b_real: int32, b_imag: int32) -> Tuple[int32, int32]:\n\
    return a_real + b_real, a_imag + b_imag\n\n\n'
        elif type == 'complex128':
            self.code += 'def complex128_add(a_real: int64, a_imag: int64, b_real: int64, b_imag: int64) -> Tuple[int64, int64]:\n\
    return a_real + b_real, a_imag + b_imag\n\n\n'
            
    def complex_sub(self, type):
        if type == 'complex64':
            self.code += 'def complex64_sub(a_real: int32, a_imag: int32, b_real: int32, b_imag: int32) -> Tuple[int32, int32]:\n\
    return a_real - b_real, a_imag - b_imag\n\n\n'
        elif type == 'complex128':
            self.code += 'def complex128_sub(a_real: int64, a_imag: int64, b_real: int64, b_imag: int64) -> Tuple[int64, int64]:\n\
    return a_real - b_real, a_imag - b_imag\n\n\n'
            
    def complex_mul(self, type):
        if type == 'complex64':
            self.code += 'def complex64_mult(a_real: int32, a_imag: int32, b_real: int32, b_imag: int32) -> Tuple[int32, int32]:\n\
    real = (a_real * b_real - a_imag * b_imag) >> ' + str(self.precision) + '\n\
    imag = (a_real * b_imag + a_imag * b_real) >> ' + str(self.precision) + '\n\
    return real, imag\n\n\n'
        elif type == 'complex128':
            self.code += 'def complex128_mult(a_real: int64, a_imag: int64, b_real: int64, b_imag: int64) -> Tuple[int64, int64]:\n\
    real = (a_real * b_real - a_imag * b_imag) >> ' + str(self.precision) + '\n\
    imag = (a_real * b_imag + a_imag * b_real) >> ' + str(self.precision) + '\n\
    return real, imag\n\n\n'
            
    def fixed_to_int(self, number):
        return int(number * (1 << self.precision))
            
            
            