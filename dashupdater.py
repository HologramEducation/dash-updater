#!/usr/bin/python
#
# dashupdater.py - Utility for pushing updates to a Konekt Dash using
# various methods
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

from libs.usbupdater import USBUpdater, DashVersion, DashVersions
from libs.otaupdater import OTAUpdater
from libs.updatergui import UpdaterGUI
from libs.updatertextui import UpdaterTextUI
from libs.kexceptions import *

import argparse
import os
import sys
import requests

class DashUpdater:
    pid = 0x1100
    vid = 0x2cf3
    method = None
    imagefile = None
    imagetype = None
    apikey = None
    deviceid = None
    orgid = None
    apibase = None
    debug = False
    update_url = 'http://downloads.hologram.io/dash/system_firmware'
    download_firmware_version = None
    download_firmware_url = None
    download_boot_version = None
    download_boot_url = None
    check_update = True
    def __init__(self, version):
        self.version = version
    def set_vid(self, vid):
        self.vid = vid
    def set_pid(self, pid):
        self.pid = pid
    def set_method(self, method):
        self.method = method
    def set_imagefile(self, imagefile):
        self.imagefile = imagefile
    def set_imagetype(self, imagetype):
        self.imagetype = imagetype
    def set_apikey(self, apikey):
        self.apikey = apikey
    def set_deviceid(self, deviceid):
        self.deviceid = deviceid
    def set_orgid(self, orgid):
        self.orgid = orgid
    def set_apibase(self, apibase):
        self.apibase = apibase
    def set_debug(self, debug):
        self.debug = debug
    def set_update_url(self, update_url):
        self.update_url = update_url
    def set_check_update(self, check_update):
        self.check_update = check_update

    def validate_file(self, offset, id, filename):
        valid = False
        if filename is None:
            filename = self.imagefile
        try:
            with open(filename, 'r') as f:
                f.seek(offset)
                fid = f.read(len(id))
                if fid == id:
                    valid = True
        except IOError:
            raise
        return valid

    def validate_memory(self, offset, id, memory):
        try:
            tag = memory[offset:offset+len(id)]
            return tag == id
        except:
            pass
        return False

    def validate_system(self, filename=None):
        return self.validate_file(0xC0, "APP0DPM2", filename)

    def validate_system_memory(self, memory):
        return self.validate_memory(0xC0, "APP0DPM2", memory)

    def validate_user(self):
        #TODO: use PID
        #For now, we allow anything to be sent to the user module so
        #people can use another compiler
        return os.path.isfile(self.imagefile)

    def validate_image(self):
        if self.imagetype == 'user':
            res = self.validate_user()
        elif self.imagetype == 'system':
            res = self.validate_system()
        else:
            raise KonektException('Invalid Image Type')
        if not res:
            raise KonektException('Invalid Image File')

    def finish_update(self, ui):
        if self.method == 'usb':
            self.finish_update_usb(ui)
        elif self.method == 'ota':
            self.finish_update_ota(ui)
        else:
            raise KonektException('Invalid Update Method')


    def finish_update_ota(self, ui):
        updater = OTAUpdater(self.imagefile)
        if self.apibase:
            updater.set_apibase(self.apibase)
        if not self.apikey:
            self.apikey = ui.prompt_for_apikey()
            if not self.apikey:
                raise MissingParamException('apikey')
        updater.set_apikey(self.apikey)
        if not self.orgid:
            orgs = updater.get_orgs()
            if len(orgs) == 1:
                orgid = orgs[0]['id']
            else:
                orgid = ui.prompt_for_orgid(orgs)
        if not self.deviceid:
            if orgid is None or not orgid:
                raise MissingParamException('orgid')
            devices = updater.get_device_list(orgid)
            if not devices:
                raise KonektException("You have no devices in your account")
            self.deviceid = ui.prompt_for_deviceid(devices)
            if not self.deviceid:
                raise MissingParamException('deviceid')
        updater.update(self.deviceid, orgid)


    def exception_usb_update(self):
        raise KonektException( ("Error updating over USB.\n"
                    "Is the correct Dash connected and did you push the "
                    "program button?\n"
                    "Contact us or visit the forum at "
                    "community.hologram.io if you need help") )


    def download_exception(self):
        raise KonektException( ("Error updating over USB.\n"
                    "Firmware could not be downloaded.\n"
                    "Contact us or visit the forum at "
                    "community.hologram.io if you need help") )


    def download_firmware(self, url):
        if url is None:
            return None
        r = requests.get(url)
        if r.ok:
            if self.debug:
                print 'successful download of ', url, ' ', len(r.content), 'bytes'
            return r.content
        return None

    def fetch_download_versions(self):
        try:
            r = requests.get(self.update_url+'/version.json')
        except Exception as e:
            if self.debug: print 'fetch_download_versions:', e
            return False
        if r.ok:
            try:
                self.download_firmware_version = DashVersion.fromstring(r.json()['system_firmware_version'])
                self.download_firmware_url = self.update_url+'/'+r.json()['system_firmware_location'] + str(self.download_firmware_version) + '.bin'
                self.download_boot_version = DashVersion.fromstring(r.json()['boot_version'])
                self.download_boot_url = self.update_url+'/'+r.json()['boot_location'] + str(self.download_boot_version) + '.bin'
                if self.debug:
                    print 'Download firmware version', self.download_firmware_version
                    print 'Download firmware', self.download_firmware_url
                    print 'Download boot version', self.download_boot_version
                    print 'Download boot', self.download_boot_url
            except Exception as e:
                if self.debug: print 'fetch_download_versions:', e
                return False
        return True

    def update_boot_firmware(self, updater, ui):
        boot_firmware = self.download_firmware(self.download_boot_url)
        system_firmware = self.download_firmware(self.download_firmware_url)
        if self.validate_system_memory(boot_firmware) and self.validate_system_memory(system_firmware):
            filename_firmware = ui.prompt_for_firmware_save('boot_' + str(self.download_boot_version) + '_system_' + str(self.download_firmware_version) + '.bin')
            if filename_firmware:
                try:
                    with open(filename_firmware, 'wb') as f:
                        f.write(boot_firmware)
                        while f.tell() < (64 * 1024):
                            f.write('\xFF')
                        f.write(system_firmware)
                except:
                    ui.show_exception()
            if not updater.update_system_memory(boot_firmware, 0, 0):
                self.exception_usb_update()
            if not updater.update_system_memory(system_firmware, 0, 64):
                self.exception_usb_update()
        else:
            self.download_exception()

    def update_system_firmware(self, updater, ui):
        system_firmware = self.download_firmware(self.download_firmware_url)
        if self.validate_system_memory(system_firmware):
            filename_firmware = ui.prompt_for_firmware_save('system_firmware_' + str(self.download_firmware_version) + '.bin')
            if filename_firmware:
                try:
                    with open(filename_firmware, 'wb') as f:
                        f.write(system_firmware)
                except:
                    ui.show_exception()
            if not updater.update_system_memory(system_firmware, 0, 0):
                self.exception_usb_update()
        else:
            self.download_exception()

    def finish_update_usb(self, ui):
        updater = USBUpdater(self.vid, self.pid, self.debug)
        device_versions = DashVersions()

        if updater.device_present():
            if self.debug: print 'Device found'
            device_versions = updater.get_device_versions()
        elif updater.device_present(0x7722, 0x1200):
            if self.debug: print 'Device 7722:1200 found'
            updater.set_ids(0x7722, 0x1200)
        else:
            self.exception_usb_update()

        if self.imagetype == 'user' and self.check_update and self.fetch_download_versions():
            if self.debug: print 'checking for updates...'
            if self.debug: print self.download_boot_version, device_versions.system_boot, device_versions.user_boot
            if self.download_boot_version > min(device_versions.system_boot, device_versions.user_boot):
                if self.debug:
                    print 'boot available', device_versions.system_boot, '->', self.download_boot_version
                if ui.ask_boot_update(min(device_versions.system_boot, device_versions.user_boot), self.download_boot_version, device_versions.system_firmware, self.download_firmware_version):
                    self.update_boot_firmware(updater, ui)
            elif self.download_firmware_version > device_versions.system_firmware:
                if self.debug:
                    print 'firmware available', device_versions.system_firmware, '->', self.download_firmware_version
                if ui.ask_firmware_update(device_versions.system_firmware, self.download_firmware_version):
                    self.update_system_firmware(updater, ui)
        elif self.imagetype == 'system':
            if not updater.update_system(self.imagefile):
                self.exception_usb_update()

        if self.imagetype == 'user':
            if not updater.update_user(self.imagefile):
                self.exception_usb_update()

        updater.reset_all()

    def start_update(self, ui):
        if not self.imagetype:
            self.imagetype = ui.prompt_for_imagetype()
            if not self.imagetype:
                raise MissingParamException('imagetype')
        if not self.imagefile:
            self.imagefile = ui.prompt_for_file()
            if not self.imagefile or self.imagefile == '.':
                raise MissingParamException('imagefile')
        self.validate_image()
        if not self.method:
            self.method = ui.prompt_for_method(self.imagetype)
            if not self.method:
                raise MissingParamException('method')
        self.finish_update(ui)

    def update(self, text_mode, use_text_success):
        ui = None
        if text_mode:
            ui = UpdaterTextUI(self.version)
        else:
            ui = UpdaterGUI(self.version)
        if self.debug: print "DEBUG!"
        try:
            self.start_update(ui)
        except MissingParamException as e:
            if self.debug:
                ui.show_exception()
            sys.exit(0)
        except KonektException as e:
            if self.debug:
                ui.show_exception()
            else:
                ui.show_message("Error: " + str(e))
            sys.exit(1)
        except IOError as e:
            if self.debug:
                ui.show_exception()
            else:
                ui.show_message("Error opening file: " + str(e.strerror))
            sys.exit(1)
        except:
            ui.show_exception()
            sys.exit(1)
        if use_text_success:
            ui = UpdaterTextUI(self.version)
        if self.imagetype == 'reprogram_system':
            ui.show_message("Firmware Update Complete\nPress the program button again to load the new System image")
        else:
            ui.show_message('Update Complete')

