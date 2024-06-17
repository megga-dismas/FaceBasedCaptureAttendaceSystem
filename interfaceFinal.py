import tkinter as tk
import json
import PIL
import mysql.connector
# import necessary modules from cv2
from cv2 import VideoCapture, imwrite, data, cvtColor, COLOR_BGR2GRAY, CascadeClassifier
from cv2 import rectangle, destroyAllWindows, imshow
from time import localtime
import os
from PIL import ImageTk, Image
import random
from tkinter.filedialog import askdirectory

def incrementRow():
    global row
    row += 1
def checkFolder():
    '''
    This function generates the date
    That is, year-month-dayOfTheMonth which will be used to save attendants of the specific day
    '''
    t = localtime()
    year = str(t.tm_year)
    month = str(t.tm_mon)
    monthDay = str(t.tm_mday) # str(t.tm_min)
    return year+'-'+month+'-'+monthDay
def connectToDatabase(host="localhost", user="root", password="", database="facecapture", table="EmpInfo")->None:
    """
    Create a database and a table if they do not exist.
    Install wampserver or any other server that serves the same
    purpose before running this function.
    """
    # connect to the server
    try:
        myDatabase = mysql.connector.connect(host=host, user=user, password=password)
        print("Server connection successfull!")
    except Exception as e:
        print("Failed to connect to the server")
        print(f"Error: {e}")

    # create a cursor object, remember to turn on your server
    # try:
    try:
        myDatabase = mysql.connector.connect(host=host, user=user, password=password, database=database)
    except Exception as e:
        print("There was a problem connecting to the database!")
        print(f"Error: {e}")
        myDatabase = mysql.connector.connect(host=host, user=user, password=password)
        print("Connection to the server established...")
        

    myCursor = myDatabase.cursor()
    # create a database if it does not exist
    try:
        myCursor.execute(f"CREATE DATABASE {database};")
        print("Database created successfully!")
    except Exception as e:
        print(e)
    try:
        myCursor.execute(f"use {database};")
        myCursor.execute(f"CREATE TABLE {table}(FirstName VARCHAR(30), LastName VARCHAR(30),\
                        Password VARCHAR(50), Contact int(12), Role VARCHAR(10), PRIMARY KEY(contact));")
        myCursor.execute(f"INSERT INTO {table} (FirstName, LastName, Password, Contact, Role) \
                    VALUES (\"admin\", \"admin\", \"admin\", \"admin\", \"admin\");")
        print("Table successfully created!")
    except Exception as e:
        print(e)

    return myDatabase, table, myCursor, database
def saveToDatabase(firstname, lastname, password, contact, role=None, save="save")->None:
    """
    Add details of a new empoyee
    Inputs:
    firstname:str, first name
    lastname: str, last name
    password: str, default password the employee will use to login into the system

    returns None

    """
    try:
        myDatabase, table, cursor, databasename = connectToDatabase()
        cursor.execute(f"USE {databasename};")
        print("Database changed successfully.")

        if save=="save":
            cursor.execute(f"INSERT INTO {table} (FirstName, LastName, Password, Contact, Role) \
                    VALUES (%s, %s, %s, %s, %s);", (firstname, lastname, password, contact, role))
            print("Record successfully added to the database.")
        elif save=="delete":
            cursor.execute(f"DELETE FROM {table} WHERE Contact='{contact}';")
            print("Record deleted successfully!")
        myDatabase.commit()
        cursor.close()
        myDatabase.close()


    except Exception as e:
        print(e)
