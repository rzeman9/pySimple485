import serial
import Simple485

SERIALPORT = "COM13"
BAUDRATE = 9600
ADDR = b'\x1b'

ser = serial.Serial()
ser.port = SERIALPORT
ser.baudrate = BAUDRATE

try:
  ser.open()
except serial.SerialException as e:
  print('Could not open serial port {}: {}\n'.format(ser.name, e))
  exit(1)

rs485 = Simple485.Simple485(ser, ADDR)

while 1:
  try:
    rs485.loop()
    while rs485.received() > 0:
      m = rs485.read()
      src = m[0]
      ln = m[1]
      msg = m[2]
      print("Received " + str(ln) + " from " + str(src))
      print(msg)
      rs485.send(src, "ACQ")
  except KeyboardInterrupt:
    print("\nClosing")
    ser.close()
    exit(0)
