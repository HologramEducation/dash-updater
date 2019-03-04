#
#  usbupdater.py
#
# Author: Reuben Balik <reuben@konekt.io>
#
# License: Copyright (c) 2015 Konekt, Inc. All Rights Reserved.
#
# Released under the MIT License (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import hid
from kexceptions import *
import time

class DashVersion:
    major = 0
    minor = 0
    revision = 0

    def __init__(self, major=0, minor=0, revision=0):
        self.major = major
        self.minor = minor
        self.revision = revision

    @classmethod
    def fromlist(cls, lst):
        return cls(lst[0], lst[1], lst[2])

    @classmethod
    def fromstring(cls, s):
        return cls(*(map(int, s.split('.'))))

    def get_int(self):
        return ((self.major & 0xFF) << 16) | ((self.minor & 0xFF) << 8) | (self.revision & 0xFF)

    def __repr__(self):
        return str(self.major) + '.' + str(self.minor) + '.' + str(self.revision)

    def __lt__(self, other):
        if isinstance(other, DashVersion):
            return self.get_int() < other.get_int()
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, DashVersion):
            return self.get_int() <= other.get_int()
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, DashVersion):
            return self.get_int() == other.get_int()
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, DashVersion):
            return self.get_int() != other.get_int()
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, DashVersion):
            return self.get_int() > other.get_int()
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, DashVersion):
            return self.get_int() >= other.get_int()
        else:
            return NotImplemented

class DashVersions:
    user_boot = DashVersion()
    system_boot = DashVersion()
    system_firmware = DashVersion()

    def __init__(self, user_boot=DashVersion(), system_boot=DashVersion(), system_firmware=DashVersion()):
        if isinstance(user_boot, DashVersion):
            self.user_boot = user_boot
        else:
            raise TypeError('user_boot must be DashVersion')
        if isinstance(system_boot, DashVersion):
            self.system_boot = system_boot
        else:
            raise TypeError('system_boot must be DashVersion')
        if isinstance(system_firmware, DashVersion):
            self.system_firmware = system_firmware
        else:
            raise TypeError('system_firmware must be DashVersion')

    @classmethod
    def fromlist(cls, lst):
        return cls(DashVersion.fromlist(lst), DashVersion.fromlist(lst[6:]), DashVersion.fromlist(lst[9:]))

    def __repr__(self):
        return 'user_boot: ' + str(self.user_boot) + \
        ' system_boot ' + str(self.system_boot) + \
        ' system_firmware ' + str(self.system_firmware)

    def is_newer(self, other):
        if isinstance(other, DashVersions):
            return self.user_boot > other.user_boot or \
            self.system_boot > other.system_boot or \
            self.system_firmware > other.system_firmware
        else:
            return NotImplemented

class USBUpdater:
    def __init__(self, vid=0x7722, pid=0x1200, debug=False):
        self.debug = debug
        self.vid = vid
        self.pid = pid

    def set_ids(self, vid, pid):
        self.vid = vid
        self.pid = pid

    def send_kb(self, h, kb, packet_id, block_id):
        '''Send a 1 KB block of data.
        The send method is chosen based on the VID

        Keyword arguments:
        h -- USB HID handle of the device
        kb -- 1KB of string-based data
        packet_id -- destination for the data
        block_id -- first block is 0, so that the destination address is:
            block_id * 1024
        returns True if successful, False if not
        '''
        if self.vid == 0x7722:
            block = [0]*65 + [x for x in bytearray(kb)]
            block[1] = packet_id
            block[4] = packet_id
            block[5] = block_id & 0xFF
            block[6] = (block_id >> 8) & 0xFF
        else:
            block = [0]*4 + [x for x in bytearray(kb)]
            block[0] = 0x33 #OUTPUT Report ID
            block[1] = packet_id
            block[2] = block_id & 0xFF
            block[3] = (block_id >> 8) & 0xFF
        n = h.write(block)
        if n == -1:
            if self.debug: print "block", block_id, "failed write to", hex(packet_id), n, len(block)
            return False
        else:
            if self.debug:
                print "block", block_id, "written to", hex(packet_id)
        return True

    def memory_update(self, memory, packet_id, offset=0, first_block=0):
        retval = True
        h = hid.device()
        try:
            h.open(self.vid, self.pid)
            block_id = first_block
            while(retval):
                start = ((block_id-first_block) * 1024) + offset
                kb = memory[start:start+1024]
                if(len(kb) == 0):
                    break
                retval = self.send_kb(h, kb, packet_id, block_id)
                block_id += 1
        except:
            if self.debug: print "block write exception"
            return False
        finally:
            h.close()
        return retval

    def update(self, file, packet_id, offset=0, first_block=0):
        retval = True
        with open(file, 'rb') as f:
            f.seek(offset)
            h = hid.device()
            try:
                h.open(self.vid, self.pid)
                block_id = first_block
                while(f and retval):
                    kb = f.read(1024)
                    if(len(kb) == 0):
                        break
                    retval = self.send_kb(h, kb, packet_id, block_id)
                    block_id += 1
            except Exception as e:
                if self.debug: print "block write exception", e
                return False
            finally:
                h.close()
            return retval

    def reset(self, reset_id):
        h = hid.device()
        try:
            h.open(self.vid, self.pid)
            if self.vid == 0x7722:
                block = [0]*1089
                block[1] = reset_id
                block[4] = reset_id
            else:
                block = [0]*1028
                block[0] = 0x33 #OUTPUT Report ID
                block[1] = reset_id
            n = h.write(block)
            if n == -1:
                print "reset", hex(reset_id), "failed", reset_id, n
        finally:
            time.sleep(2) # Hacky fix for T963
            h.close()

    def get_device_versions(self):
        h = hid.device()
        try:
            h.open(self.vid, self.pid)
            versions = h.get_feature_report(0x40, 64)
            if len(versions) > 12 and versions[0] == 0x40:
                return DashVersions.fromlist(versions[1:])
        except:
            if self.debug: print "get_device_versions exception"
        finally:
            h.close()
        return DashVersions()

    def device_present(self, vid=None, pid=None):
        if vid is None:
            vid = self.vid
        if pid is None:
            pid = self.pid

        h = hid.device()
        try:
            h.open(vid, pid)
        except:
            return False
        finally:
            h.close()
        return True

    def update_user(self, file, offset=0, first_block=0):
        if self.debug: print 'update_user', file, offset, first_block
        return self.update(file, 0x18, offset, first_block)

    def update_system(self, file, offset=0, first_block=0):
        if self.debug: print 'update_system', file, offset, first_block
        return self.update(file, 0x3C, offset, first_block)

    def update_system_memory(self, memory, offset=0, first_block=0):
        if self.debug: print 'update_system_memory', len(memory), 'bytes', offset, first_block
        return self.memory_update(memory, 0x3C, offset, first_block)

    def reset_all(self):
        if self.debug: print 'reset_all'
        self.reset(0xFC)