def createJsonFile(data: dict = None, path:str=None,filename:str=None):
    '''
    If it is the very first person to login, the system will not allow any login with user priviledges!
    Admin must login first, and be required to set a working directory if it is not set.

    By default, create a list of users, that is, admin login, meant for the firsttime when there exists
    no database
    '''
    global pathDir
    if data is None:
        data = {"username":"admin", "password":"admin", "role":"admin", "lastname":"Admin"}
    
    if filename is None:
        filename = "employees"
    if path is None:
        path = pathDir
        # create path if it does not exist
        if not os.path.exists(path+"/jsonfile"):
            os.mkdir(path+"/jsonfile")
        path = pathDir+"/jsonfile"

    filePath = path+"/"+filename+".json"

    jsonFile = open(filePath,'w')
    json.dump(data, jsonFile)
    jsonFile.close()
    print("jsonfile created successfully")
def adminInterface(window: tk.Tk, name:str, role:str, path:str=None):
    '''

    This interface is for the admin.
    It contains the fowwling widgets.
    1. Entry Widgets
        -> First name
        -> Second name
        -> Default password
    2. Buttons
        -> add an employee
        -> view employees that attended work for a specific date

    Inputs:
    window: tk.Tk, to place Entry boxes and buttons
    '''
    # delete widgets on the window first.
    for widget in window.winfo_children():
        widget.destroy()

    if role=="user":
        l = tk.Label(master=window, text="Successfully registered for today!",
                     font=("Arial", 20), fg="green")
        l.pack(fill=tk.BOTH, expand=True)
        l.after(5000, lambda: mainWindow(mainWin))
    elif role=="admin":
        if path is None:
            path = pathDir+"/faceimages"

        # create a frame to place add and view buttons
        font = ("Arial",14)
        logoutFrame = tk.Frame(master=window, background="purple")
        welcomeLabel = tk.Label(master=logoutFrame, text=f"Welcome, {name}!",
                                background="purple",
                                fg="white",
                                font=("Arial, 50"))
        logoutButton = tk.Button(master=logoutFrame, text="Logout",
                                command=lambda: mainWindow(mainWin),
                                font=font,
                                background="red")
        welcomeLabel.pack(fill=tk.X)
        logoutButton.pack(pady=20)


        # create another frame to display employees that have attended, or,
        # fields for adding a new employee
        displayFrame = tk.Frame(master=window, bg='blue')

        # add a frame to hold buttons
        AddViewDeleteFrame = tk.Frame(master=window)
        # buttons, view attendants, add user
        addButton = tk.Button(master=AddViewDeleteFrame,
                            text="Add Employee",
                            relief=tk.RAISED,
                            font = ("Arial",16),
                            command=lambda: addEmployee(displayFrame)
                            )

        viewButton = tk.Button(master=AddViewDeleteFrame, command=lambda: view(displayFrame, path),
                            text="View attendants", relief=tk.RAISED,
                            font = ("Arial",16))
        deleteButton = tk.Button(master=AddViewDeleteFrame, command=lambda: deleteEmployee(displayFrame),
                            text="Delete Employee", relief=tk.RAISED,
                            font = ("Arial",16))
        addButton.pack(side='left', fill=tk.X, ipadx=50, expand=True)
        viewButton.pack(side='right', fill=tk.X, ipadx=50, anchor='c', expand=True)
        deleteButton.pack(side='right', fill=tk.X, ipadx=50, anchor='e', expand=True)

        # organise frames
        logoutFrame.pack(fill=tk.X)
        AddViewDeleteFrame.pack()
        displayFrame.pack(expand=True,  anchor='c')
