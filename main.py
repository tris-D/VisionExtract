from flask import Flask, jsonify, render_template, request, Response,redirect,url_for,flash,send_file,send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, Date, JSON
import random as r

from datetime import date

import shutil
from flask_bootstrap5 import Bootstrap

from methods import upscale_images, extract_table, extract_text

from dotenv import load_dotenv
import os
import zipfile
from io import BytesIO
import pd
from functools import wraps


load_dotenv(override=True) # SET THIS AS TRUE BECAUSE ENVIRONMENT VARIABLES WON'T CHANGE IF THEY WERE INITIALLY SET
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
Bootstrap(app)

print(os.environ.get('BASIC_KEY'))

# Create DataBase
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///textract.db'
database = SQLAlchemy(model_class=Base)
database.init_app(app)
                    
# Textract Table Configuration
            
class Extract(database.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key = True)
    name: Mapped[str] = mapped_column(String(250),unique = False, nullable=False)
    filetype: Mapped[str] = mapped_column(String(100),nullable=False)
    date: Mapped[Date] = mapped_column(Date,nullable=False)
    file_location : Mapped[str] = mapped_column(String(250), nullable = False)
    output_location : Mapped[str] = mapped_column(String(250),nullable=False)
    input_size : Mapped[str] = mapped_column(String(100),unique=False,nullable=False)
    output_size : Mapped[str] = mapped_column(String(100),unique=False,nullable=False)
    text_output : Mapped[str] = mapped_column(String,nullable=True)
    data_output : Mapped[dict] = mapped_column(JSON,nullable=True)
    edit_date: Mapped[Date] = mapped_column(Date,nullable=True)

with app.app_context():
    database.create_all()
    db_names = Extract.__table__.columns.keys()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/documentation')
def documentation():
    token = os.environ.get('API_KEY')
    username = os.environ.get('BASIC_AUTH_USERNAME')
    password = os.environ.get('BASIC_AUTH_PASSWORD')
    basic_key = os.environ.get('BASIC_KEY')
    return render_template("documentation.html",token=token,username=username,password=password,basic_key=basic_key)

@app.route('/functions')
def functions():
    return render_template("menu.html")

@app.route('/history_images')
def history_images():
    image_history = database.session.execute(database.select(Extract).where(Extract.filetype == "image")).scalars().all()
    metadata = []
    for image in image_history:
        metadata.append({
            "name":image.name,  
            "id":image.id,
            "date":image.date,
            "link":image.output_location
        })
    return render_template("items.html",entries=metadata[::-1],view_type="Image")

@app.route('/history_tables')
def history_tables():
    table_history = database.session.execute(database.select(Extract).where(Extract.filetype == "datatable")).scalars().all()
    metadata = []
    for table in table_history:
        metadata.append({
            "name":table.name,
            "id":table.id,
            "date":table.date,
            "link":table.file_location
        })
    return render_template("items.html",entries=metadata[::-1],view_type="Table")

@app.route('/history_text')
def history_text():
    text_history = database.session.execute(database.select(Extract).where(Extract.filetype == "text")).scalars().all()
    metadata = []
    for text in text_history:
        metadata.append({
            "name":text.name,
            "id":text.id,
            "date":text.date,
            "link":text.file_location
        })
    return render_template("items.html",entries=metadata[::-1],view_type="Text")

@app.route('/find_file',methods=['POST','GET'])
def find_file():
    file_id = request.form.get('file_id')
    try:
        file_to_find = database.get_or_404(Extract,file_id)
    except Exception as e:
        print(e)
        flash("File not found.")
        return redirect(url_for('functions'))
    else:
        flash(file_to_find.name)
        flash(file_to_find.id)
        flash(file_to_find.filetype)
        flash(file_to_find.date.strftime("%Y-%m-%d"))
        flash(file_to_find.file_location)
        flash(file_to_find.output_location)
        flash(f"{float(file_to_find.output_size):.3f}KB")
        flash(file_to_find.data_output)
        return redirect(url_for('functions')+"#exploreID")

