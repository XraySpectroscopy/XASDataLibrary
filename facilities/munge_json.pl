#!/usr/bin/perl

## quick n dirty script to sanitize the data provided by lightsources.org

use strict;
use warnings;
use JSON;
use File::Slurp;
use Data::Dump::Color;
use HTML::Strip;

my $json = JSON->new->allow_nonref;
$json->pretty(1);

my $data = $json->decode(read_file('lightsources.org.json'));

my $hs = HTML::Strip -> new();


my %synchrotrons = ();
my %fels         = ();

my $i = 0;
foreach my $d (@$data) {

  ## clean up some missing data in the file
  $d->{field_abbreviation_value} = 'AS'      if ($d->{title} =~ m{Australian});
  $d->{field_abbreviation_value} = 'ILSF'    if ($d->{title} =~ m{Iranian});
  $d->{field_abbreviation_value} = 'FERMI'   if ($d->{title} eq 'FERMI');

  $d->{field_category_value} = 'Synchrotron'         if ($d->{field_abbreviation_value} =~ m{TSRF|SuperSOR|MSRF|KSR|SRS|SRC|TSRF});
  $d->{field_category_value} = 'Free-Electron Laser' if ($d->{field_abbreviation_value} =~ m{SuperB FEL|XFEL|VUFEL|iFEL|DFELL});

  ## this skips over 3 US DoE nano centers
  next if not defined($d->{field_category_value});

  my $key = $d->{title};
  my $address = $d->{field_address_value};

  my $phone = q{};
  if ($address =~ m{(?:Tel(?:|ephone)|Phone) ?[.:] (.*)(?=(?:<br>|</p>))}i) {
    $phone = $hs->parse($1);
    $phone =~ s{\A +}{};
    $phone =~ s{ +\z}{};
  };

  my $fax = q{};
  if ($address =~ m{Fax ?[.:] (.*)(?=</?[bp])}i) {
    $fax = $hs->parse($1);
    $fax =~ s{\A +}{};
    $fax =~ s{ +\z}{};
  };

  my $email = q{};
  if ($address =~ m{href="(.*?)(?=">)}) {
    $email = $1;
    $email =~ s{mailto:}{};
    $email =~ s{ }{.}g;
    $email =~ s{\"\.target=\"_blank}{};
  };

  my $post = q{};
  $address =~ s{[\t\r\n]}{}g;
  if ($address =~ m{(.+?)(?=(?:Tel(?:|ephone)|Director|Phone)[.:])}) {
    $post = $1;
  } else {
    $post = $address;
  };
  $post =~ s{<br>}{\n}g;
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

## the dear departed...

$synchrotrons{NSLS} = $synchrotrons{'NSLS-II'};
$synchrotrons{NSLS}->{fullname} =~ s{ II}{};
$synchrotrons{NSLS}->{active} = JSON::false;

$synchrotrons{DORIS} = $synchrotrons{'PETRA III'};
$synchrotrons{DORIS}->{fullname} =~ 'Doppel-Ring-Speicher';
$synchrotrons{DORIS}->{active} = JSON::false;

$synchrotrons{SRS}->{active} = JSON::false;
$synchrotrons{SRC}->{active} = JSON::false;


open(my $S, '>:encoding(UTF-8)', 'synchrotrons.json');
print $S $json->encode( \%synchrotrons );
close $S;

open(my $F, '>:encoding(UTF-8)', 'fels.json');
print $F $json->encode( \%fels );
close $F;

# field_abbreviation_value
# field_address_value
# field_category_value
# field_country_value
# field_media_contact_value
# field_website_url
# title
