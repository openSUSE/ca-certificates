#!/usr/bin/perl -w
# 
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is the Netscape security libraries.
#
# The Initial Developer of the Original Code is
# Netscape Communications Corporation.
# Portions created by the Initial Developer are Copyright (C) 1994-2000
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****
use strict;
use Encode;

my $count = 0;
my @certificates = ();
my %trusts = ();
my $object = undef;
my $output_trustbits;

my %trust_types = (
  "CKA_TRUST_DIGITAL_SIGNATURE" => "digital-signature",
  "CKA_TRUST_NON_REPUDIATION" => "non-repudiation",
  "CKA_TRUST_KEY_ENCIPHERMENT" => "key-encipherment",
  "CKA_TRUST_DATA_ENCIPHERMENT" => "data-encipherment",
  "CKA_TRUST_KEY_AGREEMENT" => "key-agreement",
  "CKA_TRUST_KEY_CERT_SIGN" => "cert-sign",
  "CKA_TRUST_CRL_SIGN" => "crl-sign",
  "CKA_TRUST_SERVER_AUTH" => "server-auth",
  "CKA_TRUST_CLIENT_AUTH" => "client-auth",
  "CKA_TRUST_CODE_SIGNING" => "code-signing",
  "CKA_TRUST_EMAIL_PROTECTION" => "email-protection",
  "CKA_TRUST_IPSEC_END_SYSTEM" => "ipsec-end-system",
  "CKA_TRUST_IPSEC_TUNNEL" => "ipsec-tunnel",
  "CKA_TRUST_IPSEC_USER" => "ipsec-user",
  "CKA_TRUST_TIME_STAMPING" => "time-stamping",
  "CKA_TRUST_STEP_UP_APPROVED" => "step-up-approved",
);

my %openssl_trust = (
  CKA_TRUST_SERVER_AUTH => 'serverAuth',
  CKA_TRUST_CLIENT_AUTH => 'clientAuth',
  CKA_TRUST_EMAIL_PROTECTION => 'emailProtection',
  CKA_TRUST_CODE_SIGNING => 'codeSigning',
);

if (@ARGV && $ARGV[0] eq '--trustbits') {
	shift @ARGV;
	$output_trustbits = 1;
}

sub colonhex
{
  return join(':', unpack("(H2)*", $_[0]));
}

sub handle_object($)
{
  my $object = shift;
  return unless $object;
  if($object->{'CKA_CLASS'} eq 'CKO_CERTIFICATE' && $object->{'CKA_CERTIFICATE_TYPE'} eq 'CKC_X_509') {
    push @certificates, $object;
  } elsif ($object->{'CKA_CLASS'} eq 'CKO_NETSCAPE_TRUST') {
    my $label = $object->{'CKA_LABEL'};
    my $serial = colonhex($object->{'CKA_SERIAL_NUMBER'});
    die "$label exists ($serial)" if exists($trusts{$label.$serial});
    $trusts{$label.$serial} = $object;
  } elsif ($object->{'CKA_CLASS'} eq 'CKO_NETSCAPE_BUILTIN_ROOT_LIST') {
    # ignore
  } else {
    print STDERR "class ", $object->{'CKA_CLASS'} ," not handled\n";
  }
}

while(<>) {
  my @fields = ();

  s/^((?:[^"#]+|"[^"]*")*)(\s*#.*$)/$1/;
  next if (/^\s*$/);

  if( /(^CVS_ID\s+)(.*)/ ) {
    next;
  }

  # This was taken from the perl faq #4.
  my $text = $_;
  push(@fields, $+) while $text =~ m{
      "([^\"\\]*(?:\\.[^\"\\]*)*)"\s?  # groups the phrase inside the quotes
    | ([^\s]+)\s?
    | \s
  }gx;
  push(@fields, undef) if substr($text,-1,1) eq '\s';

  if( $fields[0] =~ /BEGINDATA/ ) {
    next;
  }

  if( $fields[1] =~ /MULTILINE/ ) {
    die "expected MULTILINE_OCTAL" unless $fields[1] eq 'MULTILINE_OCTAL';
    $fields[2] = "";
    while(<>) {
      last if /END/;
      chomp;
      $fields[2] .= pack("C", oct($+)) while $_ =~ /\G\\([0-3][0-7][0-7])/g;
    }
  }

  if( $fields[0] =~ /CKA_CLASS/ ) {
    $count++;
    handle_object($object);
    $object = {};
  }

  $object->{$fields[0]} = $fields[2];
}
handle_object($object);
undef $object;

use MIME::Base64;
for my $cert (@certificates) {
  my $alias = $cert->{'CKA_LABEL'};
  my $serial = colonhex($cert->{'CKA_SERIAL_NUMBER'});
  if(!exists($trusts{$alias.$serial})) {
    print STDERR "NO TRUST: $alias\n";
    next;
  }
  # check trust. We only include certificates that are trusted for identifying
  # web sites
  my $trust = $trusts{$alias.$serial};
  my @addtrust;
  my @addtrust_openssl;
  my $trusted;
  if ($output_trustbits) {
	  for my $type (keys %trust_types) {
		  if (exists $trust->{$type}
		  && $trust->{$type} eq 'CKT_NETSCAPE_TRUSTED_DELEGATOR') {
			  push @addtrust, $trust_types{$type};
			  if (exists $openssl_trust{$type}) {
				  push @addtrust_openssl, $openssl_trust{$type};
			  }
			  $trusted = 1;
		  }
	  }
  } else {
	  if($trust->{'CKA_TRUST_SERVER_AUTH'} eq 'CKT_NETSCAPE_TRUSTED_DELEGATOR') {
		  $trusted = 1;
	  }
  }

  if (!$trusted) {
	  my $t = $trust->{'CKA_TRUST_SERVER_AUTH'};
	  $t =~ s/CKT_NETSCAPE_//;
	  print STDERR "$t: $alias\n";
	  next;
  }

  if ($alias =~ /\\x[0-9a-fA-F]{2}/) {
	  $alias =~ s/\\x([0-9a-fA-F]{2})/chr(hex($1))/ge; # thanks mls!
	  $alias = Encode::decode("UTF-8", $alias);
  }
  my $file = $alias;
  $alias =~ s/'/-/g;
  $file =~ s/[^[:alnum:]\\]+/_/g;
  $file = Encode::encode("UTF-8", $file);
  if (-e $file.'.pem') {
    my $i = 1;
    while (-e $file.".$i.pem") {
      ++$i;
    }
    $file .= ".$i.pem";
  } else {
    $file .= '.pem';
  }
  if (!open(O, '>', $file)) {
	  print STDERR "$file: $!\n";
	  next;
  }
  print "$file\n" if $ENV{'VERBOSE'};
  my $value = $cert->{'CKA_VALUE'};
  if ($output_trustbits) {
	  print O "# alias=",Encode::encode("UTF-8", $alias),"\n";
	  print O "# trust=",join(" ", @addtrust),"\n";
	  if (@addtrust_openssl) {
		  print O "# openssl-trust=",join(" ", @addtrust_openssl),"\n";
	  }
  }
  print O "-----BEGIN CERTIFICATE-----\n";
  print O encode_base64($value);
  print O "-----END CERTIFICATE-----\n";
  close O;
}