@app.route('/query_image',methods=['POST','GET'])
def query_image():
    keyword = request.form.get('keyword')
    date = request.form.get('date')
    # .like() and .ilike() operator is for sqlalchemy operator if you don't want an exact match, but similar or contains/partial match
    # .like() is case-sensitive and .ilike() is not
    if not date:
        images_match = database.session.execute(database.select(Extract).where(Extract.name.ilike(keyword))).scalars().all()
    elif date:
        images_match = database.session.execute(database.select(Extract).where(
            and_(
                Extract.name.ilike(keyword),
                Extract.date==date,
            )
        )).scalars().all()
    image_return = []
    if images_match:
        for image in images_match:
            temp = {"name":image.name,
                    "date":image.date,
                    "link":image.output_location
                    }
            image_return.append(temp)
    return render_template("results.html",images=image_return)

@app.route('/query_table',methods=['GET','POST'])
def query_table():
    keyword = request.form.get('keyword')
    date = request.form.get('date')
    if not date:
        datatable_match = database.session.execute(database.select(Extract).where(Extract.name.ilike(keyword))).scalars().all()
    elif date:
        datatable_match = database.session.execute(database.select(Extract).where(
            and_(
                Extract.name.ilike(keyword),
                Extract.date==date,
            )
        )).scalars().all()
    datatable_return = []
    if datatable_match:
        for table in datatable_match:
            temp = {"name":table.name,
                    "date":table.date,
                    "link":table.output_location}
            datatable_return.append(temp)
    return render_template("results.html",datatables = datatable_return)

@app.route('/query_text',methods=['GET','POST'])
def query_text():
    keyword=request.form.get('keyword')
    date = request.form.get('date')
    if not date:
        text_match = database.session.execute(database.select(Extract).where(Extract.name.ilike(keyword))).scalars().all()
    elif date:
        text_match = database.session.execute(database.select(Extract.where(
            and_(
                Extract.name.ilike(keyword),
                Extract.date==date,
            )
        ))).scalars().all()
    text_return = []
    if text_match:
        for text in text_match: 
            temp = {"name":text.name,
                    "date":text.date,
                    "link":text.output_location,
                    "text":text.text_output
                    }
            text_return.append(temp)
    return render_template("results.html",text = text_return)

@app.route('/add_image',methods=['GET','POST'])
def add_image():
    source_images = request.files.getlist('images[]')
    upscaled,input_path= upscale_images(source_images)
    input_file_paths = [os.path.join(input_path,origin.filename) for origin in source_images]
    for images,input_file_path in zip(upscaled,input_file_paths):
        # file.filename only works if the file is directly a file, but if it is a list of path, or a path
        # we must use os.path.basename(file_path)
        filename = os.path.basename(images)

        new_image = Extract(
            name=filename,
            date=date.today(),
            filetype = "image",
            file_location = input_file_path,
            output_location = images,
            input_size = os.path.getsize(input_file_path)/1024,
            output_size = os.path.getsize(images)/1024
        )
        database.session.add(new_image)
        database.session.commit()
    return jsonify(response={"Success":"New image files have been upscaled 4x and stored in the database."}),200

@app.route('/add_table',methods=['GET','POST'])
def add_table():
    extract_image = request.files.get('dataextract')
    image_name = extract_image.filename
    image_path = os.path.join('input',image_name)
    static_path = os.path.join('static','Source',"inputs",image_name)
    extract_image.save(image_path)
    shutil.copy(image_path,static_path)
    input_size_kbytes = os.path.getsize(image_path)/1024
    try:
        datatable_list = extract_table(image_path)
    except Exception as e:
        return jsonify(response={"Failure":"Image could not be processed and data was not extracted"}),400
    image_name = os.path.splitext(image_name)[0]
    output_path = os.path.join('output',image_name,f'{image_name}_1.csv')
    output_size_kbytes = os.path.getsize(output_path)/1024

    new_table = Extract(
        name=image_name,
        date=date.today(),
        filetype = 'datatable',
        file_location = static_path,
        output_location = output_path,
        input_size = input_size_kbytes,
        output_size = output_size_kbytes,
        data_output = datatable_list,
    )
    database.session.add(new_table)
    database.session.commit()
    return jsonify(response={"Success":"New .csv file has been made with the image of the data table provided."}),200

