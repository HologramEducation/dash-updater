#
#  otaupdater.py
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

import requests
import os.path
import json
from kexceptions import UpdaterException

class OTAUpdater:
    apibase = 'https://dashboard.hologram.io/api/1/'
    def __init__(self, imagefile):
        self.apikey = None
        self.imagefile = imagefile

    def set_apikey(self, apikey):
        self.apikey = apikey

    def set_apibase(self, apibase):
        self.apibase = apibase

    def load_userinfo(self):
        apiurl = self.apibase + 'users/me/'
        url_params = {'apikey' : self.apikey}
        r = requests.get(apiurl, params=url_params)
        if r.status_code != requests.codes.ok:
            raise UpdaterException('Error connecting to API: ' + r.text)
        else:
            resp = r.json();
            return resp['data']

    def load_devices(self, orgid):
        apiurl = self.apibase + 'devices/'
        url_params = {'apikey' : self.apikey, 'orgid' : orgid,
                      'limit' : 1000}
        devices = []
        while True:
          r = requests.get(apiurl, params=url_params)
          if r.status_code != requests.codes.ok:
              raise UpdaterException('Error connecting to API: ' + r.text)
          else:
              resp = r.json();
              data = resp['data']
              devices += data

              if (len(data) < 1000):
                  break
              else:
                  url_params['startafter'] = data[-1]['id']
        return devices


    def load_orgs(self, userid):
        apiurl = self.apibase + 'organizations/'
        url_params = {'apikey' : self.apikey, 'userid' : userid,
                      'limit' : 1000}
        orgs = []
        while True:
          r = requests.get(apiurl, params=url_params)
          if r.status_code != requests.codes.ok:
              raise UpdaterException('Error connecting to API: ' + r.text)
          else:
              resp = r.json();
              data = resp['data']
              orgs += data

              if (len(data) < 1000):
                  break
              else:
                  url_params['startafter'] = data[-1]['id']
        return orgs



    def get_orgs(self):
        userinfo = self.load_userinfo()
        return self.load_orgs(userinfo['id'])


    def get_device_list(self, orgid):
        devices = self.load_devices(orgid)
        return devices


    def update(self, deviceid, orgid):
        if(not os.path.exists(self.imagefile) or
                not os.path.isfile(self.imagefile)):
            raise IOError('Image file %s does not exist' % self.imagefile)
        print("Pushing firmware to device ID #%d" % deviceid)
        #upload image
        apiurl = self.apibase + 'firmwareimages/'
        url_params = {'apikey' : self.apikey, 'orgid' : orgid}
        fname = os.path.basename(self.imagefile)
        files = {'imagefile': (fname, open(self.imagefile, 'rb'),
            'application/octet-stream')}
        print("Uploading")
        r = requests.post(apiurl, files=files, params=url_params)
        if r.status_code != requests.codes.ok:
            raise UpdaterException('Error uploading image: ' + r.text)
        resp = r.json()
        imageobj = resp['data']
        fwid = imageobj['id']
        print("Firmware ID #%d created" % fwid)
        print("Executing push to device")
        sendurl = self.apibase + 'firmwareimages/' + str(fwid) + '/send'
        payload = { 'deviceids': [deviceid] }
        headers = {'Content-Type':'application/json'}
        r = requests.post(sendurl,
                params=url_params,
                data=json.dumps(payload),
                headers=headers)
        if r.status_code != requests.codes.ok:
            raise UpdaterException('Error pushing image: ' + r.text)
        print("OTA update sent")


