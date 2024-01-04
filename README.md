# SPRITY

A small script that tracks gasoline prices in configurable areas of Austria. Currently, only Diesel prices can be tracked. 

## Installation

Make sure, that the dependencies defined in the `requirements.txt`-file are installed. Either install them globally or create a custom Python VENV - any of the options work. After that, make sure to do the configuration part below. 

## Configuration

All configuration is loaded from an expected file called `config.json`, which should be located in the same folder as the script. For the initial start, a template file called `config_template.json`is included in the repo, with all the neccessary keys etc. You should make a copy of that file, rename it to 'config.json' and edit its contents to your needs. 

Configuration keys:
 * `run_scheduled`: Set to `true` if script should run at times, specified in `run_times`. If set to `false` it will immediatly do a single run and close itself. 
 * `run_times`: A list of times in 24h-format, on which the script should automatically do runs. 
 * `enable_email_notifications`: Set this to `true` if you want that the script sends you (+ optionally others) an e-mail with the last five price updates of your configured gas stations. 
 * `email_configuration`: All required settings, if you want the script to be able to send mails. 
 * `email_configuration/mode`: Currently only `STARTTLS` is supported.
 * `email_configuration/host, port, user, pwd, sender, recievers, subject, introText, outroText`: Should be self explanatory. 
 * `searchRegions`: Each tracked station has to be assigned to one search region. This is due to the special nature of the API of the Spritpreisrechner of e-Control. Its best to perform a station search first, as the apropriate JSON-Code for the search region as well as the stations to be tracked are an output to the console. 
 * `stationIds`: A list of gas stations, that the script should pull Diesel prices from. The JSON-code for this portion of the configuration can be aquired from the search output.  

## Usage

The script can be run by normal Python interpreter start, e.g. `python sprityMain.py` or `python3 sprityMain.py`. It then loads the configuration of the `config.json`-file as described and is executed accordingly. 

### Performing a station search

In order to get a list with available stations for a certain region a station search can be performed:

```python3 sprityMain.py --searchStations --lat 99.999 --lon 99.999```

For the `lat` and `lon` attributes the coordinates for latitude and longitude of the center point of the search region need to be provided. The script then prints out the code for the search region to be used in the configuration file, as well as the code for the found stations. The code for stations of interest can then also be copy and pasted into the configuration file.

### Normal Operation Mode

For normal operation mode, e.g. periodically pulling the latest price updates from the stations, do a proper configuration in the conf-file and start the script without any arguments, e.g.:

```python3 sprityMain.py```

When "scheduled-run"-mode is switched on in the config-file, the script should be run in a way where shutting down your computer or closing the terminal does not kill it. Therefore, it makes sense to run it in screen session on a server or similar - you have to come up yourself with a scenario that fits you.

The script writes the gathered data in a file called `prices.csv`, where you can further inspect the data and go crazy with it.

That's it - have fun!