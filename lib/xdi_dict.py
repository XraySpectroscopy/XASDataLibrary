##
## Dictionary of XDI terms -- Python Version
## Most data is actually given as json strings

PRINTABLES = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c'

ENERGY_UNITS = "['eV', 'keV']"

ANGLE_UNITS = "['deg', 'rad']"

COLUMN_NAMES = """['energy', 'angle', 'k', 'chi', 'i0', 'time',
		'itrans', 'ifluor', 'irefer',
		'mutrans', 'mufluor', 'murefer',
		'normtrans', 'normfluor', 'normrefer']"""

XRAY_EDGES = "['K', 'L3', 'L2', 'L1', 'M4,5', 'M3', 'N', 'O']"

######
##  Classes are broken here into a 2-level heierarchy:  Family.Member
##    Families have a name and a dictionary of Members
##    Members have a name and a pair of values:
##        type information
##        description
##   The member type information is of the form <TYPE> or <TYPE(UNITS)>
##   where TYPE is one of
##        str, int, float, datetime, atom_sym, xray_edge
##   str:       general string
##   int:       integer, unitless
##   float:     floating point number, with implied units as specified
##   datetime:  an ISO-structured datetime string
##   atom_sym:  two character symbol for element
##   xray_edge: standard symbol for absorption edge

CLASSES = {"facility":
	   {"name":  ["<str>", "name of facility / storage ring"],
	    "energy": ["<float(GeV)>", "stored beam energy"],
	    "current": ["<float(mA)>", "stored beam current"],
	    "xray_source": ["<str>", "description of x-ray source"],
	    "critical_energy": ["<float(keV)>", "critical energy of source"],
	   },
	   "beamline":
	   {"name":  ["<str>", "name of beamline"],
	    "focussing": ["<str>", "describe focussing"],
	    "collimation": ["<str>", "describe x-ray beam collimation"],
	    "harmonic_rejection": ["<str>", "describe harmonic rejection scheme"],
	   },
	   "mono":
	   {"name":  ["<str>", "name of monochromator"],
	    "dspacing": ["<float(Ang)>", "d spacing"],
	    "cooling": ["<str>", "describe cooling scheme"],
	   },
	   "scan":
	   {"mode": ["<str>", "describe scan mode"],
	    "element": ["<atom_sym>", "atomic symbol of element being scanned"],
	    "edge": ["<xray_edge>",   "edge being scanned"],
	    "start_time": ["<datetime>", "scan start time"],
	    "stop_time": ["<datetime>", "scan stop time"],
	    "n_regiions": ["<int>", "number of scan regions for segmented step scan"],
	   },
	   "detectors":
	   {"i0": ["<str>", "describe I0 detector"],
	    "itrans": ["<str>", "describe transmission detector"],
	    "ifluor": ["<str>", "describe fluorescence detector"],
	    "irefer": ["<str>", "describe reference sample detector and scheme"],
	   },
	   "sample":
	   {"name": ["<str>", "describe sample"],
	    "formula": ["<str>", "sample formula"],
	    "preparation": ["<str>", "describe sample prepation"],
	    "reference": ["<str>", "describe reference sample"],
	   },
	  }
