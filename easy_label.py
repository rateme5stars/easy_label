import os 
from utils import ImageAnnotation


def copy_folder_structure(src, dst, level='all'):
    """
    Copy the folder structure of src into dst up to a specified level.
    
    Parameters:
    - src (str): Source directory path.
    - dst (str): Destination directory path.
    - level (str or int): Specifies how many levels of subfolders should be copied. 'all' or an integer.
    """
    src_depth = src.rstrip(os.sep).count(os.sep)

    for root, dirs, files in os.walk(src):
        depth = root.count(os.sep) - src_depth
        
        if isinstance(level, int) and depth >= level:
            del dirs[:] 
        else:
            dest_dir = root.replace(src, dst, 1)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
                print(f"Created directory: {dest_dir}")

if __name__ == "__main__":
    cur_dir = os.getcwd()
    raw_data_folder = 'raw_data'
    annotation_folder = 'annotation'
    digits_folder = 'digits'

    raw_data_path = os.path.join(cur_dir, raw_data_folder)
    annotation_path = os.path.join(cur_dir, annotation_folder)
    digits_path = os.path.join(cur_dir, digits_folder)

    if not os.path.exists(annotation_path):
        os.makedirs(annotation_folder)

    if not os.path.exists(digits_path):
        os.makedirs(digits_folder)

    copy_folder_structure(src=raw_data_path, dst=digits_path, level='all')
    copy_folder_structure(src=raw_data_path, dst=annotation_path, level=2)

    image_paths = []
    for subdir, dirs, files in os.walk(raw_data_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(subdir, file)
                image_paths.append(file_path)


    image_annotation = ImageAnnotation()
    for i, path in enumerate(image_paths):
        pump_station = path.split('/')[-3]
        pump_name = path.split('/')[-2]
        json_path = os.path.join(annotation_path, pump_station, f'{pump_name}.json')
        save_path = os.path.join(digits_path, pump_station, pump_name, f"{pump_name}_{i}.png")
    
        if not os.path.exists(json_path):
            image_annotation.execute(path, json_path, save_path)
        else:
            image_annotation.cut_only(path, json_path, save_path)
        