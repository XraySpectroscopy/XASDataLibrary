

MATCH = {'word':       re.compile(r'[a-zA-Z0-9_]+$').match,
         'properword': re.compile(r'[a-zA-Z_][a-zA-Z0-9_-]*$').match,
         'datetime':   re.compile(DATETIME).match
         }

def validate_datetime(sinput):
    "validate allowed datetimes"
    return MATCH['datetime'](sinput)

def validate_int(sinput):
    "validate for int"
    try:
        int(sinput)
        return True
    except ValueError:
        return False

def validate_float(sinput):
    "validate for float"
    try:
        float(sinput)
        return True
    except ValueError:
        return False

def validate_float_or_nan(sinput):
    "validate for float, with nan, inf"
    try:
        return (sinput.lower() == 'nan' or
                sinput.lower() == 'inf' or
                float(sinput))
    except ValueError:
        return False

def validate_words(sinput):
    "validate for words"
    for word in sinput.strip().split(' '):
        if not MATCH['word'](word):
            return False
    return True

def validate_edge(sinput):
    "validate for words"
    return MATCH['properword'](sinput) and \
           sinput.upper() in xdi_dict.EDGES

def validate_properword(sinput):
    "validate for words"
    return  MATCH['properword'](sinput)

def validate_chars(sinput):
    "validate for string"
    for char in sinput:
        if char not in PRINTABLES:
            return False
    return True
