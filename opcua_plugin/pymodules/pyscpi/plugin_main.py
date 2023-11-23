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
import json
import sys
import serial
from client import BasePluginClient
from entity import BasePluginEntity
from config import BasePluginConfig
from socket import *

from ret_codes import ReturnCodes
from logservice.logservice import LogService

logger = LogService.getLogger(__name__)


class SCPISerialClient(object):
    def __init__(self):
        self.clients = []

    def getcli(self, port):
        return next(
            (client for client in self.clients if port == client['port']), None
        )

    def addcli(self, port, param):
        com_id = port[4:]
        com_param = [9600, 8, 'N', 1, 0, 0, 0, 0]
        if param is not None:
            s = param.split('-')
            com_param = [
                int(
                    s[0]), int(
                    s[1]), s[2], int(
                    s[3]), int(
                    s[4]), int(
                        s[5]), int(
                            s[6]), int(
                                s[7])]
        ser_client = serial.Serial(
            baudrate=com_param[0],
            bytesize=com_param[1],
            parity=com_param[2],
            timeout=com_param[4],
            stopbits=com_param[3],
            dsrdtr=com_param[5],
            xonxoff=com_param[6],
            rtscts=com_param[7])
        ser_client.setPort(com_id)
        client_param = {'port': port, 'client': ser_client, 'state': 'closed'}
        self.clients.append(client_param)
        return ser_client

    def open(self, port, param):
        errorcode = ReturnCodes.Good
        try:
            cli = self.getcli(port)
            if cli is None:
                ser_client = self.addcli(port, param)
                cli = self.getcli(port)
            else:
                ser_client = cli['client']
            if not ser_client.isOpen():
                ser_client.open()
            cli['state'] = 'opened'
            result = f'serial port {port} is opened'
        except BaseException:  # serial.SerialException as e:
            logger.exception(f'failed to open serial port {port}')
            result = f'failed to open serial port {port}'
            errorcode = ReturnCodes.SCPI_SerialOpenFail
        return errorcode, result

    def close(self, port):
        errorcode = ReturnCodes.Good
        try:
            cli = self.getcli(port)
            if cli is not None:
                ser_client = cli['client']
                ser_client.close()
                cli['state'] = 'closed'
                if not ser_client.isOpen():
                    result = f'serial port {port} was closed'
                else:
                    errorcode = ReturnCodes.SCPI_SerialCloseFail
                    result = f'failed to close serial port {port}'
            else:
                errorcode = ReturnCodes.SCPI_SerialNotOpen
                result = f'serial port {port} was not opened'
        except BaseException:  # serial.SerialException as e:
            errorcode = ReturnCodes.SCPI_SerialCloseFail
            result = f'failed to close serial port {port}'
            logger.exception(f'failed to close serial port {port}')
        return errorcode, result

    def send(self, port, data):
        errorcode = ReturnCodes.Good
        try:
            cli = self.getcli(port)
            if cli is not None:
                ser_client = cli['client']
                ser_client.write(data.encode("ascii"))
                if data in ["*IDN?\r\n", "SYST:VERS?\r\n"]:
                    str = ser_client.readline()  # (eol='\r\n')
                    result = str.decode('utf8')
                else:
                    errorcode = ReturnCodes.SCPI_SerialNoResponse
                    result = 'the command intendedly no response'
            else:
                errorcode = ReturnCodes.SCPI_SerialNoInited
                result = f'serial port {port} was not initiated'
        except BaseException:  # serial.SerialException as e:
            errorcode = ReturnCodes.SCPI_SerialSendFail
            result = f'failed to send data over serial port {port}'
            logger.exception(f'failed to send data over serial port {port}')
        return errorcode, result

    def state(self, port=None):
        errorcode = ReturnCodes.Good
        if port is None:
            result = [{client['port']: client['state']} for client in self.clients]
            return errorcode, result
        try:
            cli = self.getcli(port)
            if cli is not None:
                ser_client = cli['client']
                result = "opened" if ser_client.isOpen() else 'closed'
            else:
                errorcode = ReturnCodes.SCPI_SerialListStateFail
                result = f'failed to list state of serial port {port} because it is not initiated'
        except BaseException:  # serial.SerialException as e:
            errorcode = ReturnCodes.SCPI_SerialReadStateException
            result = 'hit exception when read serial port % state' % port
            logger.exception(
                'hit exception when read serial port % state' %
                port)
        return errorcode, result


