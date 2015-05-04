#!/usr/bin/perl

## quick n dirty script to sanitize the data provided by lightsources.org

use strict;
use warnings;
use JSON;
use File::Slurp;
use Data::Dump::Color;
use HTML::Strip;

my $data = decode_json(read_file('lightsources.org.json'));
#dd $data;

my $hs = HTML::Strip -> new();


my %synchrotrons = ();
my %fels         = ();

my $i = 0;
foreach my $d (@$data) {
  next if not defined($d->{field_category_value});
  my %hash;
  my $key = $d->{field_abbreviation_value} || $d->{title};
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
  #if ($address =~ m{e-?mail(?: Contact)?[.:]? (.*)(?=</?[bp])}i) {
  if ($address =~ m{href="(.*?)(?=">)}) {
    $email = $1;
    $email =~ s{mailto:}{};
    # } else {
    #   $email = $hs->parse($1);
    #   $email =~ s{\A +}{};
    #   $email =~ s{ +\z}{};
    #   print $email, $/;
    # };
    $email =~ s{ }{.}g;
  };

  my $post = q{};
  $address =~ s{[\t\r\n]}{}g;
  if ($address =~ m{(.+?)(?=(?:Tel(?:|ephone)|Director|Phone)[.:])}) {
    $post = $1;
  } else {
    $post = $address;
  };
  #$post =~ s{</?p>}{}g;
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
			   email => $email};


  } elsif ($d->{field_category_value} =~ m{free-electron}i) {
    $fels{$key} = {fullname => $d->{title},
		   website => $d->{field_website_url},
		   country => $d->{field_country_value},
		   post => $post,
		   phone => $phone,
		   fax => $fax,
		   email => $email};

  };
  $hs->eof;
};


open(my $S, '>', 'synchrotrons.json');
print $S encode_json( \%synchrotrons );
close $S;

open(my $F, '>', 'fels.json');
print $F encode_json( \%fels );
close $F;

# field_abbreviation_value
# field_address_value
# field_category_value
# field_country_value
# field_media_contact_value
# field_website_url
# title
