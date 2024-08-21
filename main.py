import uasyncio as asyncio
import usocket as socket
import machine
import time
import ntptime
ntptime.settime()
rtc = machine.RTC()


# GPIO pin assignments
GPIO_2 = machine.Pin(2, machine.Pin.OUT)
GPIO_4 = machine.PWM(machine.Pin(4))
GPIO_5 = machine.PWM(machine.Pin(5))
GPIO_4.freq(1000)
GPIO_5.freq(1000)


# HTTP server configuration
ADDR = ('0.0.0.0', 80)

global GPIO_4_STATUS
GPIO_4_STATUS = 0
global GPIO_5_STATUS
GPIO_5_STATUS = 0
global OFFTARGET
OFFTARGET = None


def set_state(state):
    GPIO_2.value(state['GPIO_2'])
    GPIO_4.duty(state['GPIO_4'])
    GPIO_5.duty(state['GPIO_5'])

def handle_request(request):
    global GPIO_4_STATUS
    global GPIO_5_STATUS
    global OFFTARGET
    global rtc
    if request.startswith('GET /?'):
        try:
            query = request.split(' ')[1].split('?')[1]
            params = query.split('&')
            for param in params:
                key, value = param.split('=')
                if key == 'gpio4':
                    GPIO_4_STATUS = int(value)
                if key == 'gpio5':
                    GPIO_5_STATUS = int(value)
                if key == 'shutdown':
                    if value == "":
                        OFFTARGET = None
                    else:
                        OFFTARGET = time.mktime(rtc.datetime()) + (int(value))
            GPIO_4.duty(GPIO_4_STATUS)
            print(GPIO_4_STATUS)
            GPIO_5.duty(GPIO_5_STATUS)
            print(GPIO_5_STATUS)
            print("offtarget is: {}".format(OFFTARGET))
            return '{{"4":{},"5":{},"localTime":"{}","offTarget":"{}"}}'.format(GPIO_4_STATUS,GPIO_5_STATUS,time.mktime(rtc.datetime()),OFFTARGET)
        except Exception as e:
            print('Error handling GET request:', e)
            return 'Error handling GET request'
    elif request.startswith('GET /state'):
        try:
            return '{{"4":{},"5":{},"localTime":{},"offTarget":{}}}'.format(GPIO_4_STATUS,GPIO_5_STATUS,time.mktime(rtc.datetime()),OFFTARGET)
        except Exception as e:
            print('Error handling GET request:', e)
            return 'Error handling GET request'
    else:
        try:
            with open('index.html', 'r') as f:
                html_response = f.read()
                return html_response
        except Exception as e:
            print('Error reading HTML file:', e)
            return 'Error reading HTML file'

async def handle_client(reader, writer):
    print("client connected")
    data = await reader.read(1024)
    #print(data)
    request = data.decode('utf-8')
    response = handle_request(request)
    #print(response)
    writer.write(response.encode('utf-8'))
    await writer.drain()
    await writer.wait_closed()
    print("disconnected")

async def main():
    asyncio.create_task(checkTimer())
    while True:
        print('Setting up webserver...')
        server = await asyncio.start_server(handle_client, ADDR[0], ADDR[1])
        async with server:
            while True: 
                await asyncio.sleep(300)


async def checkTimer():
    global OFFTARGET
    global rtc
    while True:
        await asyncio.sleep(15)
        print("checking timer...")
        if OFFTARGET != None:
            if OFFTARGET < time.mktime(rtc.datetime()):
                # Timer expired, set GPIO duty cycles to 0
                GPIO_4.duty(0)
                GPIO_5.duty(0)
                OFFTARGET = None

# Run the main coroutine
                
asyncio.run(main())
