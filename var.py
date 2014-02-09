#
# PC-BASIC 3.23 - var.py
#
# Variable & array management
# 
# (c) 2013 Rob Hagemans 
#
# This file is released under the GNU GPL version 3. 
# please see text file COPYING for licence terms.
#

import error
import vartypes
import program
from string_ptr import StringPtr


variables = {}
arrays = {}
functions = {}

array_base = 0

# set by COMMON
common_names = []
common_array_names = []

# 'free memory' as reported by FRE
total_mem = 60300    
byte_size = {'$':3, '%':2, '!':4, '#':8}

# memory model
var_mem_start = 4720
var_current = var_mem_start
string_current = var_current + total_mem # 65020
var_memory = {}
# arrays are always kept after all vars
array_current = 0
array_memory = {}

def clear_variables():
    global variables, arrays, array_base, functions, common_names, common_array_names, memory, var_mem, string_mem
    global var_current, string_current, var_memory, array_current, array_memory
    variables = {}
    arrays = {}
    array_base = 0
    functions = {}
    vartypes.deftype = ['!']*26
    # at least I think these should be cleared by CLEAR?
    common_names = []
    common_array_names = []
    # reset memory model
    memory = bytearray('\x00')*(total_mem-program.memory_size())
    var_mem = 0
    string_mem = total_mem
    # memory model
    var_current = var_mem_start
    string_current = var_current + total_mem # 65020
    var_memory = {}
    # arrays are always kept after all vars
    array_current = 0
    array_memory = {}


def set_var(name, value):
    global variables, var_current, var_memory, string_current
    name = vartypes.complete_name(name)
    type_char = name[-1]
    if type_char=='$':
        unpacked = vartypes.pass_string_unpack(value) 
        if len(unpacked)>255:
            # this is a copy if we use bytearray!
            unpacked = unpacked[:255]
        variables[name] = unpacked
    else:
        variables[name] = vartypes.pass_type_keep(name[-1], value)[1]
    # update memory model
    # first two bytes: chars of name or 0 if name is one byte long
    if name not in var_memory:
        name_ptr = var_current
        var_ptr = name_ptr + max(3, len(name)) + 1 # byte_size first_letter second_letter_or_nul remaining_length_or_nul 
        var_current += max(3, len(name)) + 1 + byte_size[name[-1]]
        if type_char=='$':
            string_current -= len(unpacked)
            str_ptr = string_current + 1 
        else:
            str_ptr = -1
        var_memory[name] = (name_ptr, var_ptr, str_ptr)
    elif type_char == '$':
        # every assignment to string leads to new pointer being allocated
        # TODO: string literals in programs have the var ptr point to program space.
        # TODO: if string space expanded to var space, collect garbage
        name_ptr, var_ptr, str_ptr = var_memory[name]
        string_current -= len(unpacked)
        str_ptr = string_current + 1 
        var_memory[name] = (name_ptr, var_ptr, str_ptr)
    
     
def get_var(name):
    name = vartypes.complete_name(name)
    try:
        if name[-1] == '$':
            return vartypes.pack_string(variables[name]) 
        else:
            return (name[-1], variables[name])
    except KeyError:
        return vartypes.null[name[-1]]


def swap_var(name1, name2):
    global variables
    name1 = vartypes.complete_name(name1)
    name2 = vartypes.complete_name(name2)
    if name1[-1] != name2[-1]:
        # type mismatch
        raise error.RunError(13)
    elif name1 not in variables or name2 not in variables:
        # illegal function call
        raise error.RunError(5)
    else:
        val1 = variables[name1] # we need a pointer swap #get_var(name1)
        variables[name1] = variables[name2]
        variables[name2] = val1

def erase_array(name):
    global arrays
    try: 
        del arrays[name]
    except KeyError:
        # illegal fn call
        raise error.RunError(5)    

#######################################

def index_array(index, dimensions):
    bigindex = 0
    area = 1
    for i in range(len(index)):
        # WARNING: dimensions is the *maximum index number*, regardless of array_base!
        bigindex += area*(index[i]-array_base)
        area *= (dimensions[i]+1-array_base)
    return bigindex 

    
def array_len(dimensions):
    return index_array(dimensions, dimensions)+1    

def var_size_bytes(name):
    try:
        return byte_size[name[-1]]  
    except KeyError:
        raise error.RunError(5)

