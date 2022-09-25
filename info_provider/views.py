from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.generic.list import ListView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import smbus
import time

import json
from .models import PasswordKeeper
from multiprocessing import Process

# Create your views here.


# Define some device parameters
I2C_ADDR  = 0x27 # I2C device address
LCD_WIDTH = 16   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#Open I2C interface
bus = smbus.SMBus(1)

time.sleep(2)

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)
  
def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  # High bits
  bus.write_byte(I2C_ADDR, bits_high)
  lcd_toggle_enable(bits_high)

  # Low bits
  bus.write_byte(I2C_ADDR, bits_low)
  lcd_toggle_enable(bits_low)
  
def lcd_toggle_enable(bits):
  # Toggle enable
  time.sleep(E_DELAY)
  bus.write_byte(I2C_ADDR, (bits | ENABLE))
  time.sleep(E_PULSE)
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  time.sleep(E_DELAY)

def lcd_string(message,line):
  # Send string to display

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)


class PasswordNameListView(ListView):
	model = PasswordKeeper
	fields = ['name']
	
	def dispatch(self, request,*args, **kwargs):
		return super(PasswordNameListView, self).dispatch(request, 
			*args, **kwargs
		)
		
	def get_queryset(self):
		return self.model.objects.all()

	def get(self, request):
		queryset = self.get_queryset()
		return JsonResponse({'list' : [
			{
				'id'   : i.id,
				'name' : i.name,
				'type' : i.crypto_type,
			} for i in queryset]
		})

def run(msg : str):
	n = 16
	s = [msg[i:i+n] for i in range(0, len(msg), n) ]
	count = 0
	while True:	
		if count == len(s):
			count = 0
		lcd_string(s[count],LCD_LINE_1)
		count += 1
		time.sleep(5)

def start_lcd():
	lcd_string("hello", LCD_LINE_1)

process = Process(target=start_lcd)
process.start()

@method_decorator(csrf_exempt, name='dispatch')
class GetPassword(View):
	def post(self, request):
		data = request.body
		if not data:
			return JsonResponse({'error' : 'No object selected'})
		# else:
		id_ = json.loads(data).get('id')
		if not id_:
			return JsonResponse({'error' : 'No object selected'})
		obj = get_object_or_404(PasswordKeeper, pk=id_)
		private_key = obj.private_key
		public_key  = obj.public_key
		msg : str = f"Private key:{private_key}, Public key:{public_key}"
		global process
		process.terminate()
		process = Process(target=run, args=(msg,))
		process.start()
		
	
lcd_init()
		
