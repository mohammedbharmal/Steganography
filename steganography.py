from flask import *

from PIL import Image
import itertools
import os
import random
import zlib
import pyaes
import sys

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
    print(request.form["btn"])
    de_text = ""
    if request.form["btn"] == "Encode":
        key = request.form['enkey']
        text = request.form['inputString']
        encode(file, text, key)
    else:
        key = request.form['dekey']
        de_text = decode(file, key)
    return render_template('index.html', var1=de_text)


def encode(file, text, key):
    permute, pix, dimensions, im = initial(file)
    compressed_text = compress_text(text)
    encrypted_text = encrypt_text(compressed_text, key)
    binary_text = bin(int.from_bytes(encrypted_text, byteorder=sys.byteorder))
    binary_text = binary_text[2:]
    binary_list = list(binary_text)
    length_of_encrypted = len(binary_list)
    length_of_encrypted_to_byte = length_of_encrypted.to_bytes(
        3, byteorder=sys.byteorder)
    pix[dimensions[0] - 1, dimensions[1] - 1] = tuple(
        [length_of_encrypted_to_byte[0], length_of_encrypted_to_byte[1], length_of_encrypted_to_byte[2]])
    j = 0
    for i in range(0, len(binary_list), 3):
        pixel = permute[j]
        if i < len(binary_list):
            red_value = int(
                format(pix[pixel[0], pixel[1]][0], 'b').zfill(8)[:7] + binary_list[i], 2)
        if (i + 1) < len(binary_list):
            green_value = int(format(pix[pixel[0], pixel[1]][1], 'b').zfill(8)[
                              :7] + binary_list[i + 1], 2)
        if (i + 2) < len(binary_list):
            blue_value = int(format(pix[pixel[0], pixel[1]][2], 'b').zfill(8)[
                             :7] + binary_list[i + 2], 2)
        pix[pixel[0], pixel[1]] = tuple([red_value, green_value, blue_value])
        j = j + 1
    im.save("6new.png")


def decode(file, key):
    permute, pix, dimensions, im = initial(file)
    last_pixel = pix[dimensions[0] - 1, dimensions[1] - 1]
    text_length = bytes([last_pixel[0]]) + bytes([last_pixel[1]]) + bytes([last_pixel[2]])
    text_length = int.from_bytes(text_length, byteorder=sys.byteorder)
    text_length2 = int(text_length / 3)
    text_length3 = 0
    if text_length % 3 != 0:
        text_length3 = text_length % 3
    pixels = ""
    for i in range(text_length2):
        pixel = permute[i]
        part1 = format(pix[pixel[0], pixel[1]][0], 'b').zfill(8)[7:]
        pixels = pixels + part1
        part2 = format(pix[pixel[0], pixel[1]][1], 'b').zfill(8)[7:]
        pixels = pixels + part2
        part3 = format(pix[pixel[0], pixel[1]][2], 'b').zfill(8)[7:]
        pixels = pixels + part3
    pixel = permute[i + 1]
    for j in range(text_length3):
        pixels = pixels + format(pix[pixel[0], pixel[1]][j], 'b').zfill(8)[7:]
    pixels = "0b" + pixels
    text = int(pixels, base=2)
    text = text.to_bytes(
        ((text.bit_length() + 7) // 8) + 1, byteorder=sys.byteorder)
    text = decrypt_text(text, key)
    text = decompress_text(text)
    return text


def initial(file):
    im = Image.open(file.filename)
    print(file.filename)
    pix = im.load()
    dimensions = im.size
    random.seed(400)
    w = random.sample(range(dimensions[0]), dimensions[0])
    h = random.sample(range(dimensions[1]), dimensions[1])
    permute = []
    for r in itertools.product(w, h):
        permute.append([r[0], r[1]])
    random.shuffle(permute)
    return permute, pix, dimensions, im


def encryption(key):
    key = key.encode('utf-8')
    return pyaes.AESModeOfOperationCTR(key)


def compress_text(x):
    return zlib.compress(x.encode('utf-8'))


def encrypt_text(x, key):
    aes = encryption(key)
    return aes.encrypt(x)


def decompress_text(x):
    return zlib.decompress(x).decode('utf-8')


def decrypt_text(x, key):
    aes = encryption(key)
    return aes.decrypt(x)


if __name__ == '__main__':
    app.run(debug=True)
