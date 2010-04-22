/*
 * Import system SSL certificates to java keystore
 * Copyright (C) 2010 SUSE LINUX Products GmbH
 *
 * Author: Ludwig Nussel
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * version 2 as published by the Free Software Foundation.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */

import java.security.KeyStore;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.BufferedInputStream;
import java.io.FilenameFilter;
import java.util.HashSet;
import java.util.Enumeration;
import java.util.Iterator;

import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;

public class keystore 
{
    static HashSet<String> blacklist;

    public static void usage() {
        System.err.println("Usage: java keystore -keystore <keystore_file> -cadir <directory> [-storepass <password>|-f|-v]");
        System.err.println("");
        System.err.println("    -keystore <keystore_file>\tname of final keystore (required)");
        System.err.println("    -cadir <directory>\t\tdirectory contains certificates (required)");
        System.err.println("    -storepass <password>\tthe password");
        System.err.println("    -f\t\t\t\tfresh existing keystore");
        System.err.println("    -v\t\t\t\tbe verbose");
        System.err.println("    -h/--help\t\t\tshow this help");
    }

    public static void main(String[] args)
	throws java.security.KeyStoreException,
	      java.security.NoSuchAlgorithmException,
	      java.security.cert.CertificateException,
	      java.io.FileNotFoundException,
	      java.io.IOException
    {
	char[] password = null;
	String ksfilename = null;
	String cadirname = null;
	boolean verbose = false;
	boolean fresh = false;

        if (args.length == 0) {
            usage();
            System.exit(1);
        }


	if (!System.getProperty("java.vendor").equals("Free Software Foundation, Inc.")) {
		password = "changeit".toCharArray();
	}

	for (int i = 0; i < args.length; ++i) {
	    if (args[i].equals("-keystore")) {
		ksfilename = args[++i];
	    } else if (args[i].equals("-cadir")) {
		cadirname = args[++i];
	    } else if (args[i].equals("-storepass")) {
		password = args[++i].toCharArray();
	    } else if (args[i].equals("-v")) {
		verbose = true;
	    } else if (args[i].equals("-f")) {
		fresh = true;
	    } else if (args[i].equals("-h") || args[i].equals("--help")) {
                usage();
                System.exit(1);
	    } else {
		System.err.println("invalid argument: " + args[i]);
		System.err.println("type -h/--help for help");
		System.exit(1);
	    }
	}
	
	if (ksfilename == null) {
	    System.err.println("must specify -keystore");
	    return;
	}

	if (cadirname == null) {
	    System.err.println("must specify -cadir");
	    return;
	}

	File cadir = new File(cadirname);
	if (!cadir.isDirectory()) {
	    System.err.println("cadir is not a directory");
	    return;
	}

	blacklist = new HashSet<String>();
	// XXX: make a file
//	blacklist.add("foo");

	String certs[] = cadir.list(new FilenameFilter(){
	    public boolean accept(File dir, String name)
	    {
		if (!name.endsWith(".pem")) {
		    return false;
		}
		if (blacklist.contains(name)) {
		    return false;
		}
		return true;
	    }
	});

	KeyStore ks = KeyStore.getInstance(KeyStore.getDefaultType());

	FileInputStream storein = null;
	try {
	    File f = new File(ksfilename);
	    if (!fresh && f.exists()) {
		storein = new FileInputStream(ksfilename);
	    }
	    ks.load(storein, password);
	} finally {
	    if (storein != null) {
		storein.close();
	    }
	}

	HashSet<String> known = new HashSet<String>();
	for (Enumeration<String> a = ks.aliases(); a.hasMoreElements();) {
	    known.add(a.nextElement());
	}

	CertificateFactory cf = CertificateFactory.getInstance("X509");
	int added = 0;
	int removed = 0;

	for (int i = 0; i < certs.length; ++i) {
	    BufferedInputStream f = new BufferedInputStream(new FileInputStream(cadirname+"/"+certs[i]));
	    String marker = "-----BEGIN CERTIFICATE-----";
	    boolean found = false;

	    f.mark(80);
	    String line;
	    String alias = null;
	    // we need to parse and skip the "header"
	    while((line = readline(f)) != null) {
		if (line.equals(marker)) {
		    f.reset();
		    found = true;
		    break;
		} else if (line.startsWith("# alias=")) {
		    // FIXME: somehow UTF-8 encoding must be enforced here
		    alias = line.substring(8);
		}
		f.mark(80);
	    }
	    if (found) {
		if (alias == null) {
		    alias = certs[i].substring(0, certs[i].length()-4); // without .pem
		}
		alias = alias.toLowerCase();
		try {
		    X509Certificate cert = (X509Certificate)cf.generateCertificate(f);
		    if (known.contains(alias)) {
			if (verbose)
			    System.out.println("already known: " + alias);
			known.remove(alias);
		    } else {
			if (verbose)
			    System.out.println("adding " + alias);
			ks.setCertificateEntry(alias, cert);
			++added;
		    }
		} catch (java.security.cert.CertificateException ex) {
		    System.err.println("imporing " + certs[i] + " failed: " + ex.getCause());
		}
	    } else {
		System.out.println("skipping file with unrecognized format: " + certs[i]);
	    }
	}

	if (!known.isEmpty()) {
	    for (Iterator<String> it = known.iterator(); it.hasNext();) {
		String alias = it.next();
		if (verbose)
		    System.out.println("removing " + alias);
		ks.deleteEntry(alias);
		++removed;
	    }
	}

	if (added != 0 || removed != 0) {
	    FileOutputStream storeout = new FileOutputStream(ksfilename);
	    ks.store(storeout, password);
	    storeout.close();
	}

	System.out.println(added + " added, " + removed + " removed.");
    }

    public static String readline(BufferedInputStream in)
	throws java.io.IOException
    {
	StringBuffer buf = new StringBuffer(80);
	int c = in.read();
	while(c != -1 && c != '\n' && c != '\r') {
	    buf.append((char)c);
	    c = in.read();
	}
	if (c == '\r') {
	    in.mark(1);
	    c = in.read();
	    if (c != '\n')
		in.reset();
	}
	if (buf.length() == 0)
	    return null;

	return buf.toString();
    }
}
