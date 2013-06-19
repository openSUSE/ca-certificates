DESTDIR=
prefix=/usr
sbindir=$(prefix)/sbin
datadir=$(prefix)/share
pkglibdir=$(prefix)/lib/ca-certificates
pkgdatadir=$(datadir)/ca-certificates
mandir=$(datadir)/man

all:

install:
	install -D -m 755 update-ca-certificates $(DESTDIR)$(sbindir)/update-ca-certificates
	install -D -m 644 update-ca-certificates.8 $(DESTDIR)$(mandir)/man8/update-ca-certificates.8
	for i in *.run; do install -D -m 755 $$i $(DESTDIR)$(pkglibdir)/update.d/$$i; done

clean:

.PHONY: all install clean
