

class InputUtil:

    def InputString(inputStr: str):
        try:
            text = input(inputStr)
            return text
        except:
            return None


    def InputNumber(min: int, max: int, inputStr: str):

        try:
            text = input(inputStr)

            number = int(text)

            if number < min:
                return None
            if number > max:
                return None
            
            return number

        except:
            return None