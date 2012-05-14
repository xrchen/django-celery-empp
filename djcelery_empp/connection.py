import socket
import datetime
import hashlib
import struct
from itertools import izip

from django.conf import settings


HOST = settings.SMS_HOST
PORT = settings.SMS_PORT
ACCOUNT = settings.SMS_ACCOUNT
PASSWORD = settings.SMS_PASSWORD

class SMSException(Exception):
    pass

class CommandID ():
    EMPP_CONNECT                = 0x00000001
    EMPP_CONNECT_RESP           = 0x80000001
    EMPP_TERMINATE              = 0x00000002
    EMPP_TERMINATE_RESP         = 0x80000002
    EMPP_SUBMIT                 = 0x00000004
    EMPP_SUBMIT_RESP            = 0x80000004
    EMPP_DELIVER                = 0x00000005
    EMPP_DELIVER_RESP           = 0x80000005
    EMPP_ACTIVE_TEST            = 0x00000008
    EMPP_ACTIVE_TEST_RESP       = 0x80000008
    EMPP_INTRINTSEARCHMSG       = 0x00000010
    EMPP_INTRINTSEARCHMSG_RESP  = 0x80000010
    EMPP_SYNCADDRBOOK           = 0x00000011
    EMPP_SYNCADDRBOOK_RESP      = 0x80000011
    EMPP_CHANGEPASS             = 0x00000012
    EMPP_CHANGEPASS_RESP        = 0x80000012
    EMPP_QUESTION               = 0x00000013
    EMPP_QUESTION_RESP          = 0x80000013
    EMPP_ANSWER                 = 0x00000014
    EMPP_ANSWER_RESP            = 0x80000014
    EMPP_REQNOTICE              = 0x00000015
    EMPP_REQNOTICE_RESP         = 0x80000015
    EMPP_SUBMIT2                = 0x00000016
    EMPP_UNAUTHORIZATION        = 0x80000017
    EMPP_INTRINTMSGSTATE        = 0x00000018
    EMPP_INTRINTMSGSTATE_RESP   = 0x80000018

class EMPPObject(object):
    _format = ''
    _field_list = []

    @property
    def size(self):
        return struct.calcsize(self._format)

    def pack(self):
        fields = [getattr(self, field_name) for field_name in self._field_list]
        return struct.pack(self._format, *fields)

    def unpack(self, data):
        for key, value in izip(self._field_list, \
                               struct.unpack(self._format, data)):
            setattr(self, key, value)

    def __repr__(self):
        return self.__class__.__name__ + '\n' + \
            '\n'.join('%s: %s' % (field_name, getattr(self, field_name)) \
                      for field_name in self._field_list)

class MessageHeader(EMPPObject):
    _format = '!3L'
    _field_list = ['total_length', 'command_id', 'sequence_id']

class ConnectBody(EMPPObject):
    command_id = CommandID.EMPP_CONNECT

    _format = '!21s16sBL'
    _field_list = ['account_id', 'authenticator_source', 'version', 'timestamp']

    def __init__(self):
        self.account_id = ACCOUNT
        now = datetime.datetime.now()
        m = hashlib.md5()
        m.update(ACCOUNT)
        m.update('\x00' * 9)
        m.update(PASSWORD)
        m.update(now.strftime('%m%d%H%M%S'))
        self.authenticator_source = m.digest()
        self.version = 1 << 4 | 0
        self.timestamp = now.month * 100000000 + now.day * 1000000 \
            + now.hour * 10000 + now.minute * 100 + now.second

class ConnectRespBody(EMPPObject):
    command_id = CommandID.EMPP_CONNECT_RESP

    _format = '!L16sBL'
    _field_list = ['status', 'authenticator_esm', 'version', 'ability']

class SubmitBody(EMPPObject):
    command_id = CommandID.EMPP_SUBMIT

    _field_list = ['msg_id', 'pk_total', 'pk_number', 'registered_delivery',
                   'msg_fmt', 'valid_time', 'at_time', 'dest_usr_tl',
                   'dest_terminal_id', 'msg_length', 'msg_content',
                   'msg_src', 'src_id', 'service_id', 'link_id', 'msg_level',
                   'fee_user_type', 'fee_terminal_id', 'fee_terminal_type',
                   'tp_pid', 'tp_udhi', 'fee_type', 'fee_code',
                   'dest_terminal_type']

    def __init__(self, receiver, message, msg_seq, seg_total, seg_seq,
                 delivery_report = False):
        msg_encode = '\x05\x00\x03' \
            + struct.pack('!3B', msg_seq, seg_total, seg_seq) \
            + message.encode('utf_16_be')
        self._format = '!10sBBBB17s17sL32sB%ds21s21s10s20sBB32sBBB2s6sB' \
            % len(msg_encode)

        self.msg_id = ''
        self.pk_total = seg_total
        self.pk_number = seg_seq
        self.registered_delivery = delivery_report
        self.msg_fmt = 8
        self.valid_time = ''
        self.at_time = ''
        self.dest_usr_tl = 1
        self.dest_terminal_id = receiver.encode('ascii')
        self.msg_length = len(msg_encode)
        self.msg_content = msg_encode
        self.msg_src = ''
        self.src_id = ACCOUNT
        self.service_id = ACCOUNT[0 : 10]
        self.link_id = ''
        self.msg_level = 1
        self.fee_user_type = 2
        self.fee_terminal_id = ''
        self.fee_terminal_type = 1
        self.tp_pid = 0
        self.tp_udhi = 1
        self.fee_type = '01'
        self.fee_code = '0'
        self.dest_terminal_type = 0

