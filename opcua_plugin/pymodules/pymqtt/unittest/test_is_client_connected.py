# -*- coding: UTF-8 -*-
# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, f'{SCRIPT_DIR}/../')
sys.path.insert(0, f'{SCRIPT_DIR}/../../../../pyutilities')
sys.path.insert(0, f'{SCRIPT_DIR}/../../')

from plugin_main import MqttPluginEntity
from plugin_main import MqttPluginConfig
from plugin_main import MqttPluginClient


class TestPluginMain(unittest.TestCase):
    def setUp(self):
        e = MqttPluginEntity(f'{SCRIPT_DIR}/../plugin_mqtt.json')
        c = MqttPluginConfig(f'{SCRIPT_DIR}/../default.conf')
        self.t = MqttPluginClient(e, c)
        self.t.start()

    def tearDown(self):
        self.t.stop()
        self.t = None

    def test_is_client_connected_T1(self):
        name = 'Device#0'
        res = self.t.is_client_connected(name)
        self.assertTrue(res, None)
        print("result:", res)

    def test_is_client_connected_T2(self):
        name = 'Device#2'
        res = self.t.is_client_connected(name)
        self.assertTrue(res, None)
        print("result:", res)

    def test_is_client_connected_F1(self):
        name = 'Device#1'
        res = self.t.is_client_connected(name)
        self.assertFalse(res, None)
        print("result:", res)

    def test_is_client_connected_F2(self):
        name = 'Device#10'
        res = self.t.is_client_connected(name)
        self.assertFalse(res, None)
        print("result:", res)


if __name__ == "__main__":
    unittest.main(verbosity=2)
