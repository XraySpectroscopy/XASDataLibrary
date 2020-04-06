#!/usr/bin/perl

##########################################################################
# This scripts scrapes the data from the tables at the IUCr compendium	 #
# of the world's XAFS beamlines (see below for the URLs).  This is a	 #
# quirky, tricky chore.  Those web pages are rather inconsistent and	 #
# have some things that are simply incorrectly written HTML.  As a	 #
# result, there are a lot of one-off, special cases in this script in an #
# attempt to snarf as much of the data from those tables as possible.	 #
# 									 #
# Also, it is challenging to get beamline names (i.e. ESRF BM8 is also	 #
# called GILDA) from the IUCr pages.  So there is a hard-coded hash of	 #
# beamline names.							 #
# 									 #
# The results are written to JSON files called Americas.json, Asia.json, #
# and Europe.json.							 #
##########################################################################

use strict;
use warnings;
use HTML::TableExtract;
use File::Slurp;
use Data::Dump::Color;
use JSON;
use LWP::Simple;

my %beamlines  = ();
my @facilities = ();

my $region = $ARGV[0] || 'Americas';

my %pages = (Asia     => 'http://www.iucr.org/resources/commissions/xafs/beamlines-in-asia-and-oceania',
	     Americas => 'http://www.iucr.org/resources/commissions/xafs/beamlines-in-the-americas',
	     Europe   => 'http://www.iucr.org/resources/commissions/xafs/beamlines-in-europe');

my %beamline_names = (ESRF => {BM2   => 'D2AM',   BM8   => 'GILDA', BM20 => 'ROBL', BM25A => 'SPLINE',
			       BM26A => 'DUBBLE', BM30B => 'FAME'},
		      APS => {'5-BM-D'    => 'DNDCAT',  '10-ID-B' => 'MRCAT',   '10-BM-D' => 'MRCAT',
			      '13-ID-C,D' => 'GSECARS', '13-BM-D' => 'GSECARS', '16-BM-B' => 'HPCAT',
			      '18-ID-D'   => 'BIOCAT',}
		     );

my $content = q{};
if ($ARGV[1]) {			# skip downloading html file
  $content = read_file($region.'.html');
} else {
  $content = get($pages{$region});
  open(my $HTML, '>', $region.'.html');
  print $HTML $content;
  close $HTML;
};

my $json = JSON->new->allow_nonref;
$json->pretty(1);
$json->canonical(1);

my $text = read_file('names.json');
my $names = $json->decode($text);

my $te = HTML::TableExtract->new( depth => 0, count => 1 );
$te->parse_file($region.'.html');
foreach my $ts ($te->tables) {
  foreach my $row ($ts->rows) {
    my @list = split(" ", sanitize($row->[0]));
    my $name = $list[0];
    next if $name =~ m{DELSY|ISI|KIPT|KSRS|TNK|Operating}; # facilities in Russia, Ukraine are not tabulated, weird!
    if ($name eq 'Photon') {	# fix several naming and typography issues in the Asia webpage
      $name = 'Photon Factory'; # PF and AS have names with spaces, which my crude parsing retrieves incorrectly
    } elsif ($list[0] eq 'Australian') {
      $name = 'Australian Synchrotron';
    } elsif ($list[0] =~ m{hisor}i) {
      $name = 'HiSOR';          # missing space before open parens in top table
    } elsif ($list[0] =~ m{slri}i) {
      $name = 'SLRI';           # strip trailing comma, it says "SLRI, Siam" in top table
    };
    push @facilities, $name;
    push(@facilities, 'SESAME') if ($name eq 'SAGA'); # my crude way of parsing the top table misses the entry for SESAME
  };
};

if ($region eq 'Europe') {	# Soleil and SLS are out of order
  @facilities[-2,-1] = @facilities[-1,-2];
};

