# SPRITY

A small script that tracks gasoline prices in configurable areas of Austria. 

## Configuration

The script will lookup all stations that are defined in a file called 'stationIds.json'. A template for that file is part of the repository. Copy and rename it, and then edit the list to your liking.

The IDs themselves have to be looked up at the E-Control API - further detail on this will follow as soon as I get to it.

Furthermore, the script requires access to an e-mail server to send you updates regarding the prices. A similar template for an e-mail configuration is also part of the repo and should be handled similarly to the one for the station ids. 

## Usage

The script can be run by normal Python interpreter start, e.g. 'python sprityMain.py'. Furthermore, there are two modes in which the script can be executed: 
 * Single-Call Mode (run as: ´python sprityMain.py´)
 * Scheduled Mode (run as: ´python sprityMain.py scheduled´)
 
In "Single-Call Mode" the script performs one roundtrip to get the current prices immediatly and closes. Accordingly, in "Scheduled Mode" the script keeps running and pulls current prices twice a day. The times for this are currently 6 o'clock in the morning and 13 o'clock in the evening. Currently, it is not possible to set the pull-times via script arguments, but it will be implemented in a future update. 

As the script should continue to do its work in "Scheduled Mode" it should be run in a way where shutting down your computer or closing the terminal does not kill it. Therefore, it makes sense to run it in screen session on a server or similar - you have to come up yourself with a scenario that fits you.

The script writes the gathered data in a file called 'prices.csv', where you can further inspect the data and go crazy with it.

Additionally, the script will also try to send you the five last prices of every station that is defined via e-mail to one or multiple e-mail adresses, to give you an update without the need to always inspect the CSV-file. For this, you need to set the apropriate e-mail server settings in the according configuration file. Currently, it is not possible to switch this feature off - but this is also on my list of future updates. 

That's it - have fun!

## Todos

 * Add switch to turn off email notifications.
 * Add user configuration of scheduled pull times.