@app.route('/add_text',methods=['GET','POST'])
def add_text():
    extract_image = request.files.get('textract')
    image_name = extract_image.filename
    image_path = os.path.join('input',image_name)
    static_path = os.path.join('static',"Source","inputs",image_name)
    extract_image.save(static_path)
    shutil.copy(static_path,image_path)
    input_size_kbytes = os.path.getsize(image_path)/1024
    text,image_name = extract_text(image_path)
    output_path = os.path.join('output',f'{image_name}.txt')
    output_size_kbytes = os.path.getsize(output_path)/1024

    new_text = Extract(
        name=image_name,
        date=date.today(),
        filetype = 'text',
        file_location = static_path,
        output_location = os.path.join('output',f'{image_name}.txt'),
        input_size = input_size_kbytes,
        output_size = output_size_kbytes,
        data_output = text,
    )
    database.session.add(new_text)
    database.session.commit()
    return jsonify(response={"Success":"New .txt file has been made with the image of the text provided."}),200

@app.route('/fix/<int:id>',methods=['POST','PATCH'])
def fix(id):
    data_id = id
    data_to_edit = database.get_or_404(Extract,data_id)
    file_type = data_to_edit.filetype
    if file_type == "text":
        data_to_edit.text_output = request.form.get('data')
        data_to_edit.edit_date = date.today()
        database.session.commit()
        return jsonify(response={"Success":"Successfully updated the text."}),200
    else:
        return jsonify(response={"Failure":"File type is not a text file so contents can not be changed"}),403

@app.route('/replace/<int:id>',methods=['PUT','POST','GET'])
def replace(id):
    datatable_replace = request.files.get('csv_file')
    data_id = id
    data_to_edit = database.get_or_404(Extract,data_id)
    file_type = data_to_edit.filetype
    key = request.args.get('key')
    if key == "TOPSECRET" and file_type == "datatable":
        new_save_path = os.path.join(data_to_edit.output_location,"replace_file")
        datatable_replace.save(new_save_path)
        data_to_edit.output_size = os.path.getsize(data_to_edit.output_location)/1024
        data_to_edit.edit_date = date.today()
        database.session.commit()
        return jsonify(response={"Success":"Successfully replaced the datatable."})
    return jsonify(error="Error"),400


@app.route('/delete/<int:id>',methods=['DELETE','POST'])
def delete(id):
    key=request.form.get('authPassword')
    if key == "TOPSECRET":
        data_to_delete = database.get_or_404(Extract,id)
        database.session.delete(data_to_delete)
        database.session.commit()
        return jsonify(response={"Success":"Session deleted."})
    return jsonify(response={"Failure":"Something went wrong."}),400

@app.route('/clear',methods=['DELETE','POST'])
def clear():
    key=request.form.get('authPassword')
    api_key = request.form.get('APIKey')
    test_key = os.environ.get('API_KEY')
    if key == "TOPSECRET" and api_key == test_key:
        database.drop_all(bind=database.engine)
        database.create_all(bind=database.engine)
        return jsonify(response={"Success":"Database cleared and reset."}),200
    return jsonify(error="Unauthorized"),403

@app.route('/download/<string:type>/<path:directory>/<path:path>',methods=['GET']) # don't use str:/string: to accept arguments "type:variableName", use <path:___> because path takes forward slashes(//)
def download(type,directory,path):
    print(directory)
    if type == "Image":
        directory=directory.split('\\')
        directory = directory[:-1]
        directory = '\\'.join(directory)
    elif type == "Text":
        path = str(path)+'.txt'
    elif type == "Table":
        BASE_DIR = r"D:\My Files\Coding\Python Coding\4. Portfolio Projects\13.5 RESTful API"
        folder_abs_path = os.path.join(BASE_DIR, "output",path)

        # Create in-memory zip file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_abs_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, folder_abs_path)
                    zipf.write(full_path, arcname=rel_path)

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=os.path.basename(path) + '.zip'
        )
    print(directory)
    print(path)
    return send_from_directory(
        directory=directory,
        path=path,
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)