foreach my $i (0 .. $#facilities) {
  my %this = ();
  $te = HTML::TableExtract->new( depth => 0, count => $i+2 );
  $te->parse_file($region.'.html');
  foreach my $ts ($te->tables) {
    foreach my $row ($ts->rows) {
      my $key;
      my $name = q{};
      if ($facilities[$i] =~ m{BESSY}) { # handle BESSY's additional column
	$name = sanitize(shift @$row, 0);
	$key  = sanitize(shift @$row, 1);
      } elsif ($facilities[$i] =~ m{Diamond|HASYLAB}) { # these two facilities have names and sectors
	my $word = sanitize(shift @$row, 0);		# in the beamline column of their tables
	next if $word eq 'Beamline';
	$word =~ m{([IBP]D?\d\d)\s+(.*)};
	$name = $2;
	$key = $1;
	$key = 'I10' if ($key eq 'ID10'); # this is a typo on the webpage
      } else {
	$key  = sanitize(shift @$row, 1);
      };
      next if $key eq 'Beamline';
      next if $key eq 'Associated beamline'; # BESSY's table has one additional column, grrrr!
      $this{$key} -> {range}    = sanitize(shift @$row, 0);
      $this{$key} -> {flux}     = sanitize(shift @$row, 0);
      $this{$key} -> {size}     = sanitize(shift @$row, 0);
      $this{$key} -> {purpose}  = sanitize(shift @$row, 0);
      $this{$key} -> {status}   = sanitize(shift @$row, 0);
      $this{$key} -> {facility} = $names->{iucr2lso}->{$facilities[$i]}; # translate facility names to the names used at lightsources.org
      $this{$key} -> {name}     = $name; # use tabulated name if it exists...
      $this{$key} -> {name}     = $beamline_names{$facilities[$i]} -> {$key} if exists $beamline_names{$facilities[$i]} -> {$key};
      $this{$key} -> {website}  = q{};
      if ($content =~ m{<a href="(.*?)">(?:<u>)?$key}) {
	$this{$key} -> {website}  = $1;
	$this{$key} -> {website}  =~ s{\"><span style=.*\z}{};
	#(?:<span style="FONT-FAMILY: Arial" lang="DE">)?(?:<u>)
      };
    }
  }
  ## translate facility names to the names used at lightsources.org
  $beamlines{$names->{iucr2lso}->{$facilities[$i]}} = \%this;

  ## the Elettra one is just too hard to suss out using the simple search above -- "xafs" is a common word!
  ## the BESSY one is a typo like the following
  if ($region eq 'Europe') {
    my $elettra = $names->{iucr2lso}->{ELETTRA};
    my $bessy   = $names->{iucr2lso}->{BESSY};
    $beamlines{$elettra}->{XAFS}   ->{website} = 'http://www.elettra.trieste.it/experiments/beamlines/xafs';
    $beamlines{$bessy}  ->{BAMLine}->{website} = 'http://www.helmholtz-berlin.de/pubbin/igama_output?modus=einzel&sprache=en&gid=1658&typoid=37587';
  };

  ## these from Asia and Americas seem to suffer from sloppy editing -- they all have a zero-width anchor just before the URL
  if ($region eq 'Asia') {
    my $asrc   = $names->{iucr2lso}->{AichiSR};
    my $ritssr = $names->{iucr2lso}->{Aurora};
    my $uvsor = $names->{iucr2lso}->{UVSOR};
    $beamlines{$asrc}   ->{BL5S1} ->{website} = 'http://www.astf-kha.jp/synchrotron/en/userguide/gaiyou/bl5s1i_xxafs.html';
    $beamlines{$ritssr} ->{'BL-2'}->{website} = 'http://www.ritsumei.ac.jp/acd/re/src/beamline/bl2_2010.pdf';
    $beamlines{$uvsor}  ->{'BL1A'}->{website} = 'http://www.uvsor.ims.ac.jp/inforuvsor/beamlines.pdf';
    $beamlines{$uvsor}  ->{'BL3U'}->{website} = 'http://www.uvsor.ims.ac.jp/inforuvsor/beamlines.pdf';
  };

  if ($region eq 'Americas') {
    my $aps = $names->{iucr2lso}->{APS};
    $beamlines{$aps}->{'10-ID-B'} ->{website} = "https://beam.aps.anl.gov/pls/apsweb/beamline_display_pkg.display_beamline?p_beamline_num_c=14";
    $beamlines{$aps}->{'12-BM-B'} ->{website} = "https://beam.aps.anl.gov/pls/apsweb/beamline_display_pkg.display_beamline?p_beamline_num_c=18";
    $beamlines{$aps}->{'4-ID-C'}  ->{website} = "https://beam.aps.anl.gov/pls/apsweb/beamline_display_pkg.display_beamline?p_beamline_num_c=7";
    $beamlines{$aps}->{'4-ID-D'}  ->{website} = "https://beam.aps.anl.gov/pls/apsweb/beamline_display_pkg.display_beamline?p_beamline_num_c=31";
    $beamlines{$aps}->{'5-BM-D'}  ->{website} = "https://beam.aps.anl.gov/pls/apsweb/beamline_display_pkg.display_beamline?p_beamline_num_c=8";
    $beamlines{$aps}->{'9-BM-B,C'}->{website} = "https://beam.aps.anl.gov/pls/apsweb/beamline_display_pkg.display_beamline?p_beamline_num_c=82";
  };
};


#dd %beamlines;
open(my $S, '>:encoding(UTF-8)', $region.'.json');
print $S $json->encode( \%beamlines );
close $S;


sub sanitize {
  my ($string, $key) = @_;
  $string =~ s{\n}{}g;		                   # put entire text on one line
  $string =~ s{\s*-{3,}\s*}{ or };		   # convert line of dashes to ' or '
  $string =~ s{10(\d{1,2})}{10^$1}g if not $key;   # convert what's left of 10<sup>11</sup> to 10^11, but watch out for MAX-IV
  $string =~ s{\xA0}{ }g;			   # remove non-breaking space
  $string =~ s{\xCE\xBC}{u}g;			   # remove greek mu
  $string =~ s{\xC3\x97}{ x }g;			   # remove \times

  if ($key) {
    $string =~ s{(\(.*\))}{};
    $string =~ s{\r}{};
  };

  $string =~ s{\A\s+}{}g;	                   # strip whitespace at beginning
  $string =~ s{  +}{ }g;			   # condense whitespace
  $string =~ s{\s+\z}{}g;			   # strip whitespace at end
  return $string;
};