class SCPITcpClient(object):
    def __init__(self):
        self.clients = []

    def getcli(self, host_str):
        return next(
            (client for client in self.clients if host_str == client['host_str']),
            None,
        )

    def addcli(self, host_str):
        # host_str "tcp:127.0.0.1:80"
        host = host_str.split(':')[1]
        port = int(host_str.split(':')[2])
        client = socket(AF_INET, SOCK_STREAM)
        client.connect((host, port))
        client_param = {
            'host_str': host_str,
            'client': client,
            'state': 'opened'}
        self.clients.append(client_param)

    def open(self, host_str):
        errorcode = ReturnCodes.Good
        try:
            cli = self.getcli(host_str)
            if cli is None:
                self.addcli(host_str)
            elif cli['state'] == 'closed':
                host = host_str.split(':')[1]
                port = int(host_str.split(':')[2])
                client = socket(AF_INET, SOCK_STREAM)
                client.connect((host, port))
                cli['client'] = client
                cli['state'] = 'opened'
            result = f'connection {host_str} was opened'
        except BaseException:  # socket.error as e:
            errorcode = ReturnCodes.SCPI_TcpOpenException
            result = f'failed to create connection {host_str}'
            logger.exception(f'failed to create connection {host_str}')

        return errorcode, result

    def close(self, host_str):
        errorcode = ReturnCodes.Good

        try:
            cli = self.getcli(host_str)
            if cli is not None:
                cli['client'].close()
                cli['state'] = 'closed'
                result = f'socket connection {host_str} was closed'
            else:
                errorcode = ReturnCodes.SCPI_TcpCloseFail
                result = f'failed to close socket connection {host_str} because it is not exist'
        except BaseException:
            errorcode = ReturnCodes.SCPI_TcpCloseException
            result = f'failed to close connection {host_str}'
            logger.exception(f'failed to close connection {host_str}')

        return errorcode, result

    def send(self, host_str, data):
        errorcode = ReturnCodes.Good
        try:
            cli = self.getcli(host_str)
            if cli is not None:
                cli['client'].sendall(data.encode('ascii'))
                cli['client'].settimeout(1)
                recv = cli['client'].recv(8192)
                result = recv.decode('utf8')
            else:
                errorcode = ReturnCodes.SCPI_TcpNoInited
                result = f'failed to send data over socket connection {host_str} because it was not initiated'
        except BaseException:
            errorcode = ReturnCodes.SCPI_TcpSendException
            result = f"failed to send data over socket connection {host_str}, socket was {cli['state']}"
            logger.exception(
                f"failed to send data over socket connection {host_str}, socket was {cli['state']}"
            )
        return errorcode, result

    def state(self, host_str=None):
        errorcode = ReturnCodes.Good
        if host_str is None:
            result = [{client['host_str']: client['state']} for client in self.clients]
            return errorcode, result
        try:
            cli = self.getcli(host_str)
            if cli is not None:
                result = cli['state']
            else:
                errorcode = ReturnCodes.SCPI_TcpListStateFail
                result = f'failed to list state of socket connection {host_str} because it is not created'
        except BaseException:
            errorcode = ReturnCodes.SCPI_TcpReadStateException
            result = 'hit exception when read socket % state' % host_str
            logger.exception(
                'hit exception when read socket % state' %
                host_str)
        return errorcode, result


class SCPIPluginEntity(BasePluginEntity):
    def __init__(self, file_name):
        super(SCPIPluginEntity, self).__init__(file_name)


class SCPIPluginConfig(BasePluginConfig):
    def __init__(self, config_fp):
        super(SCPIPluginConfig, self).__init__(config_fp)


class SCPIPluginClient(BasePluginClient):
    def __init__(self, entity, config):
        super(SCPIPluginClient, self).__init__(entity, config)
        self.scpi_serial = SCPISerialClient()
        self.scpi_tcp = SCPITcpClient()

    def open(self, link, setting=None):
        if ('ser' in link):
            retcode, result = self.scpi_serial.open(link, setting)
        elif ('tcp' in link):
            retcode, result = self.scpi_tcp.open(link)
        return {'code': retcode, 'data': result}

    def close(self, link):
        if ('ser' in link):
            retcode, result = self.scpi_serial.close(link)
        elif ('tcp' in link):
            retcode, result = self.scpi_tcp.close(link)
        return {'code': retcode, 'data': result}

    def send(self, link, data):
        if ('ser' in link):
            retcode, result = self.scpi_serial.send(link, data)
        elif ('tcp' in link):
            retcode, result = self.scpi_tcp.send(link, data)
        return {'code': retcode, 'data': result}

    def state(self, link):
        if ('ser' in link):
            retcode, result = self.scpi_serial.state(link)
            return {'code': retcode, 'data': result}
        elif ('tcp' in link):
            retcode, result = self.scpi_tcp.state(link)
            return {'code': retcode, 'data': result}
        else:
            result = []
            sercode, ser_states = self.scpi_serial.state()
            if sercode == ReturnCodes.Good:
                result.append(ser_states)
            tcpcode, tcp_states = self.scpi_tcp.state()
            if tcpcode == ReturnCodes.Good:
                result.append(tcp_states)
            return {'code': ReturnCodes.Good, 'data': json.dumps(result)}


def plugin_main(*args, **kwargs):
    plugin_entity = SCPIPluginEntity(args[0])
    plugin_config = SCPIPluginConfig(args[1])
    plugin_client = SCPIPluginClient(plugin_entity, plugin_config)
    plugin_client.start()
