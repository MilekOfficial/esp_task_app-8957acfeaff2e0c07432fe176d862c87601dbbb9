import network, urequests, machine, time

# ==== CONFIG ====
WIFI_SSID = 'Netcom_Wifi'
WIFI_PASS = '123456789'
FLASK_URL = 'http://frog01-40924.wykr.es/api/tasks'  # ← update to your PC’s LAN IP
BUTTON_PIN = 0  # change if needed
LED_PIN = 2  # Built-in LED on many ESP32 boards
# ================

# Connect to Wi-fi
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(WIFI_SSID, WIFI_PASS)
while not sta.isconnected():
    time.sleep(1)
print('WiFi ok:', sta.ifconfig())

# Setup button and LED
btn = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
led = machine.Pin(LED_PIN, machine.Pin.OUT)

def send_task(pin):
    try:
        res = urequests.post(FLASK_URL, json={"task": "Task done from ESP32"})
        print('Sent:', res.text)
        res.close()
        # Blink LED on success
        for _ in range(2):
            led.value(1)  # Turn on
            time.sleep(0.1)
            led.value(0)  # Turn off
            time.sleep(0.1)
            led.value(1)  # Turn on
            time.sleep(0.1)
            led.value(0)  # Turn off
            time.sleep(0.1)
    except Exception as e:
        print('Error:', e)

# Debounce and IRQ
last = 0
def irq_handler(pin):
    global last
    now = time.ticks_ms()
    if time.ticks_diff(now, last) > 500:
        send_task(pin)
        last = now

btn.irq(trigger=machine.Pin.IRQ_FALLING, handler=irq_handler)

# Keep alive
while True:
    send_task(1)
    time.sleep(10)