def detectFace(name, path=None):
    lt = localtime()
    hour = str(lt.tm_hour)
    minute = str(lt.tm_min)
    second = str(lt.tm_sec)
    filename = "-".join([hour, minute, second])

    folder = checkFolder()
    if path is None:
        print(f"CURRENTLY WORKING DIRECTORY: {pathDir}")
        path = pathDir

    if not os.path.exists(path+f"/faceimages"):
        print("Faceeeeeeeeeeeeeeeeeeeeeeeeeee")
        os.mkdir(path+f"/faceimages")
        print("Folder created.....")

    path = path+f"/faceimages"
    if not os.path.exists(path+f"/{folder}"):
        # create a path directory for the day
        os.mkdir(path+f"/{folder}")


    path = path+f"/{folder}"
    print(f"Faceimage path: {path} \n======================")

    # save images in their folders according to day
    # path = pathDir+"/faceimages/"+folder

    # name the image to be saved
    saveName = path+f"/{name}_{filename}.png"

    camera = VideoCapture(0)
    faceCascade = CascadeClassifier(data.haarcascades+"/haarcascade_frontalface_default.xml")
    eyeCascade = CascadeClassifier(data.haarcascades+"/haarcascade_eye.xml")
    while True:
        faceTaken = False
        try:
            _, frame = camera.read()
            # detect faces from a gray scale image
            faces = faceCascade.detectMultiScale(cvtColor(frame, COLOR_BGR2GRAY))
            for face in faces:
                x,y, xh, yh = face
                rectangle(frame, (x,y), (x+xh, y+yh), (255,255,0))
                roi = frame[y:y+yh, x:x+xh]
                eyes = eyeCascade.detectMultiScale(cvtColor(roi, COLOR_BGR2GRAY))
                if len(eyes)>=0:
                    imwrite(saveName, frame)
                    print(f"Face saved successfully {saveName}!")
                    faceTaken = True
                    break

            imshow("Frame", frame)
            if faceTaken:
                break
        except Exception as e:
            print(e)
            print("No image was saved")

            camera.release()
            print("Camera successfully closed.")
            break
    camera.release()
    destroyAllWindows()
def login(username, password):
    global pathDir, mainWin, loginError
    global row, col
    loginError.config(text="", bg="light green")
    # read the json file to confirm the system is not fresh
    jsonPath = pathDir+"/jsonfile"
    filename = "employees"
    faceImagesPath = pathDir+"/faceimages"

    try:
        jsonFile = open(jsonPath+f"/{filename}.json",'r')
        print("File read successfully...")
    except:
        '''There is no file named jsonfile.
        Set up the working directory by creating folders to work with'''
        
        if username=="admin" and password=="admin":
            detectFace(username)
            print("Creating a json file...")
            loginError.config(text="Please wait while working directory is being prepared...",
                            font=("Arial, 10"), fg="grey")
            # create a folder for the json file if it does not exist
            if not os.path.exists(jsonPath):
                os.mkdir(jsonPath)

            # create a folder for saving images taken by the camera
            if not os.path.exists(faceImagesPath):
                os.mkdir(faceImagesPath)

            # Read from the database, information of employees, so that a file is prepared for
            # reference
            myDatabase, table, myCursor, databasename = connectToDatabase()
            
            # put default admin in the database
           
            # read from the database table
            myCursor.execute(f"SELECT Contact, LastName, Password, Role FROM {table};")
            print("Table empinfo read =======================")
            dictionary = {}
            for row in myCursor:
                # in row, it is information with contact, lastname, password, role respectively
                rowDetails = list(row) # convert the tuple into a list
                dictionary[str(rowDetails[0])] = {"lastname":rowDetails[1], "password":rowDetails[2], "role":rowDetails[3]}
            print(dictionary)

            # Update the json file
            createJsonFile(dictionary,jsonPath,filename)
            loginError.config(text="Successfully set up the system directory.",
                          font=("Arial, 12"), fg="green")
        
            adminInterface(mainWin, username,"admin")
            jsonFile = open(jsonPath+"/employees.json",'r')
        else:
            loginError.config(text="Please contact the admin for assistance.",
                          font=("Arial, 12"), fg="red")
            return
    # after setting up working directory, remove the message
    loginError.config(text="  ", font=("Arial, 10"), fg="grey")

    data = json.load(jsonFile)
    print(str(data))
    createJsonFile(data)
    # check if the username exists in the database and continue to login
    # Read from the database, information of employees, so that a file is prepared for
    # reference
    myDatabase, table, myCursor, databasename = connectToDatabase()
    
    # put default admin in the database
    
    # read from the database table
    myCursor.execute(f"SELECT Contact, LastName, Password, Role FROM {table};")
    print("Table empinfo read =======================")
    dictionary = {}
    for row in myCursor:
        # in row, it is information with contact, lastname, password, role respectively
        rowDetails = list(row) # convert the tuple into a list
        dictionary[str(rowDetails[0])] = {"lastname":rowDetails[1], "password":rowDetails[2], "role":rowDetails[3]}
    print(dictionary)
    createJsonFile(dictionary)
    try:
        # loginError.config(text="")
        if password==data[username]["password"]:
            print("login successfull===============")
            loginError.config(text="Wait while the phhot is being taken...")
            detectFace(data[username]["lastname"])
            print("Face detected==============")

            adminInterface(mainWin,data[username]["lastname"], data[username]["role"])
        else:
            loginError.config(text="Incorrect username or password")
            # raise ValueError("You supplied a wrong username or password!\n Please check and try again")
    except Exception as e:
        print(e)
        message = "You supplied a wrong username or password!\n Please check and try again"
        loginError.config(text=message, font=("Arial, 14"), fg="red")
