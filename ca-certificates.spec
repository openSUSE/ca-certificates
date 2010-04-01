#
# spec file for package ca-certificates (Version 1)
#
# Copyright (c) 2010 SUSE LINUX Products GmbH, Nuernberg, Germany.
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

# norootforbuild

BuildRequires:  openssl

Name:           ca-certificates
%define ssletcdir %{_sysconfdir}/ssl
%define etccadir  %{ssletcdir}/certs
%define cabundle  %{ssletcdir}/cert.pem
%define usrcadir  %{_datadir}/ca-certificates
License:        GPLv2+
Group:          Productivity/Networking/Security
Version:        1
Release:        1
Summary:        Utilities for system wide CA certificate installation
Source0:        update-ca-certificates
Source1:        update-ca-certificates.8
Source2:        GPL-2.0.txt
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch
Url:            http://gitorious.org/opensuse/ca-certificates
#
Requires:       openssl

%description
Utilities for system wide CA certificate installation

%prep
%setup -qcT
install -m 755 %{SOURCE0} .
install -m 644 %{SOURCE1} .
install -m 644 %{SOURCE2} COPYING

%build

%install
mkdir -p %{buildroot}/%{etccadir}
mkdir -p %{buildroot}/%{usrcadir}
mkdir -p %{buildroot}/%{_sbindir}
mkdir -p %{buildroot}/%{_mandir}/man8
mkdir -p %{buildroot}/etc/ca-certificates/update.d
install -m 644 /dev/null %{buildroot}/%{cabundle}
install -m 644 /dev/null %{buildroot}/etc/ca-certificates.conf

install -m 755 update-ca-certificates %{buildroot}/%{_sbindir}
install -m 644 update-ca-certificates.8 %{buildroot}/%{_mandir}/man8

%clean
rm -rf %{buildroot}

%files
%defattr(-, root, root)
%dir %{usrcadir}
%dir %{etccadir}
%doc COPYING
%ghost %config(noreplace) /etc/ca-certificates.conf
%ghost %{cabundle}
%dir /etc/ca-certificates
%dir /etc/ca-certificates/update.d
%{_sbindir}/update-ca-certificates
%{_mandir}/man8/update-ca-certificates.8*

%changelog
