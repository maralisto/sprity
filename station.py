class Station(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.rows = []

    def addRow(self, row: list):
        '''Adds an additional row to the price list of this station.'''

        self.rows.append(row)

    def getLast5Rows(self) -> list:
       '''Returns the last five rows (dependend on timestamp) for this station.'''

       self.rows.sort(key=self.stationPrices_sortkey_id)
       return self.rows[:5]

    def stationPrices_sortkey_id(self, station) -> int:
        '''Returns the ID of a station for sorting.'''

        return int(station['id'])
