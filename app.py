from flask import Flask, redirect, render_template, request, send_file, url_for
from PIL import Image, ImageFont, ImageDraw
import csv
import os
import zipfile
from io import BytesIO

import shutil

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


app = Flask(__name__)

# Global Variables
FONT_FILE = ImageFont.truetype('static/font/GreatVibes-Regular.ttf', 180)
FONT_FILE2 = ImageFont.truetype('static/font/font4.ttf', 60)
FONT_FILE3 = ImageFont.truetype('static/font/lemonmilk.otf', 55)
FONT_FILE4 = ImageFont.truetype('static/font/font4.ttf', 50)
FONT_FILE5 = ImageFont.truetype('static/font/Poppins-Light.otf', 50)
FONT_COLOR = "#FFFFFF"
TEMPLATE_PATH = 'static/template2.png'
OUTPUT_DIR = 'static/out/'
OUTPUT_CERTIFICATE = 'static/outputcertificate/'


@app.route('/')
def landing():
    return render_template('landing.html')
@app.route('/index', methods=['GET', 'POST'])
def index():
    global FONT_COLOR
    global TEMPLATE_PATH
    if request.method == 'POST':
        if 'file' not in request.files and 'logo' not in request.files:
            return render_template('index.html', error='No file part')
        
        hidden_value = request.form['template_index']
        TEMPLATE_PATH = 'static/template' + hidden_value + '.png'

        if hidden_value in ['1', '5', '6', '7']:
            FONT_COLOR = "#000000"
        else:
            FONT_COLOR = "#FFFFFF"

        print(hidden_value)
        print(FONT_COLOR)


        if 'file' in request.files:
            file = request.files['file']

            if file.filename == '':
                return render_template('index.html', error='No selected file')

            csv_filename = 'names.csv'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], csv_filename))
            delete_everything_inside_directory(OUTPUT_DIR)
            generate_certificates(csv_filename)
            zip_path = create_zip()
            return render_template('index.html', zip_path=zip_path)

        if 'logo' in request.files:
            logo = request.files['logo']
            title = request.form['title']
            name = request.form['name']
            subtitle = request.form['subtitle']
            description = request.form['description']
            sign = request.files['sign']
            signer = request.form['signer_name']
            delete_everything_inside_directory(OUTPUT_DIR)
            make_certificate(name, description, title, subtitle, signer, logo, sign)
            zip_path = create_zip()
            return render_template('index.html', zip_path=zip_path)
    
    return render_template('index.html')


def delete_everything_inside_directory(directory):
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            delete_everything_inside_directory(item_path)
            os.rmdir(item_path)

