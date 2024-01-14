from flask import Flask, render_template, request
import ratemyprofessor ## https://pypi.org/project/RateMyProfessorAPI/
import math
import json

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html', spellingErrors=[])

def getProfessorMultiplier(name): ## Given last name of professor, gives back a float multiple based on how good they are
    rating = 0.0
    professor = ratemyprofessor.get_professor_by_school_and_name(
        ratemyprofessor.get_school_by_name("UCSB"), name)
    if professor is not None:
        rating = (((professor.rating / 5.0) - 0.5)) * (2 / math.pi) * math.atan(.5 * professor.num_ratings)
    return rating

def parseClassInput(userInfo): ## Takes in input dictionary and outputs list of class ids
    classList = []
    courseCount = int(userInfo["coursecount"])
    sillyTuple = []
    for i in range(1, courseCount + 1):
        sillyTuple.append(userInfo["code" + str(i)])
        sillyTuple.append((userInfo.get("major" + str(i), False) == "on"))
        classList.append(sillyTuple[0])
        classList.append(sillyTuple[1])
        sillyTuple.clear()
    return classList
    
def sillyStartAndEnd(timeString): ##takes in a string representing time and output a tuple with start time and end time
    startAndEnd = timeString.split('-')
    master = []
    for time in startAndEnd:
        x = time.split()
        for y in x:
            z = y.split(":")
            master.append(z)
    try: ##if the times are random nonsense like harold or TBA, returns -1, -1, this is sanitized later
        startTime = float(master[0][0]) + float(master[0][1]) / 60
        endTime = float(master[2][0]) + float(master[2][1]) / 60
        if master[1][0] == 'PM' and master[0][0] != "12":
            startTime += 12
        if master[3][0] == 'PM' and master[2][0] != "12":
            endTime += 12
        timeTuple = (startTime, endTime)
    except:
        return(-1,-1)
    return timeTuple 

