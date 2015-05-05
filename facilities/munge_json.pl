#!/usr/bin/perl

#########################################################################
# We received a JSON dump of the information that goes into the         #
# lightsources.org "Light Sources of the World" web page.  This dump    #
# has all the information from the big table on that page as well as    #
# the contact information for each individual synchrotron.	        #
# 								        #
# This is a quick n dirty script to sanitize the data in that JSON      #
# dump and write the sanitized data to two, well-structured JSON        #
# files.							        #
# 								        #
# input:  lightsources.org.json				                #
# output: synchrotrons.json and fels.json			        #
#########################################################################

use strict;
use warnings;
use JSON;
use File::Slurp;
use Data::Dump::Color;
use HTML::Strip;

## json, decoded json, and HTML::Strip objects to work with
my $json = JSON->new->allow_nonref;
$json->pretty(1);		# legible
$json->canonical(1);		# predictable

my $data = $json->decode(read_file('lightsources.org.json'));

my $hs = HTML::Strip -> new();


## these are the hashes that will be serialized to JSON at the end
my %synchrotrons = ();
my %fels         = ();

my $i = 0;
foreach my $d (@$data) {

  ## these are the fields in the json dump file:
  #    field_abbreviation_value
  #    field_address_value
  #    field_category_value
  #    field_country_value
  #    field_media_contact_value
  #    field_website_url
  #    title

  ## clean up some missing data in the json dump file
  $d->{field_abbreviation_value} = 'AS'      if ($d->{title} =~ m{Australian});
  $d->{field_abbreviation_value} = 'ILSF'    if ($d->{title} =~ m{Iranian});
  $d->{field_abbreviation_value} = 'FERMI'   if ($d->{title} eq 'FERMI');

  ## more missing data in the json dump file
  $d->{field_category_value} = 'Synchrotron'         if ($d->{field_abbreviation_value} =~ m{TSRF|SuperSOR|MSRF|KSR|SRS|SRC|TSRF});
  $d->{field_category_value} = 'Free-Electron Laser' if ($d->{field_abbreviation_value} =~ m{SuperB FEL|XFEL|VUFEL|iFEL|DFELL});

  ## this skips over 3 US DoE nano centers
  next if not defined($d->{field_category_value});

  my $key = $d->{field_abbreviation_value};
  my $address = $d->{field_address_value};

  ## the following regular expressions were developed incrementally to
  ## match all the various ways that the contact information is
  ## specified in the json dump file
  my $phone = q{};
  if ($address =~ m{(?:Tel(?:|ephone)|Phone) ?[.:] (.*)(?=(?:<br>|</p>))}i) {
    $phone = $hs->parse($1);	# strip html tags and sanitize
    $phone =~ s{\A +}{};
    $phone =~ s{ +\z}{};
  };

  my $fax = q{};
  if ($address =~ m{Fax ?[.:] (.*)(?=</?[bp])}i) {
    $fax = $hs->parse($1);	# strip html tags and sanitize
    $fax =~ s{\A +}{};
    $fax =~ s{ +\z}{};
  };

  my $email = q{};
  if ($address =~ m{href="(.*?)(?=">)}) {
    $email = $1;		# sanitize email address
    $email =~ s{mailto:}{};
    $email =~ s{ }{.}g;
    $email =~ s{\"\.target=\"_blank}{};
  };

  ## the mailing address is everything in 'field_address_value' before
  ## the telephone number ... that seems pretty consistent
  my $post = q{};
  $address =~ s{[\t\r\n]}{}g;
  if ($address =~ m{(.+?)(?=(?:Tel(?:|ephone)|Director|Phone)[.:])}) {
    $post = $1;
  } else {
    $post = $address;
  };
  $post =~ s{<br>}{\n}g;	# strip html tags and sanitize
  $post = $hs->parse($post);
  $post =~ s{\A\s+}{};
  $post =~ s{\n+\z}{};

  if ($d->{field_category_value} =~ m{synchrotron}i) {

    $synchrotrons{$key} = {fullname => $d->{title},
			   website => $d->{field_website_url},
			   country => $d->{field_country_value},
			   post => $post,
			   phone => $phone,
			   fax => $fax,
			   email => $email,
			   active => JSON::true};


  } elsif ($d->{field_category_value} =~ m{free-electron}i) {
    $fels{$key} = {fullname => $d->{title},
		   website => $d->{field_website_url},
		   country => $d->{field_country_value},
		   post => $post,
		   phone => $phone,
		   fax => $fax,
		   email => $email,
		   active => JSON::true};

  };
  $hs->eof;
};

## specify our dear, departed facilities

%{$synchrotrons{NSLS}} = %{$synchrotrons{'NSLS-II'}};
$synchrotrons{NSLS}->{fullname} =~ s{ II}{};
$synchrotrons{NSLS}->{active} = JSON::false;

%{$synchrotrons{DORIS}} = %{$synchrotrons{'PETRA III'}};
$synchrotrons{DORIS}->{fullname} = 'Doppel-Ring-Speicher';
$synchrotrons{DORIS}->{active} = JSON::false;

$synchrotrons{SRS}->{active} = JSON::false;
$synchrotrons{SRC}->{active} = JSON::false;


## finally, serialize the data to JSON

open(my $S, '>:encoding(UTF-8)', 'synchrotrons.json');
print $S $json->encode( \%synchrotrons );
close $S;

open(my $F, '>:encoding(UTF-8)', 'fels.json');
print $F $json->encode( \%fels );
close $F;

