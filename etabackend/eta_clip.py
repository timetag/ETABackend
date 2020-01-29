import os
import time

from parser_header import ETACReaderStructIDX, parse_header


class Clip():

    def __init__(self):
        self.fseekpoint = 0  # 0
        self.fendpoint = 0  # 1

        self.TTRes_pspr = 0  # 2
        self.DTRes_pspr = 0  # 3
        self.SYNCRate_pspr = 0  # 4
        self.BytesofRecords = 0  # 5
        self.RecordType = 0  # 6

        self.GlobalTimeShift = 0  # 7
        self.UnusedConfig = 0  # 8 unused

        # UniBuf info
        self.batch_actualread_length = 0  # 9 buffer length
        self.next_RecID_in_batch = 0  # 10 reader head

        self.overflowcorrection = 0  # 11
        self.resuming = 0  # 12
        self.buffer = None  # 13
        self.buffer_type = 0  # 14 unused

        # other info
        self.filename = None

    def validate(self):
        self.GlobalTimeShift = int(self.GlobalTimeShift)
        self.TTRes_pspr = int(self.TTRes_pspr)
        self.DTRes_pspr = int(self.DTRes_pspr)
        self.SYNCRate_pspr = int(self.SYNCRate_pspr)
        if self.fseekpoint >= self.fendpoint:
            return False
        return self

    def from_parser_output(self, parse_output):
        self.fseekpoint = parse_output[ETACReaderStructIDX.fseekpoint]
        self.fendpoint = parse_output[ETACReaderStructIDX.fendpoint]

        self.TTRes_pspr = parse_output[ETACReaderStructIDX.TTRes_pspr]
        self.DTRes_pspr = parse_output[ETACReaderStructIDX.DTRes_pspr]
        self.SYNCRate_pspr = parse_output[ETACReaderStructIDX.SYNCRate_pspr]
        self.BytesofRecords = parse_output[ETACReaderStructIDX.BytesofRecords]
        self.RecordType = parse_output[ETACReaderStructIDX.RecordType]

        self.GlobalTimeShift = parse_output[ETACReaderStructIDX.GlobalTimeShift]
        if len(parse_output) < ETACReaderStructIDX.resuming:
            self.resuming = 0
        else:
            self.resuming = parse_output[ETACReaderStructIDX.resuming]

    def to_parser_output(self):
        return [
            self.fseekpoint,  # 0
            self.fendpoint,  # 1

            self.TTRes_pspr,  # 2
            self.DTRes_pspr,  # 3
            self.SYNCRate_pspr,  # 4
            self.BytesofRecords,  # 5
            self.RecordType,  # 6

            self.GlobalTimeShift,  # 7
            self.UnusedConfig,  # 8 unused

            # UniBuf info
            self.batch_actualread_length,  # 9 buffer length
            self.next_RecID_in_batch,  # 10 reader head

            self.overflowcorrection,  # 11
            self.resuming,  # 12
            0,  # 13
            self.buffer_type,  # 14 unused
        ]