@app.route("/schedule")
def schedule():
    f = open("static/courses.json") ##opens file
    database = json.load(f) ##loads file into python dictionary

    wantedClases = [] ##This list containes class information of wanted classes from .json file
    masterInfo = [] ##This is the final output list --- must be ported to sceduale maker
    spellingErrors = [] ##contains any spelling errors
    

    test = { ##Test is incoming dictionary, replace this with incomign data
     "code1": "ECE 5",
     "code2": "ECE 130A",
    "code3": "ECE 152A",
     "code4": "ECE 10B",
    "count": "3",
    "coursecount": "4",
    "dinner": "on",
    "earliest": "10",
    "latest": "19",
    "lunch": "on",
    "major1": "on",
    "majorcount": "1"
    }

    getInput = request.args
    

    ##brings earliest and latest parameters to output, also brings data from .json to wanted classes. if a class doesnt exist, moves it to spelling errors
    masterInfo.append(getInput["earliest"])
    masterInfo.append(getInput["latest"])
    masterInfo.append(getInput["count"])
    masterInfo.append(getInput["majorcount"])
    classInput = parseClassInput(getInput)
    i = 0
    while i < len(classInput):
        wantedClases.append(classInput[i])
        wantedClases.append(classInput[i + 1])
        try:
            wantedClases.append(database[classInput[i]])
        except:
            spellingErrors.append(classInput[i])
            wantedClases.append("error")

        i += 2
    ##checks for errors and skips it
    i = 0
    while (i < len(wantedClases)):
        
        try:
            if wantedClases[i + 2] == "error":
                i = i + 3
                continue
        except:
                x = 1 ##does not do anything, python was angry

        for j in range(len(wantedClases[i + 2])): 
            ## Converts the time given to 24 hr floats
            timeString = wantedClases[i + 2][j]['time']
            timeTuple = sillyStartAndEnd(timeString)

            if timeTuple[0] == -1:
                continue
            ##checks for major classes
            sections = []
            for sus in wantedClases[i+2][j]['sections']:
                induvidualSection = []
                induvidualSection.append(sus['days'])
                timeTuple2 = sillyStartAndEnd(sus['time'])
                if timeTuple2[0] == -1:
                    continue
                induvidualSection.append(timeTuple2[0])
                induvidualSection.append(timeTuple2[1])
                sections.append(induvidualSection)

            ##adds a while class to output array
            ## so ("class","mwf","starthr","endhr",t/f,rating, prof, sections)
            masterInfo.append((wantedClases[i], wantedClases[i + 2][j]['days'], timeTuple[0], timeTuple[1], wantedClases[i + 1], getProfessorMultiplier(wantedClases[i + 2][j]['prof']), wantedClases[i + 2][j]['prof'], sections))
        i = i + 3

    ##final output if no problems   
    if len(spellingErrors) != 0:
        return render_template('home.html', spellingErrors=spellingErrors)
    
    def generate_schedules(classes, num_classes):
        schedules = []
        current_schedule = []

        def backtrack(index):
            nonlocal current_schedule

            # Base case: if the current schedule is valid and has the desired number of classes, add it to the list of schedules
            if len(current_schedule) == num_classes and is_valid_schedule(current_schedule):
                schedules.append(list(current_schedule))

            # Explore all possible combinations
            for i in range(index, len(classes)):
                current_schedule.append(classes[i])
                backtrack(i + 1)  # Recur with the next index
                current_schedule.pop()  # Backtrack

        def is_valid_schedule(schedule):
            # Checking if same class name (same class cannot exist in same schedule)
            for i in range(len(schedule)):
                for j in range(i + 1, len(schedule)):
                    if is_same_class(schedule[i][0], schedule[j][0]) is True:
                        return False # There is conflict
            # Implement validation logic to check for conflicts in days and times
            for i in range(len(schedule)):
                for j in range(i + 1, len(schedule)):
                    if has_common_letter(schedule[i][1],schedule[j][1]) and do_times_overlap(schedule[i][2:], schedule[j][2:]):
                        return False # There is conflict
            return True
        
        def has_common_letter(string1, string2): # Checking if classes share a day
            for char in string1:
                if char in string2:
                    return True
            return False
        
        def do_times_overlap(time1, time2):
            # Helper function to check if two time intervals overlap
            return max(time1[0], time2[0]) < min(time1[1], time2[1])
        
        def is_same_class(class1, class2): # checks if 2 classes are the same but different professor
            if class1 == class2:
                return True
            else:
                return False

        # Start the backtracking process
        backtrack(0)

        return schedules

    # Example usage: (class name, days, start time, end time, major, prof rating)
    '''
    available_classes = [
        ('ECE 5', 'MW', 15.5, 16.75, True, 0.0005090244539196737, 'BREWER F', [['F', 12.0, 14.833333333333334], ['T', 17.0, 19.833333333333332], ['F', 9.0, 11.833333333333334], ['W', 9.0, 11.833333333333334]]), 
        ('ECE 130A', 'MW', 9.5, 10.75, False, -0.0, 'MADHOW U', [['F', 9.0, 10.833333333333334], ['F', 14.0, 15.833333333333334], ['F', 11.0, 12.833333333333334], ['F', 16.0, 17.833333333333332]]), 
        ('ECE 152A', 'TR', 9.5, 10.75, False, 0.0012730698201945591, 'KIM B', [['R', 13.0, 15.833333333333334], ['W', 16.0, 18.833333333333332]]), 
        ('ECE 10B', 'TR', 17.0, 18.25, False, 0.0, 'SCHOW C L', [])
        ]
        '''

    

    available_classes = masterInfo[4:]


    num_input_classes = int(masterInfo[2]) # USER INPUT: NUMBER OF CLASSES FOR EACH SCHEDULE
    all_schedules = generate_schedules(available_classes, num_input_classes)

    # ranking schedules
    # From the avalible schedules, rank them based on the following criteria: major (+30), prof. rating(+rating),
    # # no class before __ (+3), no class after __ (+3)

    def count_true_tuples(class_list):
        # Count the number of True values in the fifth element of each tuple (if major class)
        true_count = sum(1 for class_info in class_list if class_info[4])
        return true_count

    def rank_classes(all_schedules):
        ranked_classes = []

        for schedule in all_schedules:
            points = 0
            true_count = count_true_tuples(schedule)
            # print(f"Number of True values: {true_count}")

            if true_count == int(masterInfo[3]): # USER INPUT: NUMBER OF MAJOR CLASSES
                points += 30

            # Find start time and end time for each schedule
            start_time = min(class_info[2] for class_info in schedule)
            end_time = max(class_info[3] for class_info in schedule)

            # Assign additional points based on start time and end time criteria (user inputted)
            if start_time >= int(masterInfo[0]):  # USER INPUT: EARLISET START TIME FOR CLASSES
                points += 3

            if end_time <= int(masterInfo[1]):  # USER INPUT: LATEST TIME (END) FOR CLASSES
                points += 3
            
            rating = [class_info[5] for class_info in schedule]
            rating_after_multiplier = [element * 10 for element in rating]
            rating_points = sum(rating_after_multiplier)
            points += rating_points

            ranked_classes.append({'schedule': schedule, 'points': points})

        # Rank classes based on points
        ranked_classes = sorted(ranked_classes, key=lambda x: x['points'], reverse=True)

        return ranked_classes

    result = rank_classes(all_schedules) 

    # PRINTS OUT SORTED SCHEDULES BASED ON POINTS
    schedule_string = ""
    for index, entry in enumerate(result):
        schedule_string += (f"Rank {index + 1}: Schedule {entry['schedule']} - Points: {entry['points']}")

    ranked_schedules = [data['schedule'] for data in result]
    

    # if len(ranked_schedules) <= 4:
    #     num_top_lectures = len(ranked_schedules)
    # else:
    #     num_top_lectures = math.ceil(math.sqrt(len(ranked_schedules)))
    # print(num_top_lectures)

    # top_schedules = (ranked_schedules[:num_top_lectures])
    # print(top_schedules)
    num_ranked_schedules = len(ranked_schedules)
    #print(num_ranked_schedules)

    num_display_schedules = min(num_ranked_schedules, 4)

    return render_template('schedule.html', schedule_string=json.dumps(ranked_schedules))
    return schedule_string