def mainWindow(mainWin):
    global row
    row=3
    for widget in mainWin.winfo_children():
        widget.destroy()
    mainWin.title("Face capture based attendance system - Login")
    mainWin.config(background="light green")

    loginFrame = tk.Frame(master=mainWin, bg='light green', border=12, height=50)

    # create labels and their buttons
    # labels
    usernameLabel = tk.Label(master=loginFrame, text="Username: ")
    # usernameLabel.bind("<configure>", lambda e: usernameLabel.configure(width=e.width-10))
    passwordLabel = tk.Label(master=loginFrame, text="Password: ")

    # entry boxes
    global loginError
    loginError = tk.Label(master=loginFrame,text="", bg="light green")
    usernameEntry = tk.Entry(master=loginFrame, width=50)
    passwordEntry = tk.Entry(master=loginFrame, width=50, show="*")

    # create a login in button
    loginButton = tk.Button(master=loginFrame, text="Login", width=30,
                            command=lambda : login(usernameEntry.get().strip(), passwordEntry.get()))

    ####################################placements##########################################
    # organise widgets accordingly
    loginError.grid(row=row, column=col+1)
    incrementRow()
    usernameLabel.grid(row=row, column=col)
    usernameEntry.grid(row=row, column=col+1)
    incrementRow()

    passwordLabel.grid(row=row, column=col, padx=padx, pady=pady)
    passwordEntry.grid(row=row, column=col+1, padx=padx, pady=pady)
    incrementRow()

    loginButton.grid(row=row, column=col+1, padx=padx, pady=pady-10)
    incrementRow()

    loginFrame.pack(expand=True, anchor='c')
