from PIL import Image
import os

src = r"d:\ALLProgrammes\glint\src\glint\assets\logo.png"
dst = r"d:\ALLProgrammes\glint\src\glint\assets\logo.ico"

try:
    img = Image.open(src)
    img.save(dst, format='ICO', sizes=[(256, 256)])
    print(f"Successfully converted {src} to {dst}")
except Exception as e:
    print(f"Error converting image: {e}")
