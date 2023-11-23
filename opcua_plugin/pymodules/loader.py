# --coding:utf-8--
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

# -----------------------------
# Copyright by Intel
# -----------------------------
import os
import sys
import subprocess

sys.path.insert(0, ".")
sys.path.append("../pyutilities/")

from logservice.logservice import LogService

logger = LogService.getLogger(__name__)


def load_plugin(name):
    return __import__(f'{name}.plugin_main', fromlist=[name])


def call_plugin(name, *args, **kwargs):
    try:
        plugin = load_plugin(name)
        plugin.plugin_main(*args, **kwargs)
    except ImportError as e:
        logger.exception('Import plugin handler failed :', str(e))


# --------------------
# main
# --------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python loader <plugin folder>')
    else:
        plugin_path = sys.argv[1]
        plugin_name = sys.argv[1].split('/')[1]
        sys.path.append(plugin_path)

        conf_list = []
        for (root, dirs, files) in os.walk(os.path.abspath(plugin_path)):
            conf_list.extend(
                os.path.join(root, f)
                for f in files
                if os.path.splitext(f)[1] == '.conf'
            )
        if len(conf_list) > 1:
            raise Exception(
                'The folder contains multiple configuration files : %s',
                plugin_path)
        elif not conf_list:
            logger.warn(
                'The configuration file is not found, use the default configuration')
        for entity_file in os.listdir(plugin_path):
            if entity_file.endswith(".json"):
                call_plugin(
                    plugin_name,
                    os.path.join(
                        plugin_path,
                        entity_file),
                    conf_list[0] if len(conf_list) == 1 else None)