def array_size_bytes(name):
    try:
        [dimensions, lst] = arrays[name]
    except KeyError:
        return 0
    size = array_len(dimensions)
    return size*var_size_bytes(name)     

def dim_array(name, dimensions):
    global arrays, array_memory, var_current, array_current
    name = vartypes.complete_name(name)
    if name in arrays:
        # duplicate definition
        raise error.RunError(10)
    for d in dimensions:
        if d < 0:
            # illegal function call
            raise error.RunError(5)
        elif d < array_base:
            # subscript out of range
            raise error.RunError(9)
    size = array_len(dimensions)
    try:
        if name[-1]=='$':
            arrays[name] = [ dimensions, ['']*size ]  
        else:
            arrays[name] = [ dimensions, bytearray(size*var_size_bytes(name)) ]  
    except OverflowError:
        # out of memory
        raise error.RunError(7) 
    except MemoryError:
        # out of memory
        raise error.RunError(7) 
    # update memory model
    # first two bytes: chars of name or 0 if name is one byte long
    name_ptr = array_current
    record_len = 1 + max(3, len(name)) + 3 + 2*len(dimensions)
    array_ptr = name_ptr + record_len
    array_current += record_len + array_size_bytes(name)
    array_memory[name] = (name_ptr, array_ptr)


def check_dim_array(name, index):
    try:
        [dimensions, lst] = arrays[name]
    except KeyError:
        # auto-dimension - 0..10 or 1..10 
        # this even fixes the dimensions if the index turns out to be out of range!
        dimensions = [ 10 ] * len(index)
        dim_array(name, dimensions)
        [dimensions, lst] = arrays[name]
    if len(index) != len(dimensions):
        raise error.RunError(9)
    for i in range(len(index)):
        if index[i] < 0:
            raise error.RunError(5)
        elif index[i] < array_base or index[i] > dimensions[i]: 
            # WARNING: dimensions is the *maximum index number*, regardless of array_base!
            raise error.RunError(9)
    return [dimensions, lst]

def get_bytearray(name):
    if name[-1]=='$':
        # can't use string arrays for get/put
        raise error.RunError(13) # type mismatch
    try:
        [_, lst] = arrays[name]
        return lst
    except KeyError:
        return bytearray()

def base_array(base):
    global array_base
    if base not in (1, 0):
        # syntax error
        raise error.RunError(2)    
    if arrays != {}:
        # duplicate definition
        raise error.RunError(10)
    array_base = base

def get_array(name, index):
    [dimensions, lst] = check_dim_array(name, index)
    bigindex = index_array(index, dimensions)
    if name[-1]=='$':
        return (name[-1], lst[bigindex])
    value = lst[bigindex*var_size_bytes(name):(bigindex+1)*var_size_bytes(name)]
    return (name[-1], value)
    
def set_array(name, index, value):
    [dimensions, lst] = check_dim_array(name, index)
    bigindex = index_array(index, dimensions)
    value = vartypes.pass_type_keep(name[-1], value)[1]
    if name[-1]=='$':
       lst[bigindex] = value
       return 
    bytesize = var_size_bytes(name)
    lst[bigindex*bytesize:(bigindex+1)*bytesize] = value
    
def get_var_or_array(name, indices):
    if indices == []:
        return get_var(name)            
    else:
        return get_array(name, indices)

def set_var_or_array(name, indices, value):
    if indices == []:    
        set_var(name, value)
    else:
        set_array(name, indices, value)
        
def set_field_var(field, varname, offset, length):
    if varname[-1] != '$':
        # type mismatch
        raise error.RunError(13)
    str_ptr = StringPtr(field, offset, length)
    # assign the string ptr to the variable name
    # desired side effect: if we re-assign this string variable through LET, it's no longer connected to the FIELD.
    set_var(varname, vartypes.pack_string(str_ptr))
    
def assign_field_var(varname, value, justify_right=False):
    if varname[-1] != '$' or value[0] != '$':
        # type mismatch
        raise error.RunError(13)
    s = vartypes.unpack_string(value)
    try:
        el = len(variables[varname])    
    except KeyError:
        return
    if len(s) > el:
        s = s[:el]
    if len(s) < el:
        if justify_right:
            s = ' '*(el-len(s)) + s
        else:
            s += ' '*(el-len(s))
    #if isinstance(variables[varname], StringPtr):
    #    variables[varname].set_str(s)    
    #else:
    variables[varname][:] = s    

