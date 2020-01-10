#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Regal_Collections_JPEG2PDF
    Script to munge JPEGs into small Black&White PDFs
    PDFs named based on location name recovered from OCR
    and Date of Photo recovered from filename of JPEG
"""

__author__ = "Conrad Storz"
__copyright__ = "Copyright 2019"
__credits__ = ["Conrad Storz"]
__license__ = "GPL"
__version__ = "1.0.0.0"
__maintainer__ = "Conrad Storz"
__email__ = "conradstorz@gmail.com"
__status__ = "Dev"

import os
import shutil
from time import sleep

import PIL.Image  # PIL is python 2.7 only (installed Pillow_as_PIL instead)
from loguru import logger #TODO fix location of LOG files into a sub-folder
from pytesseract import *

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
input_folder = "./Regal_photos/"
output_folder = "G:/Documents"
inputfile_extension = ".jpg"
# sample output directory
# "G:\Documents\2019_Regal_Photobooths_Collections\Regal Collections 20190918"


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
    filename = fname
    name = filename.split(".")[0]
    # TODO trap possible file error IOError
    im = PIL.Image.open(filename)
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

    files = [f for f in os.listdir(input_folder) if f.endswith(inputfile_extension)]
    num_of_files = str(len(files))
    if num_of_files == "0":
        logger.info('No files found in directory to process.')
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
                move_file("".join([input_folder, fname]), "".join([outdir, "/", fname]))
            else:
                logger.info("Failed to save: " + filename)
                return False
        else:
            return False
    return True


@logger.catch
def determine_output_filename(image, datestr):
    """ Using Optical Character Recognition try to identify from the picture
    what known location this picture represents and build the output filename.
    return rotated image and filename tuple.
    """

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
        txt = image_to_string(img)
        logger.debug("TEXT FOUND:\n" + txt)
        return (img, txt)

    dest_folder = ""
    newfilename = ""
    rotations = 4
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
        if not os.path.exists(output_folder):  # check and create output folder
            os.makedirs(output_folder)  # TODO trap IOerrors
        dest_folder = output_folder + "/" + "Regal Collections " + datestr
        if not os.path.exists(dest_folder):  # check and create date folder
            os.makedirs(dest_folder)  # TODO trap IOerrors
        newfilename = "".join([dest_folder, "/", datestr, "_", location_match, ".pdf"])
        # TODO check if name already exists and do not overwrite
    else:
        logger.error("Location name could not be identified!")
    return (img, newfilename, dest_folder)


@logger.catch
def Main():
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
        "file.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    )  # this establishes a file log that gets appended each time the program runs
    logger.add("file_{time}.log")  # create a new log file for each run of the program
    logger.info("Program Start.")  # log the start of the program
    if gather_all_JPEG_filenames_and_process():
        logger.info('All files processed.')
    else:
        logger.info('Error during processing.')
    logger.info('Program end.')
    return


if __name__ == "__main__":
    Main()


@logger.catch
def ask_user_to_decide(img):
    """ the OCR could not determine what location this image represents.
    display the image and ask the user to decide.
    this function is not functional. It is never meant to be used in this condition.
    """
    location_name = (
        "INDETERMINATE"
    )  # use the name "indeterminate" if user fails to respond
    img.show()  # display image

    # list known locations
    def use_tkinter_to_ask_user():  # DO NOT USE
        answer = "IDONTKNOW"

        def display_1():
            # .get is used to obtain the current value
            # of entry_1 widget (This is always a string)
            print(entry_1.get())

        def display_2():
            num = entry_2.get()
            # Try convert a str to int
            # If unable eg. int('hello') or int('5.5')
            # then show an error.
            try:
                num = int(num)
            # ValueError is the type of error expected from this conversion
            except ValueError:
                # Display Error Window (Title, Prompt)
                showerror("Non-Int Error", "Please enter an integer")
            else:
                print(num)

        def display_3():
            # Ask String Window (Title, Prompt)
            # Returned value is a string
            ans = askstring("Enter String", "Please enter any set of characters")
            # If the user clicks cancel, None is returned
            # .strip is used to ensure the user doesn't
            # enter only spaces ' '
            if ans is not None and ans.strip():
                print(ans)
            elif ans is not None:
                showerror("Invalid String", "You must enter something")

        def display_4():
            # Ask Integer Window (Title, Prompt)
            # Returned value is an int
            ans = askinteger("Enter Integer", "Please enter an integer")
            # If the user clicks cancel, None is returned
            if ans is not None:
                print(ans)

        # Create the main window
        root = tk.Tk()

        # Create the widgets
        entry_1 = tk.Entry(root)
        btn_1 = tk.Button(root, text="Display Text", command=display_1)

        entry_2 = tk.Entry(root)
        btn_2 = tk.Button(root, text="Display Integer", command=display_2)

        btn_3 = tk.Button(root, text="Enter String", command=display_3)
        btn_4 = tk.Button(root, text="Enter Integer", command=display_4)

        # Grid is used to add the widgets to root
        # Alternatives are Pack and Place
        entry_1.grid(row=0, column=0)
        btn_1.grid(row=1, column=0)
        entry_2.grid(row=0, column=1)
        btn_2.grid(row=1, column=1)

        btn_3.grid(row=2, column=0)
        btn_4.grid(row=2, column=1)

        root.mainloop()
        return answer

    sleep(5)  # ask user to decide but only wait for max 3 minutes

    return location_name
