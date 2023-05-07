import cv2
import numpy as np
import face_recognition
import csv
import os
import time
from datetime import datetime
from flask import Flask, request
from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client()
stop_flag = False
# Define user ID
# 'MeB18mHqcEW1gWYxLTEYhBcehh42'


app = Flask(__name__)


@app.route('/stopit')
def stopit():
    print("stopit")
    global stop_flag
    stop_flag = True
    return "OK"


@app.route('/run-script')
def run_script():
    userid = request.args.get('userid')
    classname = request.args.get('name')
    print(classname)
    # Start the loop in a separate thread so the Flask app can continue running
    from threading import Thread
    loop_thread = Thread(target=loop, args=(userid, classname))
    loop_thread.start()
    return "OK"


def loop(userid, classname):
    global stop_flag
    stop_flag = False

    # Function to load and encode images
    def load_image(image_file, name):
        image = face_recognition.load_image_file(image_file)
        encoding = face_recognition.face_encodings(image)[0]
        return encoding, name

    # Load the video capture
    video_capture = cv2.VideoCapture(0)

    # Path of the folder with image files
    path = "C:/Users/91902/Downloads/Telegram Desktop/Dataset_pics/"

    # Get all the files in the folder
    files = os.listdir(path)

    # Get only the image files in the folder
    image_files = [(path + file, file.split(".")[0]) for file in files if file.endswith((".jpeg", ".jpg"))]

    # Load and encode the images
    face_data = [load_image(image_file, name) for image_file, name in image_files]
    known_face_encodings, known_face_names = zip(*face_data)

    students = list(known_face_names)

    face_locations = []
    face_encodings = []
    face_names = []

    now = datetime.now()
    current_date = now.strftime("%d-%m-%Y")

    f = open(classname + '.csv', 'w+', newline='')
    Inwriter = csv.writer(f)

    # Write the header row in the excel
    Inwriter.writerow(["Name", "Date", "Time of entry", "Time of exit"])

    # Define the start time
    start = time.time()

    # Initialize the state of each person in the frame
    person_states = {}
    person_entry_exit_times = {}
    for name in known_face_names:
        person_states[name] = {
            "last_seen_time": None,
            "in_frame": False
        }
        person_entry_exit_times[name] = {
            "entry_time": None,
            "exit_time": None
        }

    while True:
        _, frame = video_capture.read()
        if stop_flag:
            break
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_small_frame, model="mmod")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        face_names = []

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)
            if name in known_face_names:
                if name in students:
                    now = datetime.now()
                    current_time = now.strftime("%H:%M:%S")

                    # Update the state of the person in the frame
                    state = person_states[name]
                    if not state["in_frame"]:
                        state["last_seen_time"] = now
                        state["in_frame"] = True
                        person_entry_exit_times[name]["entry_time"] = current_time
                    else:
                        last_seen_time = state["last_seen_time"]
                        elapsed_time = (now - last_seen_time).total_seconds()
                        if elapsed_time > 60:
                            state["last_seen_time"] = now
                            Inwriter.writerow([name, current_date, current_time, ""])
                        else:
                            state["in_frame"] = False
                            state["last_seen_time"] = None
                            exit_time = current_time
                            for row in reversed(list(csv.reader(open(classname + '.csv')))):
                                if row[0] == name and row[3] == '':
                                    entry_time = row[2]
                                    break
                            else:
                                entry_time = current_time
                                Inwriter.writerow([name, current_date, entry_time, exit_time])

        # Show the frame with name tags
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print('stopped')
    f.flush()
    f.close()

    with open(classname + '.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = []
        for row in reader:
            data.append(row)


    print(data)
    print("Success")

    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == '_main_':
    app.run(host='0.0.0.0',port=5000)