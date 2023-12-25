'''
    SpriTy - V1.0
    This is a small program to collect gasoline prices in a to ne specified region in Austria.
    It uses the public API of Austria's E-Control service. 
'''

''' IMPORTS '''

import csv
import os
from datetime import datetime
import json
import requests
import schedule
import string
import sys
import time
import smtplib, ssl
from email.message import EmailMessage
from station import Station

''' STATE '''

# Base API URL
apiURL: string = "http://api.e-control.at/sprit/1.0"

# Endpoint for all regions.
apiEndpointRegions: string = "/regions"

# Endpoint for region units.
apiEndpointRegionUnits: string = "/regions/units"

# Endpoint for a ping.
apiEndpointPing: string = "/ping"

# Endpoint for gas station search by adress.
apiEndpointSearchByAdress: string = "/search/gas-stations/by-address"
apiEndpointSearchByAdressParams: string = "?latitude=%PARAM_LAT%&longitude=%PARAM_LON%&fuelType=%PARAM_FUELTYPE%&includeClosed=%PARAM_INCLUDECLOSED%"
apiURLSearchByAdress: string = apiURL + apiEndpointSearchByAdress + apiEndpointSearchByAdressParams

# Endpoint for gas station search by region
apiEndpointSearchByRegion: string = "/search/gas-stations/by-region"

# Timestamp etc. for last api call
apiCallTimestamp: float = None
apiCallDateTime: string = None

''' FUNCTIONS '''

def main():
    '''Main entry point of application.'''

    # Print status
    print("*** Welcome to SpriTy! ***")

    # Set mode
    mode: string = "single"

    # Get argument
    args: list = sys.argv
    if len(args) > 1:
        if args[1] == "scheduled":
            mode = "scheduled"

    if mode == "scheduled":
        # Print status
        print("Switching to scheduled mode.")

        # Configure schedule
        schedule.every().day.at("09:00").do(job)
        schedule.every().day.at("18:00").do(job)

        # For debugging schedule every minute
        #schedule.every(1).minute.do(job)

        # Start scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)

    else:
        # Print status
        print("Switching to single call mode.")
        
        # Run job just one time.
        job()

def job():
    ''' Job-function, that is executed by the scheduler and kicks of the fetching. '''

    # Set call time
    now = datetime.now()
    apiCallTimestamp = now.timestamp()
    apiCallDateTime = now.strftime("%d.%m.%Y %H:%M:%S")

    # Print status
    print(apiCallDateTime + " Fetching prices...")

    # Read station list
    stationFile = open("stationIds.json")
    stationList = json.load(stationFile)

    # Fetch stations, filter and update prices file.
    allStations = searchStationsByCoords(46.59431, 13.85228, "DIE", False)
    filteredStations = filterStations(allStations, stationList, apiCallTimestamp, apiCallDateTime)
    allRows = writeToCSV(filteredStations)

    # Print status
    print(now.strftime("%d.%m.%Y %H:%M:%S") + " Fetching finished - file written.")

    # Send update mail
    sendMail(allRows)

def getAllRegions() -> list:
    '''Get all available regions.'''

    print("Performing call to: " + (apiURL + apiEndpointRegions))
    response = requests.get(apiURL + apiEndpointRegions)
    regionList = response.json()
    return regionList

def searchStationsByCoords(lat: float, lon: float, fuelType: string, includeClosedStations: bool) -> list:
    '''Search for gas stations by longitude and latitude.'''

    reqUrl = apiURLSearchByAdress \
                .replace("%PARAM_LAT%", str(lat)) \
                .replace("%PARAM_LON%", str(lon)) \
                .replace("%PARAM_LAT%", str(lat)) \
                .replace("%PARAM_FUELTYPE%", fuelType) \
                .replace("%PARAM_INCLUDECLOSED%", str(includeClosedStations))
    response = requests.get(reqUrl)
    return response.json()

def filterStations(completeList: list, selectedStations: list, timestamp: float, datetime: string) -> list:
    '''Filters a given complete list for the prices of selected stations.'''

    filteredStationPrices: list = []

    # Get all gas station ids of the selected stations.
    stationIds = []
    for station in selectedStations:
        stationIds.append(station["id"])

    for station in completeList:
        if station["id"] in stationIds:
            entry: dict = {}
            entry["id"] = station["id"]
            entry["name"] = station["name"]
            entry["address"] = station["location"]["address"]
            entry["postalCode"] = station["location"]["postalCode"]
            
            if len(station["prices"]) > 0:
                entry["dieselPrice"] = station["prices"][0]["amount"]
            else:
                entry["dieselPrice"] = -1

            entry["ts"] = timestamp
            entry["datetime"] = datetime

            filteredStationPrices.append(entry)
            
    return filteredStationPrices

def writeToCSV(stationPrices: list) -> list:
    '''Writes a given list to the persistent csv file.'''

    columns = ["ts", "datetime", "id", "name", "address", "postalCode", "dieselPrice"]
    rows: list = []

    if not os.path.isfile("prices.csv"):
        with open("prices.csv", "w", newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()

    with open("prices.csv",newline="") as currentFile:
        csv_reader=csv.DictReader(currentFile)
        for row in csv_reader:
            rows.append(row)

    for station in stationPrices:
        rows.append(station)

    with open("prices.csv", 'w',newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for key in rows:
            writer.writerow(key)

    return rows

def genStationListsForMail(stationPrices: list) -> str:
    '''Generates the mail body regarding the last 5 prices for each station.'''
    
    stationList = {}

    for row in stationPrices:
        if int(row['id']) not in stationList:
           newStation = Station(row['id'], row['name'])
           stationList[int(newStation.id)] = newStation
        
        station = stationList[int(row['id'])]
        station.addRow(row)

    message = ""

    for stationId in stationList:
        station = stationList[stationId]
        last5rows = station.getLast5Rows()

        message += "--------------------------------------------\n"
        message += " " + station.name + "\n"
        message += "\n"

        for idx, row in enumerate(last5rows):
            message += " " + last5rows[idx]['datetime'] + " - EUR " + str(last5rows[idx]['dieselPrice']) + "\n"

    message += "--------------------------------------------\n\n"

    return message

def loadMailConfig() -> {}:
    '''Reads the current mail configuration from the mail config file.'''

    with open('email_config.json', 'r') as emailConfigFile:
        mailConfig = json.load(emailConfigFile)
        return mailConfig

    return {}

def constructMailMessage(mailConfig: {}, rows: list) -> EmailMessage:
    '''Constructs the message for the update mail.'''

    message = EmailMessage()
    message['Subject'] = mailConfig['subject']
    message['From'] = mailConfig['sender']

    messageBody = "Greetings from your Sprity-Bot!\nHere are the last updates on your gas prices:\n\n"
    messageBody += genStationListsForMail(rows)
    messageBody += "That's all for now. Until next time!\nCU, Sprity-Bot"

    message.set_content(messageBody)

    return message


def sendMail(rows: list):
    '''Sends current updated gas prices to specified e-mail adresses.'''

    try:
        mailConfig = loadMailConfig()
        mailMessage = constructMailMessage(mailConfig, rows)
        if mailConfig['mode'] == 'STARTTLS':
            context = ssl.create_default_context()
            with smtplib.SMTP(mailConfig['host'], mailConfig['port']) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(mailConfig['user'], mailConfig['pwd'])
                server.sendmail(mailConfig['sender'], mailConfig['receivers'], mailMessage.as_bytes())
        else:
            print("Error - Mail-mode not supported.")

    except BaseException as ex:
        print("Error - Exception during mail sending: " + str(ex))

# Call main function
main()
