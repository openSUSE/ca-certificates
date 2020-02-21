#
# spec file for package ca-certificates
#
# Copyright (c) 2020 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


# the ca bundle file was meant as compat option for e.g.
# proprietary packages. It's not meant to be used at all.
# unfortunately glib-networking has such a complicated abstraction
# on top of gnutls that we have to live with the bundle for now
%bcond_without cabundle

BuildRequires:  p11-kit-devel

Name:           ca-certificates
%define ssletcdir %{_sysconfdir}/ssl
%define cabundle  /var/lib/ca-certificates/ca-bundle.pem
%define sslcerts  %{ssletcdir}/certs
Version:        2+git20200129.d1a437d
Release:        0
Summary:        Utilities for system wide CA certificate installation
License:        GPL-2.0-or-later
Group:          Productivity/Networking/Security
Source0:        ca-certificates-%{version}.tar.xz
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
Url:            https://github.com/openSUSE/ca-certificates
#
Requires:       coreutils
Requires:       findutils
Requires:       p11-kit
Requires:       p11-kit-tools >= 0.23.1
Requires:       openssl(cli)
# needed for post
Requires(post): coreutils findutils p11-kit-tools
Recommends:     ca-certificates-mozilla
# we need to obsolete openssl-certs to make sure it's files are
# gone when a package providing actual certificates gets
# installed (bnc#594434).
Obsoletes:      openssl-certs
# no need for a separate Java package anymore. The bundle is
# created by C code.
Obsoletes:      java-ca-certificates = 1
Provides:       java-ca-certificates = %version-%release
BuildArch:      noarch

%description
Update-ca-certificates is intended to keep the certificate stores of
SSL libraries like OpenSSL or GnuTLS in sync with the system's CA
certificate store that is managed by p11-kit.

%prep
%setup -q

%build

%install
%if %{without cabundle}
rm -f certbundle.run
%endif
%make_install
ln -s service %{buildroot}%{_sbindir}/rcca-certificates
install -d -m 755 %{buildroot}%{trustdir_cfg}/{anchors,blacklist}
install -d -m 755 %{buildroot}%{trustdir_static}/{anchors,blacklist}
install -d -m 755 %{buildroot}%{ssletcdir}
install -d -m 755 %{buildroot}/etc/ca-certificates/update.d
install -d -m 755 %{buildroot}%{_prefix}/lib/ca-certificates/update.d
install -d -m 555 %{buildroot}/var/lib/ca-certificates/pem
install -d -m 555 %{buildroot}/var/lib/ca-certificates/openssl
install -d -m 755 %{buildroot}/%{_prefix}/lib/systemd/system
ln -s /var/lib/ca-certificates/pem %{buildroot}%{sslcerts}
%if %{with cabundle}
install -D -m 644 /dev/null %{buildroot}/%{cabundle}
ln -s %{cabundle} %{buildroot}%{ssletcdir}/ca-bundle.pem
%endif
install -D -m 644 /dev/null %{buildroot}/var/lib/ca-certificates/java-cacerts

# should be done in git.
mv %{buildroot}/%{_prefix}/lib/ca-certificates/update.d/{,50}java.run
mv %{buildroot}/%{_prefix}/lib/ca-certificates/update.d/{,70}openssl.run
mv %{buildroot}/%{_prefix}/lib/ca-certificates/update.d/{,80}etc_ssl.run
# certbundle.run must be run after etc_ssl.run as it uses a timestamp from it
mv %{buildroot}/%{_prefix}/lib/ca-certificates/update.d/{,99}certbundle.run

%pre
# migrate /etc/ssl/certs to a symlink
if [ "$1" -ne 0 -a -d %{sslcerts} -a ! -L %{sslcerts} ]; then
	# copy custom pem files to new location (bnc#875647)
	mkdir -p /etc/pki/trust/anchors
	for cert in %{sslcerts}/*.pem; do
		test -f "$cert" -a ! -L "$cert" || continue
		read firstline < "$cert"
		# skip package provided certificates (bnc#875647)
		if test "${firstline#\# generated by }" != "${firstline}" || rpm -qf "$cert" > /dev/null; then
			continue
		fi
		# create a p11-kit header that set the label of
		# the certificate to the file name. That ensures
		# that the certificate gets the same name in
		# /etc/ssl/certs as before
		bn="${cert##*/}"
		(
		cat <<-EOF
			# created by update-ca-certificates from
			# $cert
			[p11-kit-object-v1]
			class: certificate
			label: "${bn%.pem}"
			trusted: true
		EOF
		cat $cert
		) > "/etc/pki/trust/$bn"
	done
	mv -T --backup=numbered %{sslcerts} %{sslcerts}.rpmsave && ln -s /var/lib/ca-certificates/pem %{sslcerts}
fi
%service_add_pre ca-certificates.path ca-certificates.service

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
%service_add_post ca-certificates.path ca-certificates.service

%preun
%service_del_preun ca-certificates.path ca-certificates.service

%postun
if [ "$1" -eq 0 ]; then
	rm -rf /var/lib/ca-certificates/pem /var/lib/ca-certificates/openssl
fi
%service_del_postun ca-certificates.path ca-certificates.service

%clean
rm -rf %{buildroot}

%files
%defattr(-, root, root)
%license COPYING
%doc README
%dir %{pkidir_cfg}
%dir %{trustdir_cfg}
%dir %{trustdir_cfg}/anchors
%dir %{trustdir_cfg}/blacklist
%dir %{pkidir_static}
%dir %{trustdir_static}
%dir %{trustdir_static}/anchors
%dir %{trustdir_static}/blacklist
%dir %ssletcdir
%sslcerts
%ghost /var/lib/ca-certificates/java-cacerts
%dir /etc/ca-certificates
%dir /etc/ca-certificates/update.d
%dir %{_prefix}/lib/ca-certificates
%dir %{_prefix}/lib/ca-certificates/update.d
 %{_prefix}/lib/systemd/system/*
%dir /var/lib/ca-certificates
%dir /var/lib/ca-certificates/pem
%dir /var/lib/ca-certificates/openssl
%{_sbindir}/rcca-certificates
%{_sbindir}/update-ca-certificates
%{_mandir}/man8/update-ca-certificates.8*
%{_prefix}/lib/ca-certificates/update.d/*java.run
%{_prefix}/lib/ca-certificates/update.d/*etc_ssl.run
%{_prefix}/lib/ca-certificates/update.d/*openssl.run
#
%if %{with cabundle}
%{ssletcdir}/ca-bundle.pem
%ghost %{cabundle}
%{_prefix}/lib/ca-certificates/update.d/*certbundle.run
%endif

%changelog
