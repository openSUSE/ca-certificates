DESTDIR=
prefix=/usr
pkglibdir=$(prefix)/lib/ca-certificates

all:

keystore.jar: keystore.java
	javac keystore.java
	jar cfe keystore.jar keystore keystore*.class

keystore: keystore.java
	gcj keystore.java --main=keystore -o keystore

install_jar: keystore.jar
	install -d $(DESTDIR)$(pkglibdir)/java
	install -m 644 keystore.jar $(DESTDIR)$(pkglibdir)/java

install_gcj: keystore
	install -d $(DESTDIR)$(pkglibdir)/java
	install -m 755 keystore $(DESTDIR)$(pkglibdir)/java
