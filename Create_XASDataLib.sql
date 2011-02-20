BEGIN TRANSACTION;
CREATE TABLE ligand (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE edge (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	level VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (level)
);
INSERT INTO "edge" VALUES(1,'K','1s');
INSERT INTO "edge" VALUES(2,'L2','2p1/2');
INSERT INTO "edge" VALUES(3,'L3','2p3/2');
INSERT INTO "edge" VALUES(4,'L1','2s');
CREATE TABLE crystal (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	format VARCHAR, 
	data VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE facility (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE element (
	z INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
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
CREATE TABLE citation (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	journal VARCHAR, 
	authors VARCHAR, 
	title VARCHAR, 
	volume VARCHAR, 
	pages VARCHAR, 
	year VARCHAR, 
	doi VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE monochromator (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	lattice_constant FLOAT, 
	steps_per_degree FLOAT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE mode (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO "mode" VALUES(1,'transmission','transmission intensity through sample',NULL);
INSERT INTO "mode" VALUES(2,'fluorescence, total yield','total x-ray fluorescence intensity, no energy analysis',NULL);
INSERT INTO "mode" VALUES(3,'fluorescence, energy analyzed','x-ray fluorescence measured with an energy dispersive (solid-state) detector.
 Measurements will often need to be corrected for dead-time effects',NULL);
INSERT INTO "mode" VALUES(4,'xeol','visible or uv light emission',NULL);
INSERT INTO "mode" VALUES(5,'electron emission','emitted electrons from sample',NULL);
CREATE TABLE person (
	id INTEGER NOT NULL, 
	email VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	first_name VARCHAR NOT NULL, 
	last_name VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);
CREATE TABLE format (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO "format" VALUES(1,'internal-json','Read dat_* columns of spectra table as json',NULL);
CREATE TABLE suite (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	person INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(person) REFERENCES person (id)
);
CREATE TABLE beamline (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	xray_source VARCHAR, 
	monochromator INTEGER, 
	facility INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(facility) REFERENCES facility (id), 
	FOREIGN KEY(monochromator) REFERENCES monochromator (id)
);
CREATE TABLE sample (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	formula VARCHAR, 
	material_source VARCHAR, 
	person INTEGER, 
	crystal INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(person) REFERENCES person (id), 
	FOREIGN KEY(crystal) REFERENCES crystal (id)
);
CREATE TABLE spectra (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	notes VARCHAR, 
	attributes VARCHAR, 
	file_link VARCHAR, 
	dat_energy VARCHAR, 
	dat_i0 VARCHAR, 
	dat_itrans VARCHAR, 
	dat_iemit VARCHAR, 
	dat_irefer VARCHAR, 
	dat_dtime_corr VARCHAR, 
	calc_mu_trans VARCHAR, 
	calc_mu_emit VARCHAR, 
	calc_mu_refer VARCHAR, 
	calc_energy_ev VARCHAR, 
	notes_energy VARCHAR, 
	notes_i0 VARCHAR, 
	notes_itrans VARCHAR, 
	notes_iemit VARCHAR, 
	notes_irefer VARCHAR, 
	temperature VARCHAR, 
	submission_date DATETIME, 
	reference_used INTEGER, 
	npts INTEGER, 
	person INTEGER, 
	edge INTEGER, 
	element INTEGER, 
	sample INTEGER, 
	beamline INTEGER, 
	monochromator INTEGER, 
	format INTEGER, 
	citation INTEGER, 
	reference_sample INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(edge) REFERENCES edge (id), 
	FOREIGN KEY(element) REFERENCES element (z), 
	FOREIGN KEY(sample) REFERENCES sample (id), 
	FOREIGN KEY(beamline) REFERENCES beamline (id), 
	FOREIGN KEY(monochromator) REFERENCES monochromator (id), 
	FOREIGN KEY(format) REFERENCES format (id), 
	FOREIGN KEY(citation) REFERENCES citation (id), 
	FOREIGN KEY(reference_sample) REFERENCES sample (id), 
	FOREIGN KEY(person) REFERENCES person (id)
);
CREATE TABLE spectra_suite (
	id INTEGER NOT NULL, 
	suite INTEGER, 
	spectra INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(suite) REFERENCES suite (id), 
	FOREIGN KEY(spectra) REFERENCES spectra (id)
);
CREATE TABLE rating (
	id INTEGER NOT NULL, 
	score INTEGER, 
	comments VARCHAR, 
	person INTEGER, 
	spectra INTEGER, 
	suite INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(person) REFERENCES person (id), 
	FOREIGN KEY(spectra) REFERENCES spectra (id), 
	FOREIGN KEY(suite) REFERENCES suite (id)
);
CREATE TABLE spectra_mode (
	id INTEGER NOT NULL, 
	mode INTEGER, 
	spectra INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(mode) REFERENCES mode (id), 
	FOREIGN KEY(spectra) REFERENCES spectra (id)
);
CREATE TABLE spectra_ligand (
	id INTEGER NOT NULL, 
	ligand INTEGER, 
	spectra INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ligand) REFERENCES ligand (id), 
	FOREIGN KEY(spectra) REFERENCES spectra (id)
);
COMMIT;
