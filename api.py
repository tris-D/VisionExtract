import requests
from datetime import date
import datetime
from flask import Flask,jsonify,render_template,request

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, Date, JSON

import shutil
from methods import upscale_images, extract_table, extract_text

from dotenv import load_dotenv
import os

import pd
from functools import wraps

load_dotenv(override=True)
app=Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY_V1')

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

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! NOTE: START OF RESTful API REQUESTS INSTEAD OF ONLINE DEMO !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

def token_required(function):
    @wraps(function)
    def decorator(*args,**kwargs):
        token = request.headers.get('Authorization')

        if not token or token != f"Bearer {os.environ.get('API_KEY')}":
            return jsonify(response={"Error":"Unauthorized"}),401

        return function(*args,**kwargs) # THIS IS ESSENTIAL BECAUSE YOU DON'T JUST WANT THE FUNCTION TO RUN
        # YOU ALSO WANT IT TO RETURN THE FUNCTION RUNNING FOR EXTRA WRAPPERS, OR have it ACTUALLY running outside of the 
        # decorator so that it can be captured if needed
    return decorator

def authentication_required(function):
    @wraps(function)
    def decorator(*args,**kwargs):
        authentication = request.headers.get('Authorization')

        if not authentication or authentication != f"Basic {os.environ.get('BASIC_KEY')}":
            return jsonify(response={"Error":"Unauthorized"}),401
        
        return function(*args,**kwargs)
    return decorator

@app.route('/v1/')
def V1_home():
    return render_template("index_v1.html")

@app.route('/v1/history_images',methods=['GET'])
@token_required
def v1_history_images():
    result = database.session.execute(database.select(Extract).where(Extract.filetype == "image")).scalars().all()
    list_of_files = []
    for file in result:
        db_values = [getattr(file,column) for column in db_names]
        dictionary = {key:value for key,value in zip(db_names,db_values)}
        list_of_files.append(dictionary)
    print(list_of_files)
    return jsonify({"All image files":list_of_files})

@app.route('/v1/history_text',methods=['GET'])
@token_required
def v1_history_text():
    result = database.session.execute(database.select(Extract).where(Extract.filetype == "text")).scalars().all()
    list_of_files = []
    for file in result:
        db_values = [getattr(file,column) for column in db_names]
        dictionary = {key:value for key,value in zip(db_names,db_values)}
        list_of_files.append(dictionary)
    print(list_of_files)
    return jsonify({"All text files":list_of_files})

@app.route('/v1/history_tables',methods=['GET'])
@token_required
def v1_history_tables():
    result = database.session.execute(database.select(Extract).where(Extract.filetype == "datatable")).scalars().all()
    list_of_files = []
    for file in result:
        db_values = [getattr(file,column) for column in db_names]
        dictionary = {key:value for key,value in zip(db_names,db_values)}
        list_of_files.append(dictionary)
    print(list_of_files)
    return jsonify({"All datatable files":list_of_files})

@app.route('/v1/find_file',methods=['GET'])
@token_required
def v1_find_file():
    id=int(request.args.get("id"))
    try:
        file_to_find = database.get_or_404(Extract,id)
    except Exception as e:
        print(e)
        return jsonify({"Error":f"{e}"}),403
    else:
        db_values = [getattr(file_to_find,column) for column in db_names]
        dictionary = {key:value for key,value in zip(db_names,db_values)}
        print(dictionary)
        return jsonify({f"File found":dictionary}),200
    
# In python, the decorator closest to the function is used first, and the order goes out from there, so second decorator is 
# the top one, but these two don't conflict anyways so there should be no issues   
@app.route('/v1/query_image',methods=['GET'])
@token_required
def v1_query_image():
    date,keyword = request.args.get('date'),request.args.get('keyword')
    list_of_files = []
    if not date:
        files_match = database.session.execute(database.select(Extract).where(
            and_(
                Extract.name.ilike(keyword),
                Extract.filetype == 'image'
                )
        )).scalars().all()
    elif date:
        files_match = database.session.execute(database.select(Extract).where(
            and_(
                Extract.name.ilike(keyword),
                Extract.date == datetime.strptime(date,"%Y-%m-%d"),
                Extract.filetype == "image"
            )
        )).scalars().all()
    if files_match:
        for file in files_match:
            db_values = [getattr(file,column) for column in db_names]
            dictionary = {key:value for key,value in zip(db_names,db_values)}
            list_of_files.append(dictionary)
        print(list_of_files)
        return jsonify({"Image files found":list_of_files}),200
    else:
        return jsonify({"Error":"No image files found with specified parameters"}),403
    
@app.route('/v1/query_text',methods=['GET'])
@token_required
def V1_query_text():
    date,keyword = request.args.get('date'),request.args.get('keyword')
    list_of_files = []
    if not date:
        files_match = database.session.execute(database.select(Extract).where(
            and_(
                Extract.name.ilike(keyword),
                Extract.filetype == 'text'
                )
        )).scalars().all()
    elif date:
        files_match = database.session.execute(database.select(Extract).where(
            and_(
                Extract.name.ilike(keyword),
                Extract.date == datetime.strptime(date,"%Y-%m-%d"),
                Extract.filetype == "text"
            )
        )).scalars().all()
    if files_match:
        for file in files_match:
            db_values = [getattr(file,column) for column in db_names]
            dictionary = {key:value for key,value in zip(db_names,db_values)}
            list_of_files.append(dictionary)
        print(list_of_files)
        return jsonify({"Text files found":list_of_files}),200
    else:
        return jsonify({"Error":"No text files found with specified parameters"}),403
    
