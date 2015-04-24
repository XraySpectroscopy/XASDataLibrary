CREATE TABLE person (
	id INTEGER NOT NULL, 
	email TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	name TEXT NOT NULL, 
	affiliation TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);
CREATE TABLE ligand (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE info (
	"key" TEXT NOT NULL, 
	value TEXT, 
	PRIMARY KEY ("key"), 
	UNIQUE ("key")
);
INSERT INTO "info" VALUES('version','1.0.0');
INSERT INTO "info" VALUES('create_date','2015-04-24T13:00:28.956661');
INSERT INTO "info" VALUES('modify_date','2015-04-24T13:00:28.956661');
CREATE TABLE crystal_structure (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	format TEXT,
	data TEXT,
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE edge (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	level VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (level)
);
INSERT INTO "edge" VALUES(1,'K','1s');
INSERT INTO "edge" VALUES(2,'L3','2p3/2');
INSERT INTO "edge" VALUES(3,'L2','2p1/2');
INSERT INTO "edge" VALUES(4,'L1','2s');
INSERT INTO "edge" VALUES(5,'M4,5','3d3/2,5/2');

CREATE TABLE energy_units (
	id INTEGER NOT NULL, 
	units TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (units)
);


INSERT INTO energy_units VALUES(1,'eV','electronVolts',NULL);
INSERT INTO energy_units VALUES(2,'keV','kiloelectronVolts',NULL);
INSERT INTO energy_units VALUES(3,'degrees','angle in degrees for Bragg Monochromator.  Need mono dspacing to convert to eV',NULL);

CREATE TABLE element (
        z INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	symbol VARCHAR(2) NOT NULL, 
	PRIMARY KEY (z), 
	UNIQUE (name), 
	UNIQUE (symbol)
);
INSERT INTO "element" VALUES(1,'hydrogen','H');
INSERT INTO "element" VALUES(2,'helium','He');
INSERT INTO "element" VALUES(3,'lithium','Li');
INSERT INTO "element" VALUES(4,'beryllium','Be');
INSERT INTO "element" VALUES(5,'boron','B');
INSERT INTO "element" VALUES(6,'carbon','C');
INSERT INTO "element" VALUES(7,'nitrogen','N');
INSERT INTO "element" VALUES(8,'oxygen','O');
INSERT INTO "element" VALUES(9,'fluorine','F');
INSERT INTO "element" VALUES(10,'neon','Ne');
INSERT INTO "element" VALUES(11,'sodium','Na');
INSERT INTO "element" VALUES(12,'magnesium','Mg');
INSERT INTO "element" VALUES(13,'aluminum','Al');
INSERT INTO "element" VALUES(14,'silicon','Si');
INSERT INTO "element" VALUES(15,'phosphorus','P');
INSERT INTO "element" VALUES(16,'sulfur','S');
INSERT INTO "element" VALUES(17,'chlorine','Cl');
INSERT INTO "element" VALUES(18,'argon','Ar');
INSERT INTO "element" VALUES(19,'potassium','K');
INSERT INTO "element" VALUES(20,'calcium','Ca');
INSERT INTO "element" VALUES(21,'scandium','Sc');
INSERT INTO "element" VALUES(22,'titanium','Ti');
INSERT INTO "element" VALUES(23,'vanadium','V');
INSERT INTO "element" VALUES(24,'chromium','Cr');
INSERT INTO "element" VALUES(25,'manganese','Mn');
INSERT INTO "element" VALUES(26,'iron','Fe');
INSERT INTO "element" VALUES(27,'cobalt','Co');
INSERT INTO "element" VALUES(28,'nickel','Ni');
INSERT INTO "element" VALUES(29,'copper','Cu');
INSERT INTO "element" VALUES(30,'zinc','Zn');
INSERT INTO "element" VALUES(31,'gallium','Ga');
INSERT INTO "element" VALUES(32,'germanium','Ge');
INSERT INTO "element" VALUES(33,'arsenic','As');
INSERT INTO "element" VALUES(34,'selenium','Se');
INSERT INTO "element" VALUES(35,'bromine','Br');
INSERT INTO "element" VALUES(36,'krypton','Kr');
INSERT INTO "element" VALUES(37,'rubidium','Rb');
INSERT INTO "element" VALUES(38,'strontium','Sr');
INSERT INTO "element" VALUES(39,'yttrium','Y');
INSERT INTO "element" VALUES(40,'zirconium','Zr');
INSERT INTO "element" VALUES(41,'niobium','Nb');
INSERT INTO "element" VALUES(42,'molybdenum','Mo');
INSERT INTO "element" VALUES(43,'technetium','Tc');
INSERT INTO "element" VALUES(44,'ruthenium','Ru');
INSERT INTO "element" VALUES(45,'rhodium','Rh');
INSERT INTO "element" VALUES(46,'palladium','Pd');
INSERT INTO "element" VALUES(47,'silver','Ag');
INSERT INTO "element" VALUES(48,'cadmium','Cd');
INSERT INTO "element" VALUES(49,'indium','In');
INSERT INTO "element" VALUES(50,'tin','Sn');
INSERT INTO "element" VALUES(51,'antimony','Sb');
INSERT INTO "element" VALUES(52,'tellurium','Te');
INSERT INTO "element" VALUES(53,'iodine','I');
INSERT INTO "element" VALUES(54,'xenon','Xe');
INSERT INTO "element" VALUES(55,'cesium','Cs');
INSERT INTO "element" VALUES(56,'barium','Ba');
INSERT INTO "element" VALUES(57,'lanthanum','La');
INSERT INTO "element" VALUES(58,'cerium','Ce');
INSERT INTO "element" VALUES(59,'praseodymium','Pr');
INSERT INTO "element" VALUES(60,'neodymium','Nd');
INSERT INTO "element" VALUES(61,'promethium','Pm');
INSERT INTO "element" VALUES(62,'samarium','Sm');
INSERT INTO "element" VALUES(63,'europium','Eu');
INSERT INTO "element" VALUES(64,'gadolinium','Gd');
INSERT INTO "element" VALUES(65,'terbium','Tb');
INSERT INTO "element" VALUES(66,'dysprosium','Dy');
INSERT INTO "element" VALUES(67,'holmium','Ho');
INSERT INTO "element" VALUES(68,'erbium','Er');
INSERT INTO "element" VALUES(69,'thulium','Tm');
INSERT INTO "element" VALUES(70,'ytterbium','Yb');
INSERT INTO "element" VALUES(71,'lutetium','Lu');
INSERT INTO "element" VALUES(72,'hafnium','Hf');
INSERT INTO "element" VALUES(73,'tantalum','Ta');
INSERT INTO "element" VALUES(74,'tungsten','W');
INSERT INTO "element" VALUES(75,'rhenium','Re');
INSERT INTO "element" VALUES(76,'osmium','Os');
INSERT INTO "element" VALUES(77,'iridium','Ir');
INSERT INTO "element" VALUES(78,'platinum','Pt');
INSERT INTO "element" VALUES(79,'gold','Au');
INSERT INTO "element" VALUES(80,'mercury','Hg');
INSERT INTO "element" VALUES(81,'thallium','Tl');
INSERT INTO "element" VALUES(82,'lead','Pb');
INSERT INTO "element" VALUES(83,'bismuth','Bi');
INSERT INTO "element" VALUES(84,'polonium','Po');
INSERT INTO "element" VALUES(85,'astatine','At');
INSERT INTO "element" VALUES(86,'radon','Rn');
INSERT INTO "element" VALUES(87,'francium','Fr');
INSERT INTO "element" VALUES(88,'radium','Ra');
INSERT INTO "element" VALUES(89,'actinium','Ac');
INSERT INTO "element" VALUES(90,'thorium','Th');
INSERT INTO "element" VALUES(91,'protactinium','Pa');
INSERT INTO "element" VALUES(92,'uranium','U');
INSERT INTO "element" VALUES(93,'neptunium','Np');
INSERT INTO "element" VALUES(94,'plutonium','Pu');
INSERT INTO "element" VALUES(95,'americium','Am');
INSERT INTO "element" VALUES(96,'curium','Cm');
INSERT INTO "element" VALUES(97,'berkelium','Bk');
INSERT INTO "element" VALUES(98,'californium','Cf');
INSERT INTO "element" VALUES(99,'einsteinium','Es');
INSERT INTO "element" VALUES(100,'fermium','Fm');
INSERT INTO "element" VALUES(101,'mendelevium','Md');
INSERT INTO "element" VALUES(102,'nobelium','No');
INSERT INTO "element" VALUES(103,'lawerencium','Lw');
INSERT INTO "element" VALUES(104,'Rutherfordium','Rf');
INSERT INTO "element" VALUES(105,'Dubnium','Ha');
INSERT INTO "element" VALUES(106,'Seaborgium','Sg');
INSERT INTO "element" VALUES(107,'Bohrium','Bh');
INSERT INTO "element" VALUES(108,'Hassium','Hs');
INSERT INTO "element" VALUES(109,'Meitnerium','Mt');

CREATE TABLE facility (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

INSERT INTO "facility" VALUES( 1,'SSRL','Stanford Synchrotron Radiation Laboratory, SLAC, Palo Alto, CA, USA',NULL);
INSERT INTO "facility" VALUES( 2,'SRS','Synchrotron Radiation Source, Daresbury Lab, Cheshire, UK',NULL);
INSERT INTO "facility" VALUES( 3,'NSLS','National Synchrotron Light Source, BNL, Upton, IL, USA',NULL);
INSERT INTO "facility" VALUES( 4,'Photon Factory','Photon Factory, KEK, Tsukuba, Japan',NULL);
INSERT INTO "facility" VALUES( 5,'ESRF','European Synchrotron Radiation Facility, Grenoble, France',NULL);
INSERT INTO "facility" VALUES( 6,'APS','Advanced Photon Source, ANL, Argonne, IL, USA',NULL);
INSERT INTO "facility" VALUES( 7,'ALS','Advanced Light Source, LBNL, Berkeley, CA, USA',NULL);
INSERT INTO "facility" VALUES( 8,'DLS','Diamond Light Source, Didcot, Oxfordshire, Great Britian',NULL);
INSERT INTO "facility" VALUES( 9,'SOLEIL','Synchrotron SOLEIL, GIF-sur-YVETTE, France',NULL);
INSERT INTO "facility" VALUES(10,'SPring-8','SPring=8 Synchrotron,  Hyogo, Japan',NULL);
INSERT INTO "facility" VALUES(11,'DESY','DESY Synchrotron, Hamburg, Germany',NULL);
INSERT INTO "facility" VALUES(12,'ANKA','Karlsruhe, Germany',NULL);
INSERT INTO "facility" VALUES(13,'Elettra','Elettra, Trieste, Italy',NULL);
INSERT INTO "facility" VALUES(14,'AS','Australian Synchrotron ',NULL);


CREATE TABLE mode (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO "mode" VALUES(1,'transmission','transmission intensity through sample',NULL);
INSERT INTO "mode" VALUES(2,'fluorescence, total yield','total x-ray fluorescence intensity, no energy analysis',NULL);
INSERT INTO "mode" VALUES(3,'fluorescence, energy analyzed','x-ray fluorescence  with an energy dispersive (solid-state) detector', NULL);
INSERT INTO "mode" VALUES(4,'xeol','visible or uv light emission',NULL);
INSERT INTO "mode" VALUES(5,'electron emission','emitted electrons from sample',NULL);



CREATE TABLE citation (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	journal TEXT, 
	authors TEXT, 
	title TEXT, 
	volume TEXT, 
	pages TEXT, 
	year TEXT, 
	doi TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE sample (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	formula TEXT, 
	material_source TEXT, 
	person_id INTEGER, 
	crystal_structure_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(crystal_structure_id) REFERENCES crystal_structure (id), 
	FOREIGN KEY(person_id) REFERENCES person (id)
);
CREATE TABLE suite (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	person_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(person_id) REFERENCES person (id)
);

CREATE TABLE beamline (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	xray_source TEXT, 
	facility_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(facility_id) REFERENCES facility (id) 
);
INSERT INTO "beamline" VALUES(1,'13ID','GSECARS 13-ID',NULL,'APS Undulator A',1);
INSERT INTO "beamline" VALUES(2,'13BM','GSECARS 13-BM',NULL,'APS bending magnet',1);
INSERT INTO "beamline" VALUES(3,'10ID','MR-CAT  10-ID',NULL,'APS Undulator A',1);
INSERT INTO "beamline" VALUES(4,'10BM','MR-CAT  10-BM',NULL,'APS Bending Magnet',1);
INSERT INTO "beamline" VALUES(5,'12BM','APS 12-BM',NULL,'APS bending magnet',1);
INSERT INTO "beamline" VALUES(6,'20ID','APS 20-ID',NULL,'APS Undulator A',1);
INSERT INTO "beamline" VALUES(7,'20BM','APS 20-BM',NULL,'APS Bending Magnet',1);
INSERT INTO "beamline" VALUES(8,'X11A','NSLS X11-A',NULL,'NSLS bending magnet',3);
INSERT INTO "beamline" VALUES(9,'4-3','SSRL, 4-3',NULL,'SSRL',4);
INSERT INTO "beamline" VALUES(10,'4-1','SSRL, 4-1',NULL,'SSRL',4);

CREATE TABLE suite_rating (
	id INTEGER NOT NULL, 
	score INTEGER, 
	comments TEXT, 
	person_id INTEGER,
	comment_date TIMESTAMP, 		
	suite_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(person_id) REFERENCES person (id), 
	FOREIGN KEY(suite_id) REFERENCES suite (id)
);

CREATE TABLE spectra (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	notes TEXT, 
	attributes TEXT, 
	data_energy TEXT, 
	data_i0 TEXT DEFAULT '[1.0]', 
	data_itrans TEXT DEFAULT '[1.0]', 
	data_iemit TEXT DEFAULT '[1.0]', 
	data_irefer TEXT DEFAULT '[1.0]', 
	data_dtime_corr TEXT DEFAULT '[1.0]', 
	calc_mu_trans TEXT DEFAULT '-log(itrans/i0)', 
	calc_mu_emit TEXT DEFAULT '(iemit*dtime_corr/i0)', 
	calc_mu_refer TEXT DEFAULT '-log(irefer/itrans)', 
	notes_i0 TEXT, 
	notes_itrans TEXT, 
	notes_iemit TEXT, 
	notes_irefer TEXT, 
	temperature TEXT,
	dspacing FLOAT, 
	submission_date TIMESTAMP, 
	collection_date TIMESTAMP, 
	reference_used INTEGER, 
	energy_units_id INTEGER, 
	person_id INTEGER, 
	element_z INTEGER, 
	edge_id INTEGER, 
	sample_id INTEGER, 
	beamline_id INTEGER, 
	citation_id INTEGER, 
	reference_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(person_id) REFERENCES person (id), 
	FOREIGN KEY(element_z) REFERENCES element (z),
	FOREIGN KEY(edge_id) REFERENCES edge (id), 
	FOREIGN KEY(sample_id) REFERENCES sample (id), 
	FOREIGN KEY(beamline_id) REFERENCES beamline (id), 
	FOREIGN KEY(citation_id) REFERENCES citation (id), 
	FOREIGN KEY(reference_id) REFERENCES sample (id), 
	FOREIGN KEY(energy_units_id) REFERENCES energy_units (id) 
);

CREATE TABLE spectra_suite (
	id INTEGER NOT NULL, 
	suite_id INTEGER, 
	spectra_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(suite_id) REFERENCES suite (id), 
	FOREIGN KEY(spectra_id) REFERENCES spectra (id)
);

CREATE TABLE spectra_ligand (
	id INTEGER NOT NULL, 
	ligand_id INTEGER, 
	spectra_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ligand_id) REFERENCES ligand (id), 
	FOREIGN KEY(spectra_id) REFERENCES spectra (id)
);

CREATE TABLE spectra_mode (
	id INTEGER NOT NULL, 
	mode_id INTEGER, 
	spectra_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(mode_id) REFERENCES mode (id), 
	FOREIGN KEY(spectra_id) REFERENCES spectra (id)
);

CREATE TABLE spectra_rating (
	id INTEGER NOT NULL, 
	score INTEGER, 
	comments TEXT, 
	comment_date TIMESTAMP, 	
	person_id INTEGER, 
	spectra_id INTEGER,
	PRIMARY KEY (id), 
	FOREIGN KEY(person_id) REFERENCES person (id), 
	FOREIGN KEY(spectra_id) REFERENCES spectra (id)
);