class ETA_CUT():
    def __init__(self):
        pass

    # example generators
    def simple_cut(self, filename, cuts=1, format=-1, keep_indexes=None, reuse_last_clip=False):

        last_clip = self.clip_from_file(
            filename, read_events=1, format=format, wait_timeout=0, verbose=False)

        self.send(
            "ETA.SIMPLE_CUT (Deprecated): The file '{filename}' will be cut into {cuts} equal size Clips. ".format(filename=filename,
                                                                                                                   cuts=cuts))
        TTF_header_offset = last_clip.fseekpoint
        TTF_filesize = os.path.getsize(str(filename))

        NumRecords = (
            TTF_filesize - TTF_header_offset) // last_clip.BytesofRecords

        caller_parms = []

        # build a clip for header
        last_clip.fendpoint = last_clip.fseekpoint
        for i in range(cuts):

            currentclip = Clip()
            # copy information from last clip
            currentclip.from_parser_output(last_clip.to_parser_output())
            self.clip_from_file(filename, modify_clip=currentclip, read_events=(
                (NumRecords+cuts-1) // cuts), format=format, wait_timeout=0, verbose=False)
            caller_parms.append(currentclip)
            last_clip = currentclip

        if keep_indexes:
            if type(keep_indexes) == list:
                caller_parms = [caller_parms[i] for i in keep_indexes]
            else:
                raise ValueError(
                    "ETA.SIMPLE_CUT: The third parameter, keep_indexes, should be a list . ")

        return caller_parms

    def incremental_cut(self, filename, modify_clip=None, rec_per_cut=0, format=-1, wait_timeout=0, verbose=print):
        return self.clip_from_file(filename, modify_clip, rec_per_cut, format, wait_timeout, verbose)
        """
        int MKS_inline read_next_minibatch() {
            READERs[0].batch_actualread_length = fread(READERs[0].buffer, READERs[0].BytesofRecords, batchreadRecNum, READERs[0].fpttf)*READERs[0].BytesofRecords;
            READERs[0].batch_nextreadpos_in_file += READERs[0].batch_actualread_length;
            const long long batches_left = READERs[0].batch_nextreadpos_in_file - READERs[0].fseekpoint;
            
            if (batches_left % (200* batchreadRecNum*READERs[0].BytesofRecords) == 0) {
                const long long total_batches = (READERs[0].fendpoint - READERs[0].fseekpoint);
                const long long percentage = batches_left * 100  / total_batches;
                PINFO("Reader %x for section [%lld %lld) %lld%% finished.", READERs, READERs[0].fseekpoint, READERs[0].fendpoint, percentage)
            }
            READERs[0].next_RecID_in_batch = 0; 
            return READERs[0].batch_actualread_length;
        }
        """
    # low-level API

    def clip_from_file(self, filename, modify_clip=None, read_events=0, format=-1, wait_timeout=0, verbose=print):
        filename = str(filename)  # supporting pathlib
        if (verbose == True):
            verbose = print
        if modify_clip == None:
            ret1, parse_output = parse_header(filename, format)
            if ret1 is not 0:
                raise ValueError(
                    "ETA.incremental_cut: File {} is not found or incorrect, err code {}.".format(filename, ret1))
            temp_clip = Clip()
            temp_clip.from_parser_output(parse_output)
        else:
            temp_clip = modify_clip

        # validate
        if not isinstance(temp_clip, Clip):
            raise ValueError(
                "Incremental cut must take a one Clip object as input.")

        # moving to the end of the last read
        temp_clip.fseekpoint = temp_clip.fendpoint

        # use actual size of the file
        fileactualsize = os.path.getsize(filename)
        if read_events <= 0:
            read_events += (fileactualsize -
                            temp_clip.fseekpoint)//temp_clip.BytesofRecords
        # read at least one record each time
        if read_events <= 0:
            read_events = 1
        # update the new ending
        temp_clip.fendpoint = temp_clip.fseekpoint + \
            temp_clip.BytesofRecords * read_events

        # wait for data
        waited_for = 0.0
        while not fileactualsize >= temp_clip.fendpoint:
            waited_for += 0.01
            if waited_for > wait_timeout:
                if verbose:
                    verbose(
                        "Timeout when waiting for the next cut, round to file boundry.")
                temp_clip.fendpoint = fileactualsize
                break
            if verbose:
                verbose("Waiting for file {} to grow from {} to {} bytes.".format(filename,
                                                                                  fileactualsize,
                                                                                  temp_clip.fendpoint))
            # hard-coded checking period is probably not good.
            time.sleep(0.01)

        # load data

        with open(filename, "rb") as f:
            if (temp_clip.buffer == None or len(temp_clip.buffer) != temp_clip.fendpoint-temp_clip.fseekpoint):
                # reuser buffer as much as possible
                temp_clip.buffer = bytearray(
                    temp_clip.fendpoint-temp_clip.fseekpoint)
            f.seek(temp_clip.fseekpoint)
            temp_clip.batch_actualread_length = f.readinto(temp_clip.buffer)
        # fail when zero size
        if temp_clip.batch_actualread_length == 0:
            if verbose:
                verbose(
                    "ETA.incremental_cut: The file '{}' is not long enough for the Clip. ".format(filename))
            return False
        else:
            if verbose:
                verbose(
                    "ETA.incremental_cut: The file '{}' section [{},{}) is loaded into the Clip. ".format(filename, temp_clip.fseekpoint, temp_clip.fendpoint))

        return temp_clip.validate()
