#
#  updatergui.py
#
# Author: Hologram <support@hologram.io>
#
# License: Copyright (c) 2015-2017 Konekt, Inc. All Rights Reserved.
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

# This is super hacky. Pyinstaller imports future which seems to have a
# bug where certain pieces of tkinter are missing. We want to force
# easygui to use the built-in 2.7 Tkinter and not the future tkinter
import sys
sys.modules['tkinter']=None
import easygui

class UpdaterGUI:
    title = "Hologram Updater"
    def __init__(self, version):
        title = self.title + ' v' + version
        self.title = title

    def prompt_for_apikey(self):
        return easygui.passwordbox(
                msg="Please paste in your Hologram API key",
                title=self.title)

    def prompt_for_deviceid(self, devices):
        device_list = []
        device_map = {}
        for device in devices:
            device_list.append(device['name'])
            device_map[device['name']] = device['id']
        res = easygui.choicebox(
                msg='Choose the device to update',
                title=self.title,
                choices=device_list)
        if res == None:
            return None
        return device_map[res]


    def prompt_for_orgid(self, orgs):
        org_list = []
        org_map = {}
        for org in orgs:
            org_list.append(org['name'])
            org_map[org['name']] = org['id']
        res = easygui.choicebox(
                msg='What organization does the device fall under?',
                title=self.title,
                choices=org_list)
        if res == None:
            return None
        return org_map[res]


    def prompt_for_imagetype(self):
        res = easygui.buttonbox(
                msg="What type of update do you want to push?",
                title=self.title,
                choices=["User Program", "System Firmware"])
        if res == 'User Program':
            return 'user'
        elif res == 'System Firmware':
            return 'system'
        else:
            return None


    def prompt_for_method(self, imagetype):
        choices = ["USB"]
        if imagetype == 'user':
            choices.append('OTA')
        res = easygui.buttonbox(
                msg="What type of update do you want to push?",
                title=self.title,
                choices=choices)
        if res == 'USB':
            return 'usb'
        elif res == 'OTA':
            return 'ota'
        else:
            return None

    def ask_firmware_update(self, old_version, new_version):
        return easygui.ynbox('New system firmware is available, update now?\n' +
        str(old_version) + ' -> ' + str(new_version) + '\n',
        self.title, ('Yes', 'No'))

    def ask_boot_update(self, old_version, new_version, firmware_old, firmware_new):
        msg = 'Boot upgrade is available, update now?\n' + str(old_version) + ' -> ' + str(new_version) + '\n'
        if(firmware_new > firmware_old):
            msg += 'Will also update system firmware\n' + str(firmware_old) + ' -> ' + str(firmware_new) + '\n'
        return easygui.ynbox(msg, self.title)

    def prompt_for_firmware_save(self, filename):
        if easygui.ynbox("Save the firmware before loading?", self.title):
            return easygui.filesavebox(
                    msg='Choose the image file to save',
                    default=filename,
                    title=self.title,
                    filetypes=["*.bin", "*.*"])
        return None

    def prompt_for_file(self):
        res = easygui.fileopenbox(
                msg='Choose the image file to send',
                filetypes = ["*.bin", "*.*"],
                title=self.title)
        #BUG IN easygui 0.97.4: does not return None on pressing cancel
        if res == '.': return None
        return res

    def show_message(self, message):
        return easygui.msgbox(
                msg=message,
                title=self.title)

    def show_exception(self):
        return easygui.exceptionbox(
                title=self.title)