def textsize(text, font):
    '''Function to calculate the size of the text'''

    im = Image.new(mode="RGB", size=(0, 0))
    draw = ImageDraw.Draw(im)
    bbox = draw.textbbox((0, 0), text=text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height

def split_string_by_length(text, max_length):
    words = text.split()
    result = []
    current_part = ''
    
    for word in words:
        if len(current_part + ' ' + word) <= max_length:
            current_part += ' ' + word if current_part else word
        else:
            result.append(current_part.strip())
            current_part = word
    
    if current_part:
        result.append(current_part.strip())
    
    return result

def make_certificate(name,Description,title,subtitle,signer,logo=None,sign=None):
    '''Function to save certificates as a .pdf file'''

    # Open the template image
    image_source = Image.open(TEMPLATE_PATH)
    draw = ImageDraw.Draw(image_source)

    # Finding the width and height of the text.
    name_width, name_height = textsize(name, font=FONT_FILE)

    descs = split_string_by_length(Description, 57)

    # Placing it in the center, then making some adjustments.
    draw.text(((image_source.width - name_width) / 2, (image_source.height - name_height) / 2 - 30), name,
              fill=FONT_COLOR, font=FONT_FILE)
    
    name_width, name_height = textsize(title, font=FONT_FILE3)
    draw.text(((image_source.width - name_width) / 2, (image_source.height - name_height) / 2 - 320), title,
              fill=FONT_COLOR, font=FONT_FILE3)
    
    name_width, name_height = textsize(subtitle, font=FONT_FILE4)
    FONT_COLOR2 = (255,215,0)
    draw.text(((image_source.width - name_width) / 2, (image_source.height - name_height) / 2 - 200), subtitle,
              fill=FONT_COLOR2, font=FONT_FILE4)
    
    x=0
    
    for nam in descs:
        name_width2, name_height2 = textsize(nam, font=FONT_FILE2)
        draw.text(((image_source.width - name_width2) / 2, (image_source.height - name_height2) / 2 + 145+x), nam,
              fill=FONT_COLOR, font=FONT_FILE2)
        x=x+80

    if logo is None:
        overlay_image = Image.open("overlay_image.png")
    else:
        overlay_image = Image.open(logo)
    # Resize the overlay image to have a width of 150 pixels
    new_width = 400
    width_percent = (new_width / float(overlay_image.size[0]))
    new_height = int((float(overlay_image.size[1]) * float(width_percent)))
    overlay_image = overlay_image.resize((new_width, new_height), Image.LANCZOS)
    # Calculate the position where you want to place the overlay image
    position = ((image_source.width - overlay_image.width) // 2, 100)
    # Paste the overlay image onto the main image
    image_source.paste(overlay_image, position, overlay_image)

    if sign is None:
        overlay_image = Image.open("sign.png")
    else:
        overlay_image = Image.open(sign)
    # Resize the overlay image to have a width of 150 pixels
    new_width = 200
    width_percent = (new_width / float(overlay_image.size[0]))
    new_height = int((float(overlay_image.size[1]) * float(width_percent)))
    overlay_image = overlay_image.resize((new_width, new_height), Image.LANCZOS)
    # Calculate the position where you want to place the overlay image
    position = ((image_source.width - overlay_image.width) // 2, (image_source.height - overlay_image.height)-215)
    # Paste the overlay image onto the main image
    image_source.paste(overlay_image, position, overlay_image)

    name_width, name_height = textsize(signer, font=FONT_FILE5)
    draw.text(((image_source.width - name_width) / 2, (image_source.height - name_height)- 155), signer,
              fill=FONT_COLOR, font=FONT_FILE5)



    # Saving the certificate as PNG temporarily
    temp_png_path = os.path.join(OUTPUT_DIR, name + ".png")
    image_source.save(temp_png_path)

    # Convert the PNG to PDF
    pdf_path = os.path.join(OUTPUT_DIR, name + ".pdf")
    image_width, image_height = image_source.size
    pdf = canvas.Canvas(pdf_path, pagesize=(image_width, image_height))
    pdf.drawImage(temp_png_path, 0, 0, width=image_width, height=image_height, preserveAspectRatio=True)
    pdf.save()

    # Remove the temporary PNG file
    os.remove(temp_png_path)

    print('Saving Certificate of:', name)

def generate_certificates(csv_filename):
    data = read_data_from_csv(csv_filename)
    for row in data:
        make_certificate(*row)
    print(len(data), "certificates done.")

def read_data_from_csv(filename):
    data = []
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:  # Check if the row is not empty
                data.append(row[:5])  # Assuming columns 0, 1, 2, and 3 are names, descs, col3, col4
    return data

def create_zip():
    zip_filename = 'certificates'
    zip_path = shutil.make_archive(OUTPUT_CERTIFICATE+zip_filename, 'zip', OUTPUT_DIR)
    return zip_path

@app.route('/download_zip')
def download_zip():
    # Assuming your zip file is named 'example.zip' and located in the 'static' folder
    zip_path = 'static/outputcertificate/certificates.zip'
    return send_file(zip_path, as_attachment=True)


# Check if the source file exists


if __name__ == "__main__":
    app.config['UPLOAD_FOLDER'] = 'uploads'
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