def addEmployee(frame:tk.Frame, save="save"):
    global mainWin
    mainWin.title("Add Employe")
    for widget in frame.winfo_children():
        widget.destroy()
    frame['bg']="green"
    # labels

    bg = 'light blue'
    firstNameLabel = tk.Label(master=frame, text="First name: ", bg=bg)
    lastNameLabel = tk.Label(master=frame, text="Last name: ", bg=bg)
    passwordLabel = tk.Label(master=frame, text="Password: ", bg=bg)
    contactLabel = tk.Label(master=frame, text="ID: ", bg=bg)
    roleLabel = tk.Label(master=frame, text="Role: ", bg=bg)

    # Entry boxes
    firstNameEntry = tk.Entry(master=frame, width=50)
    lastNameEntry = tk.Entry(master=frame, width=50)
    passwordEntry = tk.Entry(master=frame, width=50, show="*")
    contactEntry = tk.Entry(master=frame, width=50)
    roleEntry = tk.Entry(master=frame, width=50)

    # organise widgets on the main window
    global row
    row, col = 0, 0
    padx, pady = 10, 10
    firstNameLabel.grid(row=row, column=col, padx=padx, pady=pady)
    firstNameEntry.grid(row=row, column=col+1)

    incrementRow()

    lastNameLabel.grid(row=row, column=col, padx=padx, pady=pady)
    lastNameEntry.grid(row=row, column=col+1, padx=padx, pady=pady)
    incrementRow()

    passwordLabel.grid(row=row, column=col, padx=padx, pady=pady)
    passwordEntry.grid(row=row, column=col+1, padx=padx, pady=pady)
    incrementRow()

    contactLabel.grid(row=row, column=col, padx=padx, pady=pady)
    contactEntry.grid(row=row, column=col+1, padx=padx, pady=pady)
    incrementRow()

    roleLabel.grid(row=row, column=col, padx=padx, pady=pady)
    roleEntry.grid(row=row, column=col+1, padx=padx, pady=pady)
    incrementRow()

    # add a button to click and save to database
    saveButton = tk.Button(master=frame, text="save", font=("Arial",15),
                           command=lambda: saveToDatabase(firstNameEntry.get().strip(),
                                                  lastNameEntry.get().strip(),
                                                  passwordEntry.get(),
                                                  contactEntry.get(),
                                                  roleEntry.get().strip(),
                                                  save))
    saveButton.grid(row=row, column=col+1, padx=padx, pady=pady)
def deleteEmployee(frame:tk.Frame, save="delete"):
    global mainWin
    mainWin.title("Delete Employe")
    # clear the frame
    for widget in frame.winfo_children():
        widget.destroy()

    frame['bg']="red"
    # labels

    bg = 'light green'
    firstNameLabel = tk.Label(master=frame, text="First name: ", bg=bg)
    lastNameLabel = tk.Label(master=frame, text="Last name: ", bg=bg)
    passwordLabel = tk.Label(master=frame, text="Password: ", bg=bg)
    contactLabel = tk.Label(master=frame, text="ID: ", bg=bg)
    roleLabel = tk.Label(master=frame, text="Role: ", bg=bg)

    # Entry boxes
    bgEntry = "purple"
    firstNameEntry = tk.Entry(master=frame, width=50, state="readonly", bg=bgEntry, highlightcolor="BLACK")
    lastNameEntry = tk.Entry(master=frame, width=50, state="disabled", bg=bgEntry)
    passwordEntry = tk.Entry(master=frame, width=50, show="*", state="disabled", bg=bgEntry)
    contactEntry = tk.Entry(master=frame, width=50)
    roleEntry = tk.Entry(master=frame, width=50, state="disabled", bg=bgEntry)

    # organise widgets on the main window
    global row
    row, col = 0, 0
    padx, pady = 10, 10
    firstNameLabel.grid(row=row, column=col, padx=padx, pady=pady)
    firstNameEntry.grid(row=row, column=col+1)
    incrementRow()

    lastNameLabel.grid(row=row, column=col, padx=padx, pady=pady)
    lastNameEntry.grid(row=row, column=col+1, padx=padx, pady=pady)
    incrementRow()

    passwordLabel.grid(row=row, column=col, padx=padx, pady=pady)
    passwordEntry.grid(row=row, column=col+1, padx=padx, pady=pady)
    incrementRow()

    contactLabel.grid(row=row, column=col, padx=padx, pady=pady)
    contactEntry.grid(row=row, column=col+1, padx=padx, pady=pady)
    incrementRow()

    roleLabel.grid(row=row, column=col, padx=padx, pady=pady)
    roleEntry.grid(row=row, column=col+1, padx=padx, pady=pady)
    incrementRow()

    # add a button to click and save to database
    saveButton = tk.Button(master=frame, text="Delete", font=("Arial",15),
                           command=lambda: saveToDatabase('',
                                                  '',
                                                  '',
                                                  contactEntry.get().strip(),
                                                  roleEntry.get(),
                                                  save))
    saveButton.grid(row=row, column=col+1, padx=padx, pady=pady)
