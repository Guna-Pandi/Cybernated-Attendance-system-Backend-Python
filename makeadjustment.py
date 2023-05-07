import csv
from datetime import datetime, timedelta
from flask import Flask, request
from google.cloud import firestore

app = Flask(__name__)

db = firestore.Client()


@app.route('/run2-script')
def run_script():
    userid = request.args.get('userid')
    classname = request.args.get('name')
    print(classname)
    now = datetime.now()
    current_date = now.strftime("%d-%m-%Y")

    # Load the CSV file
    with open(classname + '.csv', 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Create a dictionary to store the unique entries
    unique_entries = {}

    # Iterate through each row in the CSV file
    for row in rows[1:]:
        name = row[0]
        entry_time = row[2]
        exit_time = row[3]

        # Check if the name is already in the dictionary
        if name not in unique_entries:
            # Add the row to the dictionary
            unique_entries[name] = {'entry_time': entry_time, 'exit_time': exit_time}
        else:
            # Update the time of exit in the dictionary
            unique_entries[name]['exit_time'] = exit_time

    # Write the unique entries to a new CSV file
    with open(classname + '_unique.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Date", "Time of entry", "Time of exit", "Duration", "Attendance"])

        # Iterate through the unique entries
        for name in unique_entries:
            entry_time = unique_entries[name]['entry_time']
            exit_time = unique_entries[name]['exit_time']

            # Calculate the duration
            duration = ""
            if entry_time and exit_time:
                entry_datetime = datetime.strptime(entry_time, "%H:%M:%S")
                exit_datetime = datetime.strptime(exit_time, "%H:%M:%S")
                duration_timedelta = exit_datetime - entry_datetime
                duration = str(duration_timedelta)

                # Mark attendance as present or absent based on duration
                attendance = "Present" if duration_timedelta >= timedelta(seconds=10) else "Absent"
                #minutes=41

            writer.writerow([name, current_date, entry_time, exit_time, duration, attendance])

    # ... (the rest of your code)

    with open(classname + '_unique.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = []
        for row in reader:
            data.append(row)

    user_ref = db.collection('CSV').document(userid)
    parent_col_ref = db.collection('CSV').document(userid).collection('csv_files')
    parent_doc_ref = parent_col_ref.document(classname)
    parent_doc_ref.set({'1': 'hello', '2': 'hi'})
    col_ref = parent_doc_ref.collection('data')

    # Add CSV data as document in collection
    i = 0
    for doc in data:
        i += 1
        col_ref.document(str(i)).set(doc)

    return "500"


if __name__ == '_main_':
    app.run(host='0.0.0.0', port=6000)