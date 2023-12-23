# SPRITY

A small script that tracks gasoline prices in configurable areas of Austria. 

## Configuration

The script will lookup all stations that are defined in a file called 'stationIds.json'. A template for that file is part of the repository. Copy and rename it, and then edit the list to your liking. 

The IDs themselves have to be looked up at the E-Control API - further detail on this will follow as soon as I get to it. 

## Usage

The script can be run by normal Python interpreter start, e.g. 'python sprityMain.py'. It will then run in your console as long as you do not close it. Therefore, it makes sense to run it in screen session on a server or similar - you have to come up yourself with a scenario that fits you.

The script writes the gathered data in a file called 'prices.csv', where you can further inspect the data and go crazy with it. 

That's it - have fun!

## Todos

I want to implement next an e-mail feature, where it sends you everyday the prices of the last five days.
