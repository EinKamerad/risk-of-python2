import socket
import struct
import threading
import json
import time
from config import ctx

BASE_PORT = 27777
DISCOVERY_PORT = 27788
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def get_local_ip():
    """Определяет локальный IP-адрес компьютера в сети LAN"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def encode_room_code(ip_str, port=BASE_PORT):
    """Кодирует IPv4 и смещение порта в короткий буквенно-цифровой код комнаты"""
    try:
        ip_int = struct.unpack('!I', socket.inet_aton(ip_str))[0]
    except Exception:
        ip_int = struct.unpack('!I', socket.inet_aton('127.0.0.1'))[0]
    offset = max(0, min(15, port - BASE_PORT))
    val = (ip_int << 4) | offset
    chars = []
    while val > 0:
        val, rem = divmod(val, 36)
        chars.append(ALPHABET[rem])
    raw = ''.join(reversed(chars)) or '0'
    if len(raw) > 3:
        return f"{raw[:-3]}-{raw[-3:]}"
    return raw


def decode_room_code(code_str):
    """Декодирует код комнаты (или прямой IP) обратно в (ip, port)"""
    clean = code_str.strip().upper().replace(' ', '')
    if not clean:
        return '127.0.0.1', BASE_PORT

    # Поддержка прямого ввода IP или IP:PORT
    if '.' in clean:
        if ':' in clean:
            host, p_str = clean.split(':', 1)
            return host, int(p_str)
        return clean, BASE_PORT

    clean = clean.replace('-', '')
    val = 0
    for ch in clean:
        if ch not in ALPHABET:
            raise ValueError("Неверный символ в коде комнаты")
        val = val * 36 + ALPHABET.index(ch)

    offset = val & 0xF
    ip_int = val >> 4
    ip_str = socket.inet_ntoa(struct.pack('!I', ip_int))
    return ip_str, BASE_PORT + offset


class NetworkManager:
    def __init__(self):
        ctx.net = self
        self.mode = None  # None, 'host', 'client'
        self.my_id = 'host'
        self.room_code = ''
        self.host_ip = get_local_ip()
        self.port = BASE_PORT
        self.connected = False

        self.server_sock = None
        self.client_sock = None
        self.clients = {}          # pid -> socket (только на хосте)
        self.lock = threading.Lock()
        self.inbox = []            # Очередь входящих пакетов для главного потока Ursina
        self.discovered_rooms = {} # code -> {ip, port, time}

        self.running = True
        self._start_lan_listener()

    def _start_lan_listener(self):
        """Слушает UDP-маяки комнат в локальной сети"""
        def listen_loop():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(('', DISCOVERY_PORT))
                sock.settimeout(1.0)
            except Exception:
                return
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    msg = json.loads(data.decode('utf-8'))
                    if msg.get('magic') == 'ROR2_LAN':
                        code = msg['code']
                        self.discovered_rooms[code] = {
                            'ip': addr[0] if addr[0] != '0.0.0.0' else msg.get('ip', '127.0.0.1'),
                            'port': msg.get('port', BASE_PORT),
                            'code': code,
                            'time': time.time()
                        }
                except Exception:
                    pass
        threading.Thread(target=listen_loop, daemon=True).start()

    def host_room(self):
        """Создаёт комнату и запускает TCP-сервер + UDP-анонсер"""
        self.stop_session()
        self.host_ip = get_local_ip()
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        bound = False
        for offset in range(16):
            try:
                self.port = BASE_PORT + offset
                self.server_sock.bind(('0.0.0.0', self.port))
                bound = True
                break
            except Exception:
                continue

        if not bound:
            return False, "Не удалось занять сетевой порт"

        self.server_sock.listen(4)
        self.mode = 'host'
        self.my_id = 'host'
        self.connected = True
        self.room_code = encode_room_code(self.host_ip, self.port)

        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        return True, self.room_code

    def _broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.mode == 'host' and self.connected:
            payload = json.dumps({
                'magic': 'ROR2_LAN',
                'code': self.room_code,
                'ip': self.host_ip,
                'port': self.port
            }).encode('utf-8')
            for target in ('<broadcast>', '127.0.0.1'):
                try:
                    sock.sendto(payload, (target, DISCOVERY_PORT))
                except Exception:
                    pass
            time.sleep(1.0)
        sock.close()

    def _accept_loop(self):
        next_idx = 2
        while self.mode == 'host' and self.connected:
            try:
                conn, addr = self.server_sock.accept()
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                pid = f"p{next_idx}"
                next_idx += 1
                with self.lock:
                    self.clients[pid] = conn

                # Отправляем клиенту его ID и текущее состояние комнаты
                welcome = {'type': 'welcome', 'player_id': pid, 'room_code': self.room_code}
                self._send_json(conn, welcome)
                with self.lock:
                    self.inbox.append({'type': 'client_joined', 'player_id': pid})

                threading.Thread(target=self._client_recv_loop, args=(conn, pid), daemon=True).start()
            except Exception:
                break

    def join_by_code(self, code_str):
        """Подключается к хосту по коду комнаты или IP"""
        try:
            ip, port = decode_room_code(code_str)
        except Exception as e:
            return False, f"Ошибка кода: {e}"
        return self.join_direct(ip, port, code_str.strip().upper())

    def join_lan_auto(self):
        """Подключается к первой найденной в LAN комнате"""
        now = time.time()
        active = [r for r in self.discovered_rooms.values() if now - r['time'] < 5.0]
        if not active:
            # Пробуем локальный хост на случай запуска двух окон на одном ПК
            return self.join_direct('127.0.0.1', BASE_PORT, encode_room_code(get_local_ip(), BASE_PORT))
        room = active[0]
        return self.join_direct(room['ip'], room['port'], room['code'])

    def join_direct(self, ip, port, display_code=''):
        self.stop_session()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(3.5)
            sock.connect((ip, port))
            sock.settimeout(None)
        except Exception as e:
            return False, f"Не удалось подключиться ({ip}:{port})"

        self.client_sock = sock
        self.mode = 'client'
        self.connected = True
        self.room_code = display_code or encode_room_code(ip, port)
        threading.Thread(target=self._client_recv_loop, args=(sock, 'host'), daemon=True).start()
        return True, self.room_code

    def _client_recv_loop(self, sock, sender_id):
        buffer = ""
        while self.connected:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8', errors='ignore')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line.strip():
                        continue
                    msg = json.loads(line)
                    if self.mode == 'host':
                        msg['_sender'] = sender_id
                        # Ретранслируем пакеты клиента остальным клиентам
                        self.broadcast(msg, exclude_pid=sender_id)
                    with self.lock:
                        self.inbox.append(msg)
            except Exception:
                break

        if self.mode == 'host':
            with self.lock:
                self.clients.pop(sender_id, None)
                self.inbox.append({'type': 'player_left', 'player_id': sender_id})
            self.broadcast({'type': 'player_left', 'player_id': sender_id})
        else:
            with self.lock:
                self.inbox.append({'type': 'disconnected'})
            self.connected = False

    def _send_json(self, sock, data):
        try:
            raw = (json.dumps(data) + '\n').encode('utf-8')
            sock.sendall(raw)
            return True
        except Exception:
            return False

    def broadcast(self, data, exclude_pid=None):
        if not self.connected:
            return
        if self.mode == 'host':
            dead = []
            with self.lock:
                items = list(self.clients.items())
            for pid, sock in items:
                if pid == exclude_pid:
                    continue
                if not self._send_json(sock, data):
                    dead.append(pid)
            if dead:
                with self.lock:
                    for pid in dead:
                        self.clients.pop(pid, None)
        elif self.mode == 'client' and self.client_sock:
            self._send_json(self.client_sock, data)

    def poll_messages(self):
        with self.lock:
            msgs = list(self.inbox)
            self.inbox.clear()
        return msgs

    def stop_session(self):
        self.connected = False
        self.mode = None
        with self.lock:
            for s in self.clients.values():
                try:
                    s.close()
                except Exception:
                    pass
            self.clients.clear()
            self.inbox.clear()
        if self.client_sock:
            try:
                self.client_sock.close()
            except Exception:
                pass
            self.client_sock = None
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
            self.server_sock = None