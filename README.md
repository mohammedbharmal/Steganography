# Steganography

This is a very simple implementation of a steganography algorithm. It is only compatible with text. A web interface is provided using flask. This algorithm also compresses the text before encrypting it using AES and encoding it in the image. This ensures that more text can be stored in an image without losing much quality. A 128-bit key is used.

## Requirements

1. Flask
2. Pillow
3. zlib
4. pyaes
5. NumPy
