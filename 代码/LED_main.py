from machine import Pin, UART, PWM

import utime

utime.sleep(2)
uart = UART(1, 115200)
uart.init(115200, bits=8, parity=None, stop=1)


if __name__ == '__main__':
    while True:
        for i in range(0, 800, 5):
            utime.sleep(0.01)
            PWM(Pin(2), freq=800, duty=i)
        for i in range(0, 800, 5):
            utime.sleep(0.01)
            PWM(Pin(2), freq=800, duty=800 - i)




