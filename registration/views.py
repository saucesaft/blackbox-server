import os

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from datetime import datetime
from hashlib import sha256
import json

from .create_password import create_password


PASSWORD = create_password()
FILE = '/media/blackbox/ARCH_202202/password.txt'


def read_usb(file_name : str, disk_name : str = '/dev/sda') -> str:
	"""
	Returns the string in the file file_name if the disk disk_name
	exists. Else, returns an empty string
	"""
	disk_exists : bool = os.path.exists(disk_name)
	if not disk_exists:
		return ''
	# else:
	with open(file_name, 'r', encoding='utf8') as f:
		return f.read().strip()
	
def error_response(msg : str) -> JsonResponse:
	return JsonResponse({
		'error' : msg
	})

def validate_usb():
	"""
	Returns a string or an http response
	"""
	# Check if the file exists
	try:
		usb : str = read_usb(FILE)
	except FileNotFoundError:
		return error_response('The USB is not mounted')
	# Check if the disk exists
	if not usb:
		return error_response('You need the USB to register')
	# Check if the password is correct
	elif usb != PASSWORD.strip():
		return error_response('The USB password is invalid')
	
	return usb
	
@csrf_exempt
def registration_view(request) -> JsonResponse:
	"""
	Only valid when request is POST
	Checks if the raspberry has the valid usb connected,
	and if so, sends a code as response
	"""
	# Check that POST is being used
	if request.method != 'POST':
		return error_response('Invalid method')

	usb = validate_usb()
	if not isinstance(usb, str):
		return usb
	# If everything is correct:
	curr_datetime : str = datetime.now().strftime('%y%m%d-%H%M%S')
	hash_ : str = sha256(bytes(usb + curr_datetime, 'utf8')).hexdigest()
	
	with open('password.txt', 'w', encoding='utf8') as f:
		f.write(hash_)
	
	return JsonResponse({
		'code' : hash_
	})


@method_decorator(csrf_exempt, name='dispatch')
class ConfirmationView(View):
	
	def request_error(self,
			msg='Invalid operation. Register again')-> HttpResponse:
		with open('password.txt', 'w', encoding='utf8') as f:
			f.write('')
		return error_response(msg)
	
	def post (self, request) -> HttpResponse:
		usb = validate_usb()
		if not isinstance(usb, str):
			return usb
		if not request.body:
			return self.request_error()
			
		data = json.loads(request.body)
		code = data.get('code')
		if not code:
			return self.request_error()
		# check that the code is the same as before
		with open('password.txt', 'r', encoding='utf8') as f:
			if f.read().strip() != code.strip():
				return self.request_error()
		# else (everything is correct):
		with open('confirmed', 'w') as f:
			# creates empty file
			pass
		return JsonResponse({
			'success' : True
		})
