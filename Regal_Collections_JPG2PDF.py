#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Regal_Collections_JPEG2PDF
    Script to munge JPEG photos into small Black&White PDFs
    PDFs named based on location name recovered from Optical Character Recognition
    combined with Date of Photo recovered from filename of JPEG
"""

__author__ = "Conrad Storz"
__copyright__ = "Copyright 2019-2020"
__credits__ = ["Conrad Storz"]
__license__ = "GPL"
__version__ = "1.0.0.1"
__maintainer__ = "Conrad Storz"
__email__ = "conradstorz@gmail.com"
__status__ = "Dev"

import os
import shutil
import string
import random
from time import sleep

import PIL.Image  # PIL is python 2.7 only (installed Pillow_as_PIL instead)
from loguru import logger #TODO fix location of LOG files into a sub-folder
from pytesseract import *

pyt_img2str = pytesseract.image_to_string
# the line below has windows style file descriptor slashes that python decodes as unicode
# but the module pytesseract requires these slashes to find the file
pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)  # Windows put files in a location off-path so this is a workaround

import tkinter as tk
from tkinter.simpledialog import askstring, askinteger
from tkinter.messagebox import showerror

# Variables
known_locations = {
    "River Falls": "Regal_Cinemas_River_Falls",
    "#1537": "Regal_Cinemas_River_Falls",
    "New Albany": "Regal_Cinemas_New_Albany",
    "#1522": "Regal_Cinemas_New_Albany",
    "Hamburg": "Regal_Cinemas_Hamburg",
    "#728": "Regal_Cinemas_Hamburg",
    "Wilder": "Regal_Cinemas_Wilder",
    "#1526": "Regal_Cinemas_Wilder",
}
output_reduction_factor = 3
#input_folder = "./Regal_photos/"
input_folder = "G:/Documents/"
output_folder = "G:/Documents"
inputfile_extension = ".jpg"
# sample output directory
# "G:/Documents/Regal_Collections_20190918"


@logger.catch
def move_file(old_FQFN, new_FQFN):
    """ Move a file from it's old location to a new location
    FQFN = Fully Qualified File Name
    """
    logger.info("Move " + old_FQFN + " to " + new_FQFN)
    shutil.move(old_FQFN, new_FQFN)
    # os.rename(old_FQFN, new_FQFN) # doesn't work across different drives
    return


@logger.catch
def retieve_image(fname, color=True):
    """ Read a JPEG image from storage and optionally rotate and remove color from image
    """
    #filename = fname
    #name = filename.split(".")[0]
    # TODO trap possible file error IOError
    im = PIL.Image.open(fname)
    logger.debug(str(im.format) + " " + str(im.mode) + " " + str(im.size))

    if color == False:
        im = im.convert("L")  # strip color information from image

    return im


@logger.catch
def save_as_pdf(image, fname, date="xxxxxxx"):
    """ Place the PDF in the specified folder. Create the directory if needed.
    """

    @logger.catch
    def reduce_size(tpl, factor):
        """ reduce the values of integers inside of the tuple by factor
        """
        out = []
        for x in list(tpl):
            out.append(int(x / factor))
        return tuple(out)

    output_size = reduce_size(image.size, output_reduction_factor)
    logger.debug(output_size)
    image = image.resize(output_size)
    PIL.Image.Image.save(image, fname, "PDF", resolution=100.0)
    logger.info("PDF Image saved: {}".format(fname))
    return True


@logger.catch
def gather_all_JPEG_filenames_and_process():
    """ Get files and convert to PDF
    """

    @logger.catch
    def extract_date(fname):
        """ the filename contaims the date the photo was taken
        extract and return the date string
        """
        logger.info("Processing: " + fname)
        datestring = fname[4:12]  # sample filename string "IMG_20190724_102855.jpeg"
        return datestring

    logger.info(f'\nScanning input folder: {input_folder}')
    files = [f for f in os.listdir(input_folder) if f.endswith(inputfile_extension)]
    num_of_files = str(len(files))
    if num_of_files == "0":
        logger.info('\nNo files found in directory to process.')
        return False
    logger.debug(files)

    for fname in files:
        logger.info(
            "\nProcessing: "
            + str(files.index(fname) + 1)
            + " of "
            + num_of_files
            + " files..."
        )
        filedate = extract_date(fname)
        logger.debug(filedate)
        img = retieve_image("".join([input_folder, fname]), color=False)
        if img != None:
            img, filename, outdir = determine_output_filename(img, filedate)
            logger.debug("New filename: " + filename)
            if save_as_pdf(img, filename):
                logger.info("Completed: " + filename)
                # TODO the next line choked on a filename with spaces in the name
                move_file("".join([input_folder, fname]), "".join([outdir, "/", fname]))
            else:
                logger.info("Failed to save: " + filename)
                return False
        else:
            return False
    return True


@logger.catch
def find_match(txt):
    match = "INDETERMINATE"
    for k in known_locations.keys():
        if k in txt:
            match = known_locations[k]
    return match


@logger.catch
def rotate_and_OCR(image):
    logger.info("Rotating image...")
    img = image.transpose(PIL.Image.ROTATE_270)
    logger.info("Applying Optical Character Recognition...")
    try:
        txt = pyt_img2str(img)
    except pytesseract.pytesseract.TesseractNotFoundError as e:
        logger.error(str(e))
        return (image, 'notfound')
    logger.debug("TEXT FOUND:\n" + txt)
    return (img, txt)


@logger.catch
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):

    return ''.join(random.choice(chars) for _ in range(size))

@logger.catch
def determine_output_filename(image, datestr):
    """ Using Optical Character Recognition try to identify from the picture
    what known location this picture represents and build the output filename.
    return rotated image and filename tuple.
    """
    dest_folder = ""
    newfilename = ""
    rotations = 4
    location_match = "INDETERMINATE"
    logger.info('Verifing output folder...')
    if not os.path.exists(output_folder):  # check and create output folder
        os.makedirs(output_folder)  # TODO trap IOerrors
    dest_folder = output_folder + "/" + "Regal_Collections_" + datestr
    if not os.path.exists(dest_folder):  # check and create date folder
        os.makedirs(dest_folder)  # TODO trap IOerrors    
    logger.info("Starting OCR image processing...")
    while rotations:
        rotations -= 1
        img, text = rotate_and_OCR(image)  # unpack returned tuple
        location_match = find_match(text)
        if location_match != "INDETERMINATE":
            rotations = 0
        else:
            logger.info("No Match!")
    if location_match != "INDETERMINATE":
        logger.info("Data extracted: " + location_match)
    else:
        logger.error("Location name could not be identified!")
        logger.error('Generating random filename...')
        id1 = id_generator()
        location_match = f'{datestr}_{id1}'
    newfilename = "".join([dest_folder, "/", datestr, "_", location_match, ".pdf"])
    # TODO check if name already exists and do not overwrite
    return (img, newfilename, dest_folder)


@logger.catch
def DefineLoggers():
    logger.configure(
        handlers=[{"sink": os.sys.stderr, "level": "INFO"}]
    )  # this method automatically suppresses the default handler to modify the message level
    logger.add(
        os.sys.stderr,
        format="{time} {level} {message}",
        filter="my_module",  # creates an entry showing module name and source code line number
        level="INFO",
    )  # set a handler
    logger.add(
        "./file.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    )  # this establishes a file log that gets appended each time the program runs
    logger.add("./LOGS/file_{time}.log")  # create a new log file for each run of the program
    return


@logger.catch
def Main():
    DefineLoggers()
    logger.info("Program Start.")  # log the start of the program
    if gather_all_JPEG_filenames_and_process():
        logger.info('All files processed.')
    else:
        logger.info('Error during processing.')
    logger.info('Program end.')
    return


if __name__ == "__main__":
    Main()
