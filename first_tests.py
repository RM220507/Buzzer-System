from machine import Pin

btn = Pin(14, Pin.IN, Pin.PULL_DOWN)

def handler(pin):
    print(type(pin))
    
btn.irq(trigger = Pin.IRQ_RISING, handler=handler)

while True:
    continue