def view(frame:tk.Frame, path:str, date: str = None):
    global mainWin
    if date is None:
        date = checkFolder()
    path += f"/{date}"

    mainWin.title("View staff at work")

    for widget in frame.winfo_children():
        widget.destroy()
    # mainWin.state("zoomed")
    frame['bg']="light green"
    myDatabase, table, myCursor, database = connectToDatabase()
    myCursor.execute(f"SELECT Contact, FirstName, LastName, Password FROM {table}")

    # create a tk variable to hold the name of the label
    nameLabel = tk.StringVar()
    image_address_dict = {}
    attendants = []

    # path = r"E:\PROJECTS\academic\INNOCENT\face capture system\images"
    for imagename in os.listdir(path):
        image_address_dict[imagename] = path+"/"+imagename
        attendants.append(imagename)

    # for d in myCursor:
    #     print(d)
        # attendants.append(d[0])

    def searchDate(listItems):
        image_address_dict.clear()
        attendants.clear()
        specificDate = askdirectory()
        for imagename in os.listdir(specificDate):
            image_address_dict[imagename] = specificDate+"/"+imagename
            attendants.append(imagename)
        searchDayEntry.delete(0,tk.END)
        searchDayEntry.insert(0, specificDate) # browse the directory
        listItems.set(value=[image for image in os.listdir(specificDate)])


    # create a tk variable to hold list of items
    listItems = tk.Variable(value=[key for key in image_address_dict])
    # create a frame to hold the search widgets
    searchFrame = tk.Frame(master=frame, bg="blue")
    searchLabel = tk.Label(master=searchFrame, text="Search specific date?", font=("Arial, 14"),
                           bg="light green")
    searchDayEntry = tk.Entry(master=searchFrame, text="Today's attendance.", width=100)
    searchButton = tk.Button(master=searchFrame, text="Browse...", command=lambda: searchDate(listItems))

    # ORGANISE THE WIDGETS ON THE FRAME

    searchLabel.grid(row=0, column=0, padx=10, pady=10 )
    searchDayEntry.grid(row=1, column=0, padx=10, pady=10)
    searchButton.grid(row=1, column=1, padx=10, pady=10)
    searchFrame.pack(fill=tk.X, side=tk.TOP) ########## PLACE THE WIDGET

    # create a frame for others, image and its label
    viewImageFrame = tk.Frame(master=frame, bg='light green')
    nameList = tk.Listbox(master=viewImageFrame, width=50, listvariable=listItems)

    # create a function bind the listbox
    def selectedItem(event):
        selected = nameList.curselection()[0]
        # set the name of the label to the selected person
        nameLabel.set(attendants[selected].split(".")[0]) # name to put on the image as caption
        path = image_address_dict[attendants[selected]]
        print(path)
        pilImage = Image.open(path).resize((300,300))
        image = ImageTk.PhotoImage(pilImage)
        imageHolderLabel = tk.Label(master=viewImageFrame, image=image)
        imageHolderLabel.image=image
        imageHolderLabel.grid(row=0, column=3)

    nameList.bind("<<ListboxSelect>>",selectedItem)

    imageName = tk.Label(master=viewImageFrame, textvariable=nameLabel, bg="white")

    nameList.grid(row=0, column=0)
    imageName.grid(row=1, column=3)
    viewImageFrame.pack(fill=tk.BOTH)
    # nameList.pack()
    # imageHolder.pack()
    # imageLabel.pack()
    print("Image view activtated")


if __name__=="__main__":
    print("main interface running")
    # global pathDir, loginError
    pathDir = os.getcwd()
    print(pathDir)

    loginError = None

    row, col= 0, 0
    padx, pady = 10, 20

    mainWin = tk.Tk()

    # mainWin.state("zoomed")
    mainWin.geometry("500x400")
    # mainWin.resizable(1000, 800)  # disable resizing the window
    mainWindow(mainWin)
    mainWin.mainloop()
