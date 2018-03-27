def get_onefile_loop(tables, init, looping, globals_init, num_rslot,num_rchns, num_vslot):
    return """
@jit(nopython=True, parallel=True, nogil=True)
def mainloop(chn, {tables}, filename1, fseekpoint, fendpoint, BytesofRecords, TTRes_pspr, SYNCRate_pspr, DTRes_pspr):
    link_libs()
    Channel = ffi.from_buffer(chn)
    Filename = ffi.from_buffer(filename1)
    eta_ret = 0
    eta_ret += FileReader_init(Filename, fseekpoint, fendpoint,
                            BytesofRecords, TTRes_pspr, SYNCRate_pspr, DTRes_pspr)

    # print("bytes of the rec", READER_BytesofRecords_get())
    eta_ret += POOL_init({num_rslot},{num_rchns},  {num_vslot})
    #count = 0
    {init}
    AbsTime_ps = POOL_next(Channel)
    while AbsTime_ps != 9223372036854775807:
        #count += 1
        # if count %1000 ==0:
        #   print(AbsTime_ps,chn)
        {looping}

        AbsTime_ps = POOL_next(Channel)
    return eta_ret

def sp_core(caller_parms,mainloop):
    {globals_init}
    filename = caller_parms.pop()
    print(mainloop(np.zeros(1, dtype=np.int8), {tables},  bytearray(filename, "ascii"), *caller_parms))
    return ({tables})

#globals_init
# routine warming up
#mainloop(np.zeros(1, dtype=np.int8), {tables},
#         bytearray("NONEXISTING", "ascii"), 1,1,1,1,1,1)
""".format(init=init, looping=looping, globals_init=globals_init, tables=",".join(tables), num_rslot=num_rslot,
           num_vslot=num_vslot,num_rchns=num_rchns)