###########################################################

# memory model

# for reporting by FRE()        
def variables_memory_size():
#    return var_current + array_current + (var_current + total_mem - string_current)
    mem_used = 0
    for name in variables:
        mem_used += 1 + max(3, len(name))
        if name[-1] == '$':
            mem_used += 3+len(variables[name])
        else:
            mem_used += var_size_bytes(name)
    for name in arrays:
        mem_used += 4 + array_size_bytes(name) + max(3, len(name))
        dimensions, lst = arrays[name]
        mem_used += 2*len(dimensions)    
        if name[-1] == '$':
            for mem in lst:
                mem_used += len(mem)
    return mem_used

def get_var_ptr(name, indices):
    name = vartypes.complete_name(name)
    if indices == []:
        try:
            name_ptr, var_ptr, str_ptr = var_memory[name]
            return var_ptr
        except KeyError:
            return -1
    else:
        try:
            [dimensions, lst] = arrays[name]
            name_ptr, array_ptr = array_memory[name]
            # arrays are kept at the end of the var list
            return var_current + array_ptr + var_size_bytes(name) * index_array(indices, dimensions) 
        except KeyError:
            return -1

def get_name_in_memory(name, offset):
    if offset == 0:
        return byte_size[name[-1]]
    elif offset == 1:
        return ord(name[0].upper())
    elif offset == 2:
        if len(name) > 2:
            return ord(name[1].upper())
        else:
            return 0                    
    elif offset == 3:
        if len(name) > 3:
            return len(name)-3        
        else:
            return 0
    else:
        # rest of name is encoded such that c1 == 'A'
        return ord(name[offset-1].upper()) - ord('A') + 0xC1
                            
def get_var_memory(address):
    if address < var_current:
        # find the variable we're in
        name_addr = -1
        var_addr = -1
        str_addr = -1
        the_var = None 
        for name in var_memory:
            name_ptr, var_ptr, str_ptr = var_memory[name]
            if name_ptr <= address and name_ptr > name_addr:
                name_addr, var_addr, str_addr = name_ptr, var_ptr, str_ptr
                the_var = name
        if the_var == None:
            return -1        
        if address >= var_addr:
            offset = address - var_addr
            if offset >= byte_size[name[-1]]:
                return -1
            if name[-1] == '$':
                # string is represented as 3 bytes: length + uint pointer
                var_rep = bytearray(chr(len(variables[name]))) + vartypes.value_to_uint(str_addr)
            else:
                var_rep = variables[name]
            return var_rep[offset]
        else:
            offset = address - name_ptr
            return get_name_in_memory(name, offset)
    elif address < var_current + array_current:
        name_addr = -1
        arr_addr = -1
        the_arr = None 
        for name in array_memory:
            name_ptr, arr_ptr = array_memory[name]
            if name_ptr <= address and name_ptr > name_addr:
                name_addr, arr_addr = name_ptr, arr_ptr
                the_arr = name
        if the_arr == None:
            return -1        
        if address >= var_current + arr_addr:
            offset = address - arr_addr - var_current
            if offset >= array_size_bytes(name):
                return -1
            if name[-1] == '$':
                # TODO: not implemented for arrays of strings
                return 0
            return get_bytearray(name)[offset]
        else:
            offset = address - name_ptr - var_current
            if offset < max(3, len(name))+1:
                return get_name_in_memory(name, offset)
            else:
                offset -= max(3, len(name))+1
                [dimensions, lst] = arrays[name]
                data_rep = vartypes.value_to_uint(array_size_bytes(name) + 1 + 2*len(dimensions)) + chr(len(dimensions)) 
                for d in dimensions:
                    data_rep += vartypes.value_to_uint(d + 1 - array_base)
                return data_rep[offset]               
    elif address > string_current:
        # string space
        # find the variable we're in
        name_addr = -1
        var_addr = -1
        str_addr = -1
        the_var = None 
        for name in var_memory:
            name_ptr, var_ptr, str_ptr = var_memory[name]
            if str_ptr <= address and str_ptr > str_addr:
                name_addr, var_addr, str_addr = name_ptr, var_ptr, str_ptr
                the_var = name
        if the_var == None:
            return -1
        offset = address - str_addr
        return variables[name][offset]
    else:
        # unallocated var space
        return 0 
        
