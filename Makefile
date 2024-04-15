DESTDIR=
prefix=/usr
sbindir=$(prefix)/sbin
datadir=$(prefix)/share
pkglibdir=$(prefix)/lib/ca-certificates
pkgdatadir=$(datadir)/ca-certificates
mandir=$(datadir)/man
systemdsystemunitdir=$(prefix)/lib/systemd/system

all:

install:
	install -D -m 755 update-ca-certificates   $(DESTDIR)$(sbindir)/update-ca-certificates
	install -D -m 644 update-ca-certificates.8 $(DESTDIR)$(mandir)/man8/update-ca-certificates.8
	install -D -m 644 ca-certificates.path     $(DESTDIR)$(systemdsystemunitdir)/ca-certificates.path
	install -D -m 644 ca-certificates.service  $(DESTDIR)$(systemdsystemunitdir)/ca-certificates.service
	install -D -m 644 ca-certificates-setup.service  $(DESTDIR)$(systemdsystemunitdir)/ca-certificates-setup.service
	install -D -m 755 java.run                 $(DESTDIR)$(pkglibdir)/update.d/50java.run
	install -D -m 755 openssl.run              $(DESTDIR)$(pkglibdir)/update.d/70openssl.run
	install -D -m 755 etc_ssl.run              $(DESTDIR)$(pkglibdir)/update.d/80etc_ssl.run
	# certbundle.run must be run after etc_ssl.run as it uses a timestamp from it
	install -D -m 755 certbundle.run           $(DESTDIR)$(pkglibdir)/update.d/99certbundle.run

package:
	obs/mkpackage

clean:

.PHONY: all install clean package