def auto_int(x):
    return int(x, 0)

def main():
    version = get_version()
    parser = argparse.ArgumentParser(
            description='Push a firmware image to a Konekt Dash',
            add_help=True)
    parser.add_argument('--vid', type=auto_int, help=argparse.SUPPRESS)
    parser.add_argument('--pid', type=auto_int, help=argparse.SUPPRESS)
    parser.add_argument('--imagetype', choices=['user', 'system'])
    parser.add_argument('--imagefile', type=str)
    parser.add_argument('--method', choices=['usb', 'ota'])
    parser.add_argument('--apikey', type=str)
    parser.add_argument('--deviceid', type=int)
    parser.add_argument('--orgid', type=int,
        help="Needed for OTA if the device isn't on your default organization")
    parser.add_argument('--text-mode', action='store_true',
        help="Disable the GUI and do everything via text inputs")
    parser.add_argument('--apibase', type=str, help=argparse.SUPPRESS)
    parser.add_argument('--version', action='version', version='dashupdater v'+version)
    parser.add_argument('--debug', help=argparse.SUPPRESS, action='store_true')
    parser.add_argument('--updateurl', help=argparse.SUPPRESS)
    parser.add_argument('--nocheck', help=argparse.SUPPRESS, action='store_true')
    # This is so that in Arduino we don't generate a dialog box on success
    # and just print to the console
    parser.add_argument('--use-text-success', help=argparse.SUPPRESS,
            action='store_true')
    args = parser.parse_args()
    updater = DashUpdater(version)
    if args.vid:
        updater.set_vid(args.vid)
    if args.pid:
        updater.set_pid(args.pid)
    if args.imagefile:
        updater.set_imagefile(args.imagefile)
    if args.imagetype:
        updater.set_imagetype(args.imagetype)
    if args.apikey:
        updater.set_apikey(args.apikey)
    if args.deviceid:
        updater.set_deviceid(args.deviceid)
    if args.apibase:
        updater.set_apibase(args.apibase)
    if args.debug:
        updater.set_debug(True)
    if args.method:
        updater.set_method(args.method)
    if args.updateurl:
        updater.set_update_url(args.updateurl)
    if args.nocheck:
        updater.set_check_update(False)
    if args.orgid:
        updater.set_orgid(args.orgid)
    updater.update(args.text_mode, args.use_text_success)

def get_basedir():
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        return sys._MEIPASS
    else:
        # we are running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

def get_version():
    with open(get_basedir() + '/version.txt', 'r') as f:
        return f.readline().rstrip()

if __name__ == "__main__":
    main()