class SubmitRespBody(EMPPObject):
    command_id = CommandID.EMPP_SUBMIT_RESP

    _format = '!10sL'
    _field_list = ['msg_id', 'result']

class ActiveTestBody(EMPPObject):
    command_id = CommandID.EMPP_ACTIVE_TEST

class ActiveTestRespBody(EMPPObject):
    command_id = CommandID.EMPP_ACTIVE_TEST_RESP

    _format = '!B'
    _field_list = ['reserved']

class TerminateBody(EMPPObject):
    command_id = CommandID.EMPP_TERMINATE

class TerminateRespBody(EMPPObject):
    command_id = CommandID.EMPP_TERMINATE_RESP

def sequence_generator(max_value):
    while True:
        i = 1
        while i <= max_value:
            yield i
            i += 1

def get_body_class(command_id):
    for klass in [ConnectRespBody, SubmitRespBody, ActiveTestRespBody,
                  TerminateBody]:
        if klass.command_id == command_id:
            return klass
    raise ValueError('unknown command id %d' % command_id)

class Connection(object):
    BUF_SIZE = 4096
    MAX_MESSAGE_SEGMENTS = 10
    SINGLE_MESSAGE_SIZE = 67

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer = ''
        self.package_id_sequence = sequence_generator(0xffffffff)
        self.message_id_sequence = sequence_generator(0xff)

    def open(self):
        self.socket.connect((HOST, PORT))
        self._send_single_packet(ConnectBody())
        resp = self._receive_command([ConnectRespBody.command_id])
        if resp.status == 0 or resp.status == 20000:
            return True
        else:
            raise SMSException('connection failed with status %s'
                               % resp.status)

    def close(self):
        self._send_single_packet(TerminateBody())
        self.socket.close()

    def send_sms(self, receiver, content):
        segments = self._split_message(content)
        if len(segments) > self.MAX_MESSAGE_SEGMENTS:
            raise SMSException('content too long')
        need_ack = set()
        for (seg_id, seg_content) in izip(
                sequence_generator(self.MAX_MESSAGE_SEGMENTS),
                segments):
            body = SubmitBody(receiver, seg_content,
                              self.message_id_sequence.next(),
                              len(segments), seg_id)
            self._send_single_packet(body)
            need_ack.add(body.header.sequence_id)
        while need_ack:
            body = self._receive_command([SubmitRespBody.command_id])
            if body.result == 0:
                need_ack.remove(body.header.sequence_id)
            else:
                raise SMSException('submit resp return %s' % body.result)

    def is_alive(self):
        try:
            self._send_single_packet(ActiveTestBody())
            self._receive_command([ActiveTestRespBody.command_id])
            return True
        except:
            return False

    def _serialize_packet(self, body):
        header = MessageHeader()
        header.total_length = header.size + body.size
        header.command_id = body.command_id
        header.sequence_id = self.package_id_sequence.next()
        body.header = header
        return header.pack() + body.pack()

    def _split_message(self, content):
        segments = []
        while content:
            segments.append(content[: self.SINGLE_MESSAGE_SIZE])
            content = content[self.SINGLE_MESSAGE_SIZE: ]
        return segments

    def _send_single_packet(self, body):
        try:
            data = self._serialize_packet(body)
            self.socket.send(data)
        except Exception as e:
            raise SMSException('socket sending error, caused by:\n%s' % e)

    def _parse_single_packet(self):
        header = MessageHeader()
        if header.size > len(self.buffer):
            return
        header.unpack(self.buffer[: header.size])
        if header.total_length > len(self.buffer):
            return
        body = get_body_class(header.command_id)()
        body.unpack(self.buffer[header.size: header.total_length])
        self.buffer = self.buffer[header.total_length: ]
        body.header = header
        return body

    def _receive_command(self, accept_command):
        while True:
            body = self._parse_single_packet()
            if body and body.command_id in accept_command:
                return body
            data = self.socket.recv(self.BUF_SIZE)
            if data:
                self.buffer += data
            else:
                raise SMSException('remote connection closed')

def get_connection():
    c = Connection()
    c.open()
    return c
