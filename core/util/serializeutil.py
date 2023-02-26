
import datetime


class SerializeUtil:
    
    def GetDatetimeFromString(dateString: str):
        return datetime.datetime.strptime(dateString, '%y/%m/%d %H:%M:%S')

    def GetStringFromDateTime(date: datetime):
        return datetime.datetime.strftime(date, '%y/%m/%d %H:%M:%S')

