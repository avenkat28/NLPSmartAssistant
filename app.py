import json
import datetime
import nltk
import os
import re
from nltk.tokenize import regexp_tokenize, word_tokenize
from timefhuman import timefhuman
from datetime import timedelta

from flask import Flask, jsonify, request
from http import HTTPStatus


app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'hello test'

@app.route("/extract-meetinginfo", methods=["POST"])
def extract_meetinginfo():
    #msg = json.loads(request.data)
    data = request.get_json()
    msgText = data.get("message")

    ## Start parse for With Person
    patternForWith = r"with\s+(\w+)\s?(\w+)?"
    withMatched = regexp_tokenize(msgText, patternForWith)
    #print("withMatched is: ", withMatched)

    withPersonList = []
    withPerson = " "
    for tup in withMatched:
        for ent in tup:
            #print("entity is: ", ent)
            tagged_ent = nltk.pos_tag(word_tokenize(ent))
            #print("tagged_ent is: ", tagged_ent)
            for word, tag in tagged_ent:
                #print("word is: ", word)
                #print("tag is: ", tag)
                if (re.match("^NN[P|PS|S]?$", tag)):
                    withPersonList.append(word)

    withPerson = withPerson.join(withPersonList)
    #print("withPerson: ", withPerson)
    ## End Parse for With Person

    ## Start parse for meeting date

    # First normalize the date before passing to timefhuman
    # timefhuman library has a bug if the input contains a digit day followed by th e.g. 25th.
    # it works fine with st, nd and rd. So, we should get rid of th if th follows a number.
    # Let's do it for st, rd and nd as well for consistency

    # Removed "with <withPerson>" from the msgText before performing date parsing
    #print("msgText is: ", msgText)
    normalizedText1 = msgText.replace("with " + withPerson, " ")
    #print("normalizedText1 is: ", normalizedText1)

    normalizedText = re.sub('(\d+\s?)(th|st|nd|rd)\s?', r'\1 ', normalizedText1)
    #print("normalized text is: ", normalizedText)

    parsedTime = timefhuman(normalizedText)
    #print("parsed dateTime: ", parsedTime)

    # parsedTime could be just a string or a tuple of dateTime objects or list of dateTime.dateTime objects or a list containing a dateTime.dateTime object and a tuple of dateTime.dateTime objects
    #print("Type of parsedTime is: ", type(parsedTime))

    parsedTimeList = []
    meetingStartTime = datetime.datetime.now()
    meetingEndTime = meetingStartTime + timedelta(hours=1)

    if (isinstance(parsedTime, datetime.datetime)):
        meetingStartTime = parsedTime
        # set the default block to be 1 hour
        meetingEndTime = meetingStartTime + timedelta(hours=1)
        #print("Meeting start time is: ", meetingStartTime)
        #print("Meeting end time is: ", meetingEndTime)
    elif (isinstance(parsedTime, list)):
        # iterate through the list
        for i in parsedTime:
            if (isinstance(i, datetime.datetime)):
                parsedTimeList.append(i)
            elif (isinstance(i, tuple)):
                for t in i:
                    if (isinstance(t, datetime.datetime)):
                        parsedTimeList.append(t)
    elif (isinstance(parsedTime, tuple)):
        for t in parsedTime:
            if (isinstance(t, datetime.datetime)):
                parsedTimeList.append(t)
    if (len(parsedTimeList) > 0):
        #print("parsedTimeList is: ", parsedTimeList)
        sortedParsedTimeList = []
        # sort the parsedTimeList in descending order
        sortedParsedTimeList = sorted(parsedTimeList, reverse=True)
        #print("Sorted parsedTimeList is:", sortedParsedTimeList)

        # compute the start and end times
        sortedTimeListLen = len(sortedParsedTimeList)
        if (sortedTimeListLen > 0):
            meetingYear = sortedParsedTimeList[0].year
            meetingMonth = sortedParsedTimeList[0].month
            meetingDay = sortedParsedTimeList[0].day
            startTimeHour = sortedParsedTimeList[0].hour
            startTimeMin = sortedParsedTimeList[0].minute
            endTimeHour = (sortedParsedTimeList[0] + timedelta(hours=1)).hour
            endTimeMin = (sortedParsedTimeList[0] + timedelta(hours=1)).minute
            if (sortedTimeListLen == 2):
                endTimeHour = startTimeHour
                endTimeMin = startTimeMin
                startTimeHour = sortedParsedTimeList[1].hour
                startTimeMin = sortedParsedTimeList[1].minute
            elif (sortedTimeListLen > 2):
                startTimeHour = sortedParsedTimeList[2].hour
                startTimeMin = sortedParsedTimeList[2].minute
                endTimeHour = sortedParsedTimeList[1].hour
                endTimeMin = sortedParsedTimeList[1].minute
            # Now construct the start and end times in datetime format
            meetingStartTime = datetime.datetime(meetingYear, meetingMonth, meetingDay, startTimeHour, startTimeMin)
            #print("Meeting start time is: ", meetingStartTime)
            meetingEndTime = datetime.datetime(meetingYear, meetingMonth, meetingDay, endTimeHour, endTimeMin)
            #print("Meeting end time is: ", meetingEndTime)

    # Construct response json
    res = {
        "meetwith": withPerson,
        "meetstarttime": meetingStartTime,
        "meetendtime": meetingEndTime
    }
    return jsonify(res)


if __name__ == '__main__':
    app.run()