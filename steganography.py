from flask import *
from PIL import Image
import itertools
import os
import random
import zlib
import pyaes
import sys
import numpy as np

ALLOWED_EXTENSIONS = {'png', 'bmp'}

app = Flask(__name__)


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=["GET"])
def root():
	return render_template('index.html')


@app.route('/', methods=["POST"])
def root2():
	file = request.files['file']
	if file.filename == '':
		print('No selected file')
		return render_template('index.html', var1="No file Selected")
	if not (file and allowed_file(file.filename)):
		print("Invalid File")
		return render_template('index.html', var1="Invalid File")
	de_text = ""
	if request.form["btn"] == "Encode":
		key = request.form['enkey']
		text = request.form['inputString']
		output_file = request.form['output_image']
		encode(file, text, key, output_file)
	else:
		key = request.form['dekey']
		de_text = decode(file, key)
	return render_template('index.html', var1=de_text)


def encode(file, text, key, output_file):
	print(file.filename.split(".")[-1], type(file))
	pix, dimensions, im = initial(file)
	compressed_text = zlib.compress(text.encode('utf-8'))
	encrypted_text = initialize_aes(key).encrypt(compressed_text)
	binary_list = list(bin(int.from_bytes(encrypted_text, byteorder=sys.byteorder))[2:])
	length_of_encrypted = len(binary_list)
	permute = random_permutations(length_of_encrypted, dimensions[0], dimensions[1])
	length_of_encrypted_to_byte = length_of_encrypted.to_bytes(3, byteorder=sys.byteorder)
	pix[dimensions[0] - 1, dimensions[1] - 1] = tuple([length_of_encrypted_to_byte[0], length_of_encrypted_to_byte[1], length_of_encrypted_to_byte[2]])
	binary_length = length_of_encrypted - (length_of_encrypted % 3)

	i = j = 0
	for i in range(0, binary_length, 3):
		pixel = choose_permutation(permute, j)
		red_value = modify_pixel(pix, pixel, 0, binary_list[i])
		green_value = modify_pixel(pix, pixel, 1, binary_list[i + 1])
		blue_value = modify_pixel(pix, pixel, 2, binary_list[i + 2])
		pix[pixel[0], pixel[1]] = tuple([red_value, green_value, blue_value])
		j = j + 1

	i += 3
	pixel = choose_permutation(permute, j)
	red_value = pix[pixel[0], pixel[1]][0]
	green_value = pix[pixel[0], pixel[1]][1]
	blue_value = pix[pixel[0], pixel[1]][2]
	if i < length_of_encrypted:
		red_value = modify_pixel(pix, pixel, 0, binary_list[i])
	if (i + 1) < length_of_encrypted:
		green_value = modify_pixel(pix, pixel, 1, binary_list[i + 1])
	if (i + 2) < length_of_encrypted:
		blue_value = modify_pixel(pix, pixel, 2, binary_list[i + 2])

	pix[pixel[0], pixel[1]] = tuple([red_value, green_value, blue_value])

	im.save(output_file + "." + file.filename.split(".")[-1])


def decode(file, key):
	pix, dimensions, im = initial(file)
	last_pixel = pix[dimensions[0] - 1, dimensions[1] - 1]
	text_length = bytes([last_pixel[0]]) + bytes([last_pixel[1]]) + bytes([last_pixel[2]])
	text_length = int.from_bytes(text_length, byteorder=sys.byteorder)
	text_length2 = text_length // 3
	permute = random_permutations(text_length, dimensions[0], dimensions[1])
	text_length3 = 0
	if text_length % 3 != 0:
		text_length3 = text_length % 3
	pixels = ""
	for i in range(text_length2):
		pixel = choose_permutation(permute, i)
		part1 = format(pix[pixel[0], pixel[1]][0], 'b').zfill(8)[7:]
		pixels = pixels + part1
		part2 = format(pix[pixel[0], pixel[1]][1], 'b').zfill(8)[7:]
		pixels = pixels + part2
		part3 = format(pix[pixel[0], pixel[1]][2], 'b').zfill(8)[7:]
		pixels = pixels + part3
	pixel = choose_permutation(permute, i, 1)
	for j in range(text_length3):
		pixels = pixels + format(pix[pixel[0], pixel[1]][j], 'b').zfill(8)[7:]
	pixels = "0b" + pixels
	text = int(pixels, base=2)
	text = text.to_bytes(((text.bit_length() + 7) // 8) + 1, byteorder=sys.byteorder)
	text = initialize_aes(key).decrypt(text)
	text = zlib.decompress(text).decode('utf-8')
	return text


def initial(file):
	im = Image.open(file.filename)
	pix = im.load()
	dimensions = im.size
	return pix, dimensions, im


def random_permutations(length_of_encrypted, width, height):
	np.random.seed(400)
	all_permutations = np.array(np.meshgrid(range(width), range(height))).T.reshape(-1,2)
	np.random.shuffle(all_permutations)
	return all_permutations


def modify_pixel(pix, pixel, colour_value, binary_list):
	return int(format(pix[pixel[0], pixel[1]][colour_value], 'b').zfill(8)[:7] + binary_list, 2)


def initialize_aes(key):
	return pyaes.AESModeOfOperationCTR(key.encode('utf-8'))


def choose_permutation(permute, index, offset = 0):
	return permute[index + offset].tolist()


if __name__ == '__main__':
	app.run(debug=True)
