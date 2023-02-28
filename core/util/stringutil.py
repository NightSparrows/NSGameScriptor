

class StringUtil:
    
    # 中文對其問題
    def align(string, length=0):
        if length == 0:
            return string
        slen = len(string)
        re = string
        if isinstance(string, str):
            placeholder = ' '
        else:
            placeholder = u'　'
        while slen < length:
            re += placeholder
            slen += 1
        return re
