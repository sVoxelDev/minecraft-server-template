#!/usr/bin/env python3
import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import socket
import struct
import subprocess
import time
import zlib

loader = importlib.machinery.SourceFileLoader('status_protocol', str(Path(__file__).resolve().parents[1] / 'scripts/status'))
protocol = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
loader.exec_module(protocol)


def string(value):
    encoded = value.encode()
    return protocol.varint(len(encoded)) + encoded


class Client:
    def __init__(self, host, port):
        self.connection = socket.create_connection((host, port), timeout=10)
        self.threshold = None

    def send(self, packet, payload=b''):
        data = protocol.varint(packet) + payload
        if self.threshold is not None:
            data = protocol.varint(len(data)) + zlib.compress(data) if len(data) >= self.threshold else b'\x00' + data
        self.connection.sendall(protocol.varint(len(data)) + data)

    def receive(self):
        length = protocol.read_varint(self.connection)
        if length > 8 * 1024 * 1024:
            raise ValueError('Packet exceeds validation client limit.')
        data = protocol.read_exact(self.connection, length)
        if self.threshold is not None:
            uncompressed, offset = decode_varint(data)
            data = zlib.decompress(data[offset:]) if uncompressed else data[offset:]
        packet, offset = decode_varint(data)
        return packet, data[offset:]


def decode_varint(data):
    value = 0
    for offset, byte in enumerate(data[:5]):
        value |= (byte & 127) << (offset * 7)
        if not byte & 128:
            return value, offset + 1
    raise ValueError('Invalid VarInt.')


def login(args):
    supported = {'26.2': 776}
    if args.version not in supported:
        raise ValueError('Unsupported validation client protocol for Minecraft ' + args.version + '. Update the client packet mapping before validating this version.')
    client = Client(args.host, args.port)
    client.send(0, protocol.varint(supported[args.version]) + string(args.host) + struct.pack('>H', args.port) + b'\x02')
    identity = bytearray(hashlib.md5(('OfflinePlayer:' + args.username).encode()).digest())
    identity[6] = (identity[6] & 15) | 48
    identity[8] = (identity[8] & 63) | 128
    client.send(0, string(args.username) + identity)
    state = 'login'
    deadline = time.monotonic() + 25
    packets = []
    try:
        while time.monotonic() < deadline:
            packet, data = client.receive()
            packets.append([state, packet])
            if state == 'login':
                if packet == 0:
                    return {'denied': True, 'reason': data.decode(errors='replace'), 'packets': packets}
                if packet == 1:
                    return {'denied': True, 'reason': 'authentication_required', 'packets': packets}
                if packet == 3:
                    client.threshold = decode_varint(data)[0]
                elif packet == 4:
                    message, offset = decode_varint(data)
                    client.send(2, protocol.varint(message) + b'\x00')
                elif packet == 2:
                    client.send(3)
                    state = 'configuration'
                    client.send(0, string('en_us') + b'\x04\x00\x01\x7f\x01\x00\x01\x00')
            elif state == 'configuration':
                if packet == 2:
                    return {'denied': True, 'reason': data.decode(errors='replace'), 'packets': packets}
                if packet == 14:
                    client.send(7, b'\x00')
                elif packet == 4:
                    client.send(4, data)
                elif packet == 5:
                    client.send(5, data)
                elif packet == 19:
                    client.send(9)
                elif packet == 3:
                    client.send(3)
                    state = 'play'
                    if args.verify_cli:
                        end = time.monotonic() + 8
                        while time.monotonic() < end:
                            result = subprocess.run([str(args.verify_cli), 'command', 'list'], text=True,
                                                    capture_output=True, timeout=5)
                            if args.username in result.stdout:
                                return {'play': True, 'backend_list': result.stdout, 'packets': packets}
                            time.sleep(0.2)
                        raise ValueError('Client configured but absent from backend RCON list.')
                    return {'play': True, 'packets': packets}
        raise TimeoutError('Login deadline expired.')
    finally:
        client.connection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Minimal 26.2 validation client. No account login or gameplay automation.')
    parser.add_argument('--version', default=dict(line.split('=', 1) for line in (Path(__file__).resolve().parents[1] / 'versions.env').read_text().splitlines() if line)['PAPER_VERSION'])
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--username', default='ForwardProof')
    parser.add_argument('--expect', choices=['play', 'deny', 'auth'], default='play')
    parser.add_argument('--verify-cli', type=Path)
    args = parser.parse_args()
    try:
        result = login(args)
        print(json.dumps(result))
        passed = result.get('play') if args.expect == 'play' else result.get('denied')
        if args.expect == 'auth':
            passed = result.get('reason') == 'authentication_required'
        raise SystemExit(0 if passed else 1)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({'error': str(error)}))
        raise SystemExit(1)
