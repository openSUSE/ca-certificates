#
# spec file for package ca-certificates
#
# Copyright (c) 2013 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


# the ca bundle file was meant as compat option for e.g.
# proprietary packages. It's not meant to be used at all.
# unfortunately glib-networking has such a complicated abstraction
# on top of gnutls that we have to live with the bundle for now
%bcond_without cabundle

BuildRequires:  openssl
BuildRequires:  p11-kit-devel

Name:           ca-certificates
%define ssletcdir %{_sysconfdir}/ssl
%define cabundle  /var/lib/ca-certificates/ca-bundle.pem
%define sslcerts  %{ssletcdir}/certs
Version:        1_201310161709
Release:        0
Summary:        Utilities for system wide CA certificate installation
License:        GPL-2.0+
Group:          Productivity/Networking/Security
Source0:        ca-certificates-%{version}.tar.xz
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
Url:            https://github.com/openSUSE/ca-certificates
#
Requires:       openssl
Requires:       p11-kit
Requires:       p11-kit-tools >= 0.19.3
# needed for %post
Requires(post): coreutils openssl p11-kit-tools
Recommends:     ca-certificates-mozilla
# we need to obsolete openssl-certs to make sure it's files are
# gone when a package providing actual certificates gets
# installed (bnc#594434).
Obsoletes:      openssl-certs < 0.9.9
# no need for a separate Java package anymore. The bundle is
# created by C code.
Obsoletes:      java-ca-certificates = 1
Provides:       java-ca-certificates = %version-%release
BuildArch:      noarch

%description
Utilities for system wide CA certificate installation

%prep
%setup -q

%build

%install
%if %{without cabundle}
rm -f certbundle.run
%endif
%make_install
install -d m 755 %{buildroot}%{trustdir_cfg}/{anchors,blacklist}
install -d m 755 %{buildroot}%{trustdir_static}/{anchors,blacklist}
install -d m 755 %{buildroot}/etc/ssl/certs
install -d m 755 %{buildroot}/etc/ca-certificates/update.d
install -d m 755 %{buildroot}%{_prefix}/lib/ca-certificates/update.d
install -d m 755 %{buildroot}/var/lib/ca-certificates/pem
install -d m 755 %{buildroot}/var/lib/ca-certificates/openssl
%if %{with cabundle}
install -D -m 644 /dev/null %{buildroot}/%{cabundle}
ln -s %{cabundle} %{buildroot}%{ssletcdir}/ca-bundle.pem
%endif
install -D -m 644 /dev/null %{buildroot}/var/lib/ca-certificates/java-cacerts

%post
if [ -s /etc/ca-certificates.conf ]; then
	while read line; do
		[ ${line#\!} != "$line"  ] || continue
		cert="${line#\!*/}"
		ln -s /usr/share/ca-certificates/anchors/"$cert" %{trustdir_cfg}/blacklist
	done < /etc/ca-certificates.conf
	echo "/etc/ca-certificates.conf converted and saved as /etc/ca-certificates.conf.rpmsave"
	mv /etc/ca-certificates.conf /etc/ca-certificates.conf.rpmsave
fi
# force rebuilding all certificate stores.
# This also makes sure we update the hash links in /etc/ssl/certs
# as openssl changed the hash format between 0.9.8 and 1.0
update-ca-certificates -f || true

%postun
if [ "$1" -eq 0 ]; then
	rm -rf /var/lib/ca-certificates/{pem,openssl}
fi

%clean
rm -rf %{buildroot}

%files
%defattr(-, root, root)
%doc COPYING README
%dir %{pkidir_cfg}
%dir %{trustdir_cfg}
%dir %{trustdir_cfg}/anchors
%dir %{trustdir_cfg}/blacklist
%dir %{pkidir_static}
%dir %{trustdir_static}
%dir %{trustdir_static}/anchors
%dir %{trustdir_static}/blacklist
%dir /etc/ssl/certs
%ghost /var/lib/ca-certificates/java-cacerts
%dir /etc/ca-certificates
%dir /etc/ca-certificates/update.d
%dir %{_prefix}/lib/ca-certificates
%dir %{_prefix}/lib/ca-certificates/update.d
%dir /var/lib/ca-certificates
%dir /var/lib/ca-certificates/pem
%dir /var/lib/ca-certificates/openssl
%{_sbindir}/update-ca-certificates
%{_mandir}/man8/update-ca-certificates.8*
%{_prefix}/lib/ca-certificates/update.d/java.run
%{_prefix}/lib/ca-certificates/update.d/etc_ssl.run
%{_prefix}/lib/ca-certificates/update.d/openssl.run
#
%if %{with cabundle}
%{ssletcdir}/ca-bundle.pem
%ghost %{cabundle}
%{_prefix}/lib/ca-certificates/update.d/certbundle.run
%endif

%changelog
