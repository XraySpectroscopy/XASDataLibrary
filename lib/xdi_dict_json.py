COLUMN_NAMES = ['energy', 'angle', 'k', 'chi', 'i0', 'time',
		'itrans', 'ifluor', 'irefer',
		'mutrans', 'mufluor', 'murefer',
		'normtrans', 'normfluor', 'normrefer']

ENERGY_UNITS = ['eV', 'keV']
ANGLE_UNITS = ['deg', 'rad']

EDGES = ['K', 'L3', 'L2', 'L1', 'M4,5', 'M3', 'N', 'O']

CLASSES = {'facility':
	   {'name':  ['<str>', 'name of facility / storage ring'],
	    'energy': ['<float|GeV>', 'stored beam energy'],
	    'current': ['<float|mA>', 'stored beam current'],
	    'xray_source': ['<str>', 'description of x-ray source'],
	    'critical_energy': ['<float|keV>', 'critical energy of source'],
	   },
	   'beamline':
	   {'name':  ['<str>', 'name of beamline'],
	    'focussing': ['<str>', 'describe focussing'],
	    'collimation': ['<str>', 'describe x-ray beam collimation'],
	    'harmonic_rejection': ['<str>', 'describe harmonic rejection scheme'],
	   },
	   'mono':
	   {'name':  ['<str>', 'name of monochromator'],
	    'dspacing': ['<float|Ang>', 'd spacing'],
	    'cooling': ['<str>', 'describe cooling scheme'],
	   },
	   'scan':
	   {'mode': ['<str>', 'describe scan mode'],
	    'element': ['<elem>', 'atomic symbol of element being scanned'],
	    'edge': ['<edge>',   'edge being scanned'],
	    'start_time': ['<date>', 'scan start time'],
	    'stop_time': ['<date>', 'scan stop time'],
	    'n_regiions': ['<int>', 'number of scan regions for segmented step scan'],
	   },
	   'detectors':
	   {'i0': ['<str>', 'describe I0 detector'],
	    'itrans': ['<str>', 'describe transmission detector'],
	    'ifluor': ['<str>', 'describe fluorescence detector'],
	    'irefer': ['<str>', 'describe reference sample detector and scheme'],
	   },
	   'sample':
	   {'name': ['<str>', 'describe sample'],
	    'formula': ['<str>', 'sample formula'],
	    'preparation': ['<str>', 'describe sample prepation'],
	    'reference': ['<str>', 'describe reference sample'],
	   },
	  }
