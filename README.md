# SPRITY

A small script that tracks gasoline prices in configurable areas of Austria. 

## Configuration

All configuration is loaded from an expected file called `config.json`, which should be located in the same folder as the script. For the initial start, a template file called `config_template.json`is included in the repo, with all the neccessary keys etc. You should make a copy of that file, rename it to 'config.json' and edit its contents to your needs. 

Configuration keys:
 * `run_scheduled`: Set to `true` if script should run at times, specified in `run_times`. If set to `false` it will immediatly do a single run and close itself. 
 * `run_times`: A list of times in 24h-format, on which the script should automatically do runs. 
 * `enable_email_notifications`: Set this to `true` if you want that the script sends you (+ optionally others) an e-mail with the last five price updates of your configured gas stations. 
 * `email_configuration`: All required settings, if you want the script to be able to send mails. 
 * `email_configuration/mode`: Currently only `STARTTLS` is supported.
 * `email_configuration/host, port, user, pwd, sender, recievers, subject, introText, outroText`: Should be self explanatory. 
 * `stationIds`: A list of gas stations, that the script should pull Diesel prices from. The info has to be collected manually by yourself from the Spritpreis-Rechner of E-Control Austria. I'm working on a simplier solution. 

## Usage

The script can be run by normal Python interpreter start, e.g. `python sprityMain.py` or `python3 sprityMain.py`. It then loads the configuration of the `config.json`-file as described and is executed accordingly. 

When switching to "scheduled-run"-mode, it should be run in a way where shutting down your computer or closing the terminal does not kill it. Therefore, it makes sense to run it in screen session on a server or similar - you have to come up yourself with a scenario that fits you.

The script writes the gathered data in a file called `prices.csv`, where you can further inspect the data and go crazy with it.

That's it - have fun!