@app.route('/v1/query_table',methods=['GET'])
@token_required
def V1_query_table():
    date,keyword = request.args.get('date'),request.args.get('keyword')
    list_of_files = []
    if not date:
        files_match = database.session.execute(database.select(Extract).where(
            and_(
                Extract.name.ilike(keyword),
                Extract.filetype == 'datatable'
                )
        )).scalars().all()
    elif date:
        files_match = database.session.execute(database.select(Extract).where(
            and_(
                Extract.name.ilike(keyword),
                Extract.date == datetime.strptime(date,"%Y-%m-%d"),
                Extract.filetype == "datatable"
            )
        )).scalars().all()
    if files_match:
        for file in files_match:
            db_values = [getattr(file,column) for column in db_names]
            dictionary = {key:value for key,value in zip(db_names,db_values)}
            list_of_files.append(dictionary)
        print(list_of_files)
        return jsonify({"Datatable file found":list_of_files}),200
    else:
        return jsonify({"Error":"No table files found with specified parameters"}),403
    
@app.route('/v1/add_image', methods=['POST'])
@token_required
def V1_add_image():
    source_images = request.files.getlist('images[]')
    output_path,input_path = upscale_images(source_images)
    input_file_paths = [os.path.join(input_path,origin.filename) for origin in source_images]
    for images,input_file_path in zip(output_path,input_file_paths):
        filename = os.path.basename(images)
        new_image=Extract(
            name=filename,
            filetype="image",
            file_location=input_file_path,
            output_location=images,
            input_size = os.path.getsize(input_file_path)/1024,
            output_size = os.path.getsize(images)/1024
        )
        database.session.add(new_image)
        database.session.commit()
    return jsonify(response={"Success":"New image files have been upscaled 4x and stored in the database."}),200

@app.route('/v1/add_table',methods=['POST'])
@token_required
def V1_add_table():
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

@app.route('/v1/add_text',methods=['POST'])
@token_required
def V1_add_text():
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

@app.route('/v1/fix/<string:filetype>',methods=['PATCH'])
@token_required
def V1_fix(filetype):
    if filetype == "text":
        data = request.get_json()
        file_id = data.get('id')
        text_data = data.get('text')
        file_to_edit = database.get_or_404(Extract,file_id)
        file_to_edit.text_output = text_data
        file_to_edit.edit_date = date.today()
        database.session.commit()
        return jsonify(response={"Success":"Successfully updated the text."}),200
    else:
        return jsonify(response={"Error":"File type must be text to edit and change the extracted text within."}),403

# REMEMBER FOR PUT, PATCH, AND POST METHODS, TYPICALLY INFORMATION IS PASSED THROUGH THE ROUTE BY the url
# OR MORE COMMONLY, THROUGH (url,headers=header,json={info}), not as parameters
@app.route('/v1/replace/<string:filetype>',methods=['PUT'])
@token_required
def V1_replace(filetype):
    if filetype == "datatable":
        datatable_replace = request.files.get('file')
        data = request.get_json()
        file_id = data.get('id')

        data_to_replace = database.get_or_404(Extract,file_id)

        if data_to_replace.filetype == "datatable":
            new_save_path = os.path.join(data_to_replace.output_location,"replace_file.csv")
            datatable_replace.save(new_save_path)
            new_datatable = Extract(
                id = data_to_replace.id,
                name = data_to_replace.name,
                date = data_to_replace.date,
                filetype = 'datatable',
                file_location = data_to_replace.file_location,
                output_location = data_to_replace.output_location,
                input_size = data_to_replace.input_size,
                output_size = os.path.getsize(data_to_replace.output_location)/1024,
                data_output = (pd.read_csv(new_save_path)).to_json(orient="records"),
                edit_date = date.today()
            )
            # DELETING OLD ENTRY
            database.session.delete(data_to_replace)
            database.session.commit()
            # CREATING NEW ENTRY WITH THE SAME ID
            database.session.add(new_datatable)
            database.session.commit()

            return jsonify(response={"Success":"Datatable replace successful."}),200

# FOR DELETE METHODS, INFORMATION IS PASSED THROUGH THE URL    
@app.route('/v1/delete/<int:id>',methods=['DELETE'])
@authentication_required
def V1_delete(id):
    file = database.session.get_or_404(Extract,id)
    database.session.delete(file)
    database.session.commit()
    return jsonify(response={"Success":"Session deleted."}),200

@app.route('/v1/clear',methods=['DELETE'])
@authentication_required
def V1_clear():
    database.drop_all()
    database.create_all()
    return jsonify(response={"Success":"Database cleared and reset."}),200

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! NOTE: END OF RESTful API REQUESTS INSTEAD OF ONLINE DEMO !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=4000)