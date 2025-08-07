import os
import shutil
import boto3
import pandas as pd
from dotenv import load_dotenv

textract = boto3.client('textract')
os.makedirs('input',exist_ok=True)
os.makedirs('output',exist_ok=True)

# *************************************!!!!!!!!!!!!! METHOD 1 !!!!!!!!!!!!!!!!!!!********************************

def extract_table(image_path):
    filename = os.path.basename(image_path) # get just the filename from its entire path
    filename = filename = os.path.splitext(filename)[0]
    data_folder = os.path.join('output',filename)
    os.makedirs(data_folder,exist_ok=True)
    with open(image_path,mode='rb') as newfile:
        document_bytes = newfile.read()
        
    response = textract.analyze_document(
        Document={'Bytes': document_bytes},
        FeatureTypes=['TABLES']
    )

    # First, build a map of Block IDs to Block data
    blocks_map = {block['Id']: block for block in response['Blocks']}

    # Store tables with rows and cells
    tables = []
    frames = []
    

    for block in response['Blocks']:
        if block['BlockType'] == 'TABLE':
            table = []
            # Table has CHILD relationships that point to CELL blocks
            for relationship in block.get('Relationships', []):
                if relationship['Type'] == 'CHILD':
                    for cell_id in relationship['Ids']:
                        cell = blocks_map[cell_id]
                        if cell['BlockType'] == 'CELL':
                            row_index = cell['RowIndex']
                            column_index = cell['ColumnIndex']
                            # Get cell text by following relationships to WORD blocks
                            cell_text = ''
                            for rel in cell.get('Relationships', []):
                                if rel['Type'] == 'CHILD':
                                    words = [blocks_map[word_id]['Text'] for word_id in rel['Ids'] if blocks_map[word_id]['BlockType'] == 'WORD']
                                    cell_text = ' '.join(words)

                            # Ensure the table has enough rows
                            while len(table) < row_index:
                                table.append({})
                            table[row_index - 1][column_index] = cell_text
            tables.append(table)

    for t_index, table in enumerate(tables, start=1):
        df_rows = []
        for row in table:
            ordered_row = [row.get(i, '') for i in sorted(row)]
            df_rows.append(ordered_row)
        
        df = pd.DataFrame(df_rows)
        df.columns = df.iloc[0]
        df = df[1:]
        # Set the first column (which contains NaN) as the index
        df.set_index(df.columns[0], inplace=True)
        # Remove the index name completely
        if not df.index.name:
            df.index.name = None
        # Remove column level names
        if df.columns.name == 0:
            df.columns.name = None
        df.to_csv(f'output/{filename}/{filename}_{t_index}.csv')
        frames.append(df)
    try:
        json_table = frames[0].to_json()
    except Exception as e:
        print(e)
        json_table = frames[0].reset_index(drop=True).to_json(orient="records")
    finally:
        return json_table

# *************************************!!!!!!!!!!!!! END !!!!!!!!!!!!!!!!!!!********************************

# *************************************!!!!!!!!!!!!! METHOD 2 !!!!!!!!!!!!!!!!!!!********************************

def extract_text(image_path):
    image_name = os.path.basename(image_path)
    image_name = os.path.splitext(image_name)[0]
    with open(image_path, 'rb') as document:
        document_bytes = document.read()

    # Send request to Textract to detect handwriting
    response = textract.detect_document_text(
    Document={'Bytes': document_bytes}
    )

    # Extract and print the text
    text = ''
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            text += block['Text']
            text += ''' '''
    
    # translated_path = os.path.join(output_dir,'new.txt')
    with open(f'output/{image_name}.txt',mode="w") as newfile:
        newfile.write(text)
    print(text)
    return text,image_name

# *************************************!!!!!!!!!!!!! END !!!!!!!!!!!!!!!!!!!********************************

from PIL import Image
import subprocess

# *************************************!!!!!!!!!!!!! METHOD 3 !!!!!!!!!!!!!!!!!!!********************************

def upscale_images(listImages):
    base_dir = "Image Upscaler"
    venv_python = os.path.join(base_dir, "venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(base_dir, "venv", "bin", "python")
    input_dir = os.path.join(base_dir, "Real-ESRGAN", "inputs")
    output_dir = os.path.join(base_dir, "Real-ESRGAN", "results")
    script_path = os.path.join(base_dir, "Real-ESRGAN", "inference_realesrgan.py")
    source_assets = "Source"
    input_path = os.path.join("static",source_assets,"inputs")
    output_path = os.path.join("static",source_assets,"outputs")

    # Delete the Sources folder if it exists
    if os.path.exists(source_assets):
        shutil.rmtree(source_assets)

    # Recreate directories
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(input_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)

    # Save all input images
    for image in listImages:
        save_path = os.path.join(input_dir, image.filename)
        image.save(save_path)

    # Run the upscaler with venv Python
    try:
        subprocess.run([
            venv_python,
            script_path,
            "-i", input_dir,
            "-o", output_dir,
            "--fp32"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print("Upscaling failed:", e)
        raise

    # Collect processed images and save to Sources
    processed_images = []
    for filename in os.listdir(output_dir): # RETURNS ALL FILES AND DIRECTORIES WITHIN SPECIFIC DIRECTORY WITHIN A LIST
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            filepath = os.path.join(output_dir, filename)
            img = Image.open(filepath) # opens as image object
            finished_path = os.path.join(output_path, filename)
            img.save(finished_path)
            processed_images.append(finished_path)

    # Collect processed images and save to Sources
    before_images = []
    for filename in os.listdir(input_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            filepath = os.path.join(input_dir, filename)
            img = Image.open(filepath)
            finished_path = os.path.join(input_path, filename)
            img.save(finished_path)
            before_images.append(finished_path)

    # Clean up by deleting input and result folders
    shutil.rmtree(input_dir)
    shutil.rmtree(output_dir)

    return processed_images,input_path

# *************************************!!!!!!!!!!!!! END !!!!!!!!!!!!!!!!!!!********************************

