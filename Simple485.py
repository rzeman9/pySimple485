import time
import logging
logger = logging.getLogger('gate.Simple485')

SOH = b'\x01'
STX = b'\x02'
ETX = b'\x03'
EOT = b'\x04'
LF = b'\x10'
NUL = b'\x00'

LINE_READY_TIME = 10
MESSAGE_MAX_LEN = 255

millis = lambda: int(round(time.time() * 1000))

class Simple485:

  def __init__(self, serial, addr):
    logger.info('Init.')
    self.serial = serial
    self.addr = addr
    self.last_receive = millis()
    self.stat = 0
    self.first_nibble = True
    self.receivedMessages = []
    self.outputMessages = []
    self.incoming = 0
    
  def receive(self):
    while self.serial.in_waiting > 0:
        self.last_receive = millis()
        b = self.serial.read()
        if b == SOH:
          self.stat = 1
        elif self.stat == 0:
          continue
        elif self.stat == 1:
          if b == self.addr or b == NUL:
            self.stat += 1
            self.dst = b
          else:
            self.stat = 0
        elif self.stat == 2:
          self.src = b
          self.stat += 1
        elif self.stat == 3:
          self.ln = b[0]
          self.stat += 1
        elif self.stat == 4:
          if b == STX:
            self.stat+= 1
          else:
            self.stat = 0
          self.crc = self.dst[0] ^ self.src[0] ^ self.ln
          self.first_nibble = 1
          self.pos = 0
          self.buff = b''
        elif self.stat == 5:
          if (~(((b[0] << 4) & 240) | ((b[0] >> 4) & 15))) & 0xff == b[0]:
            if self.first_nibble:
              self.incoming = b[0] & 240
              self.first_nibble = 0
            else:
              self.first_nibble = 1
              self.incoming |= b[0] & 15
              self.buff += bytes([self.incoming])
              self.crc ^= self.incoming
          elif b == ETX:
            if len(self.buff) == self.ln:
              self.stat += 1
            else:
              self.stat = 0
          else:
            self.stat = 0
        elif self.stat == 6:
          if b[0] == self.crc:
            self.stat += 1
          else:
            self.stat = 0
        elif self.stat == 7:
          if b == EOT:
            m = (self.src, self.ln, self.buff)
            logger.debug("Received message: " + str(list(m)))
            self.receivedMessages.append(m)
            self.stat = 0
          else:
            self.stat = 0

  def send(self, dst, msg):
    if isinstance(msg, str):
      msg = msg.encode()
    if len(msg) > MESSAGE_MAX_LEN:
      msg = msg[0:MESSAGE_MAX_LEN-1]
    buff = LF + LF + LF + SOH + dst + self.addr + bytes([len(msg)]) + STX
    crc = self.addr[0] ^ dst[0] ^ len(msg)
    for i in range(0, len(msg)):
      crc ^= msg[i]
      b = msg[i] & 240
      b = b | (~(b >> 4) & 15)
      buff += bytes([b])
      b = msg[i] & 15
      b = b | ((~b << 4) & 240)
      buff += bytes([b])
    buff += ETX + bytes([crc]) + EOT + LF + LF
    logger.debug("Send append: " + str(buff))
    self.outputMessages.append(buff)
  
  def transmitt(self):
    logger.debug("Trying to transmit.")
    if millis() > self.last_receive + LINE_READY_TIME:
      while len(self.outputMessages) > 0:
        logger.debug("Sending message.")
        self.serial.write(self.outputMessages.pop(0))
    else:
      logger.debug("Port busy.")
    
  def loop(self):
    self.receive()
    self.transmitt()
  
  def received(self):
    return len(self.receivedMessages)
  
  def read(self):
    return self.receivedMessages.pop(0)