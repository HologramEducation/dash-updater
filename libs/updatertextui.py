#
#  updatertextui.py
#
# Author: Hologram <support@hologram.io>
#
# License: Copyright (c) 2017 Konekt, Inc. All Rights Reserved.
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

import sys

class UpdaterTextUI:
    title = "Hologram Updater"
    def __init__(self, version):
        title = self.title + ' v' + version
        self.title = title


    def prompt_for_apikey(self):
        return raw_input("Please enter your Hologram API key: ")


    def prompt_for_deviceid(self, devices):
        print("Available devices: ")
        result = None
        deviceids = []
        if not devices:
            print("  [NONE]")
        else:
            for device in devices:
                deviceids.append(device['id'])
                print("  ID#%d - %s"%(device['id'], device['name']))
            while True:
                deviceid = raw_input("Enter device ID to update: ")
                if not deviceid.isdigit():
                    print("Error: Invalid deviceid")
                    continue
                deviceid = int(deviceid)
                if deviceid not in deviceids:
                    print("Error: Invalid deviceid")
                    continue
                break
            result = deviceid
        return result


    def prompt_for_orgid(self, orgs):
        print("Available organizations: ")
        result = None
        orgids = []
        if not orgs:
            print("  [NONE]")
        else:
            for org in orgs:
                orgids.append(org['id'])
                print("  ID#%d - %s"%(org['id'], org['name']))
            while True:
                orgid = raw_input(
                        "Choose the organization id to search for the device: ")
                if not orgid.isdigit():
                    print("Error: Invalid organization id")
                    continue
                orgid = int(orgid)
                if orgid not in orgids:
                    print("Error: Invalid organization id")
                    continue
                break
            result = orgid
        return result


    def prompt_for_imagetype(self):
        options = {"U":"user","S":"system"}
        print("What type of update do you want to push?")
        while True:
            choice = raw_input("(U)ser or (S)ystem? ")
            choice = choice.upper()
            if choice not in options:
                continue
            return options[choice]


    def prompt_for_method(self, imagetype):
        options = {"U":"usb"}
        optstr = "U:USB"
        if imagetype == 'user':
            optstr += " or O:OTA"
            options["O"] = 'ota'
        print("How do you want to push the update?")
        optstr += "? "
        while True:
            choice = raw_input(optstr)
            choice = choice.upper()
            if choice not in options:
                continue
            return options[choice]


    def prompt_yes_no(self):
        while True:
            choice = raw_input("(Y)es or (N)o? ")
            choice = choice.upper()
            if choice not in "YN":
                continue
            res = False
            if choice == "Y":
                res = True
            return res


    def ask_firmware_update(self, old_version, new_version):
        print('New system firmware is available, update now?\n' +
            str(old_version) + ' -> ' + str(new_version) + '\n')
        return self.prompt_yes_no()


    def ask_boot_update(self, old_version, new_version, firmware_old, firmware_new):
        msg = 'Boot upgrade is available, update now?\n' + str(old_version) + ' -> ' + str(new_version) + '\n'
        if(firmware_new > firmware_old):
            msg += 'Will also update system firmware\n' + str(firmware_old) + ' -> ' + str(firmware_new) + '\n'
        print(msg)
        return self.prompt_yes_no()


    def prompt_for_firmware_save(self, filename):
        print("Save the firmware before loading?")
        if self.prompt_yes_no():
            return raw_input("Enter the filename to save: ")
        return None


    def prompt_for_file(self):
        return raw_input("Enter the filename to open: ")


    def show_message(self, message):
        print(message)


    def show_exception(self):
        print(str(sys.exc_info()))
