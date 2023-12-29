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
import argparse

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

# Configuration of the app as described in config.json.
config: dict = None

''' FUNCTIONS '''

def main():
    '''Main entry point of application.'''

    # Parse arguments.
    args = setupArgparse()

    # Read config from config file. 
    global config
    config = loadConfiguration()

    # Print status.
    print("*** Welcome to SpriTy! ***\n")

    # Check if in station search mode and process it.
    if args.searchStations:
        processStationSearchMode(args)
        return

    # Load configuration from config file and store it in global variable. 
    if config['run_scheduled']:
        # Print status
        print("Switching to scheduled mode.")

        # Configure schedule
        for timeSetting in config['run_times']:
            schedule.every().day.at(timeSetting).do(job)

        # Start scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)

    else:
        # Print status
        print("Switching to single call mode.")
        
        # Run job just one time.
        job()

def processStationSearchMode(consoleArgs):
    '''Processes the arguments for a station search and performs the search.'''
    print("Switching to station search mode...\n")

    # Perform station search instead of price gathering.
    searchLat = consoleArgs.lat
    searchLon = consoleArgs.lon

    foundStations = searchStationsByCoords(searchLat, searchLon, 'DIE', True)

    print("Use the following search region for these stations: ")
    printOutSearchRegion(searchLat, searchLon) 

    print("The following stations were found in the vincinity of the given area:\n\n")
    for station in foundStations:
        printOutStationInfo(station)
            
    print("*** End of station search results. ***")

def printOutStationInfo(stationInfo: dict):
    '''Prints out a filtered and formatted info of a station.'''

    filteredDict = {}
    filteredDict['id'] = stationInfo['id']
    filteredDict['name'] = stationInfo['name']
    filteredDict['location'] = stationInfo['location']

    print('----------- Station Info ------------')
    print(json.dumps(filteredDict, indent=2))
    print('\n')

def printOutSearchRegion(lat: float, lon: float) -> int:
    '''Prints out a suggestion for a search region, to be used in the config file. Furthermore, it returns the calculated highest region id for futher use.'''

    # Determine current index of search regions and increment it for the suggestion. 

    currentSearchRegions = config['searchRegions']
    highestID = -1
    for region in currentSearchRegions:
        if int(region['id']) > highestID:
            highestID = int(region['id'])

    suggestion = {}
    suggestion['id'] = highestID + 1
    suggestion['name'] = "PUT_YOUR_NAME_HERE"
    suggestion['lat'] = lat
    suggestion['lon'] = lon

    print(json.dumps(suggestion, indent=2))
    print("\n")

    return highestID


def setupArgparse() -> dict:
    '''Sets up argparse to process arguments of the command line.'''

    parser = argparse.ArgumentParser(description='Sprity - Austrian gas-price helper.')
    parser.add_argument('--searchStations', action='store_true', help='Search for gas stations.')
    parser.add_argument('--lat', help='Latitude of search region.')
    parser.add_argument('--lon', help='Longitude of search region.')
    
    args = parser.parse_args()

    return args

def job():
    ''' Job-function, that is executed by the scheduler and kicks of the fetching. '''

    # Set call time
    now = datetime.now()
    apiCallTimestamp = now.timestamp()
    apiCallDateTime = now.strftime("%d.%m.%Y %H:%M:%S")

    # Print status
    print(apiCallDateTime + " Fetching prices...")

    # Read station list and regions.
    stationList = config['stationIds']
    regionList = config['searchRegions']
    reportList = []

    for region in regionList:

        # Fetch stations, filter and update prices file.
        allStations = searchStationsByCoords(region['lat'], region['lon'], "DIE", False)
        reportList.append(filterStations(allStations, stationList, apiCallTimestamp, apiCallDateTime, region['id']))
        
    allRows = writeToCSV(reportList)

    # Print status
    print(now.strftime("%d.%m.%Y %H:%M:%S") + " Fetching finished - file written.")

    # Send update mail
    if config['enable_email_notifications']:
        sendMail(allRows)

def loadConfiguration() -> dict:
    '''Loads the contents of the configuration file (config.json).'''

    configFile = open("config.json")
    return json.load(configFile)

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

def filterStations(
        completeList: list, 
        selectedStations: list, 
        timestamp: float, 
        datetime: string,
        regionId: int) -> list:
    '''Filters a given complete list for the prices of selected stations.'''

    filteredStationPrices: list = []

    # Get all gas station ids of the selected stations.
    stationIds = []
    for station in selectedStations:
        if station['searchRegion'] == regionId:
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

def constructMailMessage(mailConfig: {}, rows: list) -> EmailMessage:
    '''Constructs the message for the update mail.'''

    message = EmailMessage()
    message['Subject'] = mailConfig['subject']
    message['From'] = mailConfig['sender']

    messageBody = mailConfig['introText']    
    messageBody += genStationListsForMail(rows)
    messageBody += mailConfig['outroText']
    message.set_content(messageBody)

    return message

def sendMail(rows: list):
    '''Sends current updated gas prices to specified e-mail adresses.'''

    try:
        mailConfig = config['email_configuration']
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
