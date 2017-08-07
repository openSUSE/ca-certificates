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
	install -D -m 755 update-ca-certificates $(DESTDIR)$(sbindir)/update-ca-certificates
	install -D -m 644 update-ca-certificates.8 $(DESTDIR)$(mandir)/man8/update-ca-certificates.8
	install -D -m 644 ca-certificates.path $(DESTDIR)$(systemdsystemunitdir)/ca-certificates.path
	install -D -m 644 ca-certificates.service $(DESTDIR)$(systemdsystemunitdir)/ca-certificates.service
	for i in *.run; do install -D -m 755 $$i $(DESTDIR)$(pkglibdir)/update.d/$$i; done

package:
	obs/mkpackage

clean:

.PHONY: all install clean package
