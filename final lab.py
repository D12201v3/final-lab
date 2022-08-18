""" 
COMP 593 - Final Project
Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.
Usage:
  python apod_desktop.py image_cache_path [apod_date]
Parameters:
  image_cache_path = Full path of the image cache directory
  apod_date = APOD date (format: YYYY-MM-DD)
History:
  Date        Author    Description
  2022-05-09  J.Dalby   Initial creation
  2022-08-16  H.Wood    Finishing project
"""

from os import path
from sys import argv, exit
from  datetime import datetime, date
from hashlib import sha256
from os import path, makedirs
import ctypes
import requests
import sqlite3
import re


def main():
    # *** DO NOT MODIFY THIS FUNCTION ***

    # Determine the path of image cache directory and SQLite data base file
    image_cache_path = get_image_cache_path()
    db_path = path.join(image_cache_path, 'apod_images.db')

    # Determine the date of the desired APOD
    apod_date = get_apod_date()

    # Create the image cache database, if it does not already exist
    create_apod_image_cache_db(db_path)

    # Get info about the APOD from the NASA API
    apod_info_dict = get_apod_info(apod_date)
    
    # Get the URL of the APOD
    image_url = get_apod_image_url(apod_info_dict)
    image_title = get_apod_image_title(apod_info_dict)
    
    # Determine the path at which the downloaded image would be saved 
    image_path = get_apod_image_path(image_cache_path, image_title, image_url)

    # Download the APOD image data, but do not save to disk
    image_data = download_image_from_url(image_url)

    # Determine the SHA-256 hash value and size of the APOD image data
    image_size = get_image_size(image_data)
    image_sha256 = get_image_sha256(image_data)

    # Print APOD image information
    print_apod_info(image_url, image_title, image_path, image_size, image_sha256)

    # Add image to cache if not already present
    if not apod_image_already_in_cache(db_path, image_sha256):
        save_image_file(image_data, image_path)
        add_apod_to_image_cache_db(db_path, image_title, image_path, image_size, image_sha256)

    # Set the desktop background image to the selected APOD
    set_desktop_background_image(image_path)

def get_image_cache_path():
    
    if len(argv) >= 2:
        dir_path = argv[1]

        if not path.isabs(dir_path):
            print('Error: Image cache path perameter must be absolute.')
            exit('Script aborted')
        else:
            if path.isdir(dir_path):
                print('Image cache directory:', dir_path)
                return dir_path
            elif path.isfile(dir_path):
                print('Error: Path perameter is existing file.')
                exit('Script aborted')
            else:
                print("Creating new direcorty" + dir_path + "...", end='.')
                try:
                    makedirs(dir_path)
                    print('success')
                except:
                    print('failure')
                return dir_path

    else:
        print('Error: missing image path parameter.')
        exit('Sreipt aborted')
    

def get_apod_date():
    
    if len(argv) >= 3:
        apod_date = argv[2]

        try: 
            apod_datetime = datetime.strptime(apod_date, '%Y-%m-%d')
        except:
            print('Error: Invalic date format: must be YYYY-MM-DD.')
            exit('Script aborted')
        if apod_datetime.date() < date(1995,6,16):
            print('Error: please use any date after 1995,06,16.')
            exit('Script aborted')
        elif apod_datetime.date() > date.today():
            print ('Error: please do not use future dates.')
            exit('Script aborted')
    else:
        apod_date = date.today().isoformat()
    
    print('APOD date:', apod_date)
    return apod_date

def get_apod_image_path(image_cache_path, image_title, image_url):

    file_ext = image_url.split(".")[-1]

    file_name = image_title.strip()
    file_name = file_name.replace(' ','_')
    file_name = re.sub(r'\W','', file_name)
    file_name = '.'.join((file_name, file_ext))
    file_path = path.join(image_cache_path, file_name)

    return file_path
    

def get_apod_info(apod_date):
    
    print("Getting APOD information from NASA...", end='')

    NASA_API_KEY = 'tz6CvXkLfg4etTXfvIZSOFaGDi6Cmm9BT393j05V'
    APOD_URL = "https://api.nasa.gov/planetary/apod"
    apod_params = {
        'api_key' : NASA_API_KEY,
        'date' : apod_date,
        'thumbs' : True
    }
    
    resp_msg = requests.get(APOD_URL, params=apod_params)
    if resp_msg.status_code == requests.codes.ok:
        print('success')
    else:
        print('failure code:', resp_msg.status_code)    
        exit('Script execution aborted')

    # Convert the received info into a dictionary 
    apod_info_dict = resp_msg.json()
    return apod_info_dict
   

def get_apod_image_url(apod_info_dict):

    if apod_info_dict['media_type'] == 'image':
        return apod_info_dict['hdurl']
    elif apod_info_dict['media_type'] == 'video':
        return apod_info_dict['thumbnail_url']

def get_apod_image_title(apod_info_dict):
   
    return apod_info_dict['title']

def print_apod_info(image_url, image_title, image_path, image_size, image_sha256):
    
    print('APOD image information:')
    print('Image Title:', image_title)
    print('Image URL:', image_url)
    print('Image Size:', image_size)
    print('Image Hash:', image_sha256)
    print('Image saved to:', image_path)

def create_apod_image_cache_db(db_path):

    con = sqlite3.connect(db_path)
    con.commit
    con.close

def add_apod_to_image_cache_db(db_path, image_title, image_path, image_size, image_sha256):
    
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(''' CREATE TABLE IF NOT EXISTS Image (title TEXT, path BLOB, size INTEGER, sha256 BLOB);''')
    Apod_info = [image_title, image_path, image_size, image_sha256]
    add_apod_data = '''INSERT INTO Image (title, path, size, sha256) VALUES(?, ?, ?, ?);'''
    cur.execute(add_apod_data, Apod_info)
    con.commit
    con.close

def apod_image_already_in_cache(db_path, image_sha256):
   
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    try:
        cur.execute('''SELECT Image WHERE sha256 = VALUES(?)''',(image_sha256))
    except:
        return False
    else:
        return True

def get_image_size(image_data):
   
    return (len(image_data))
    

def get_image_sha256(image_data):
    
    return sha256(image_data).hexdigest().upper()
    
def download_image_from_url(image_url):
    
    print("Downloading APOD image from NASA...", end='')

    # Send GET request to download the image
    resp_msg = requests.get(image_url)

    # Check if the image was retrieved successfully
    if resp_msg.status_code == requests.codes.ok:
        print('success')
    else:
        print('failure code:', resp_msg.status_code)    
        exit('Script execution aborted')

    return resp_msg.content

def save_image_file(image_data, image_path):
    
    try:
        print("Saving image file to cache...", end='')
        with open(image_path, 'wb') as fp:
            fp.write(image_data)
        print("success")
    except:
        print("failure")
        exit('Script execution aborted')

def set_desktop_background_image(image_path):
   
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path , 0)

main()