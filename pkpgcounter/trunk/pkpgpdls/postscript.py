#! /usr/bin/env python
# -*- coding: ISO-8859-15 -*-
#
# pkpgcounter : a generic Page Description Language parser
#
# (c) 2003, 2004, 2005 Jerome Alet <alet@librelogiciel.com>
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# $Id$
#

import sys
import popen2

import pdlparser

class Parser(pdlparser.PDLParser) :
    """A parser for PostScript documents."""
    def isValid(self) :    
        """Returns 1 if data is PostScript, else 0."""
        if self.firstblock.startswith("%!") or \
           self.firstblock.startswith("\004%!") or \
           self.firstblock.startswith("\033%-12345X%!PS") or \
           ((self.firstblock[:128].find("\033%-12345X") != -1) and \
             ((self.firstblock.find("LANGUAGE=POSTSCRIPT") != -1) or \
              (self.firstblock.find("LANGUAGE = POSTSCRIPT") != -1) or \
              (self.firstblock.find("LANGUAGE = Postscript") != -1))) or \
              (self.firstblock.find("%!PS-Adobe") != -1) :
            if self.debug :  
                sys.stderr.write("DEBUG: Input file is in the PostScript format.\n")
            return 1
        else :    
            return 0
        
    def throughGhostScript(self) :
        """Get the count through GhostScript, useful for non-DSC compliant PS files."""
        if self.debug :
            sys.stderr.write("Internal parser sucks, using GhostScript instead...\n")
        self.infile.seek(0)
        command = 'gs -sDEVICE=bbox -dNOPAUSE -dBATCH -dQUIET - 2>&1 | grep -c "%%HiResBoundingBox:" 2>/dev/null'
        child = popen2.Popen4(command)
        try :
            data = self.infile.read(pdlparser.MEGABYTE)    
            while data :
                child.tochild.write(data)
                data = self.infile.read(pdlparser.MEGABYTE)
            child.tochild.flush()
            child.tochild.close()    
        except (IOError, OSError), msg :    
            raise pdlparser.PDLParserError, "Problem during analysis of Binary PostScript document : %s" % msg
            
        pagecount = 0
        try :
            pagecount = int(child.fromchild.readline().strip())
        except (IOError, OSError, AttributeError, ValueError), msg :
            raise pdlparser.PDLParserError, "Problem during analysis of Binary PostScript document : %s" % msg
        child.fromchild.close()
        
        try :
            child.wait()
        except OSError, msg :    
            raise pdlparser.PDLParserError, "Problem during analysis of Binary PostScript document : %s" % msg
        return pagecount * self.copies
        
    def natively(self) :
        """Count pages in a DSC compliant PostScript document."""
        self.infile.seek(0)
        pagecount = 0
        for line in self.infile.xreadlines() : 
            if line.startswith(r"%%Page: ") :
                pagecount += 1
            elif line.startswith(r"%%Requirements: numcopies(") :    
                try :
                    number = int(line.strip().split('(')[1].split(')')[0])
                except :     
                    pass
                else :    
                    if number > self.copies :
                        self.copies = number
            elif line.startswith(r"%%BeginNonPPDFeature: NumCopies ") :
                # handle # of copies set by some Windows printer driver
                try :
                    number = int(line.strip().split()[2])
                except :     
                    pass
                else :    
                    if number > self.copies :
                        self.copies = number
            elif line.startswith("1 dict dup /NumCopies ") :
                # handle # of copies set by mozilla/kprinter
                try :
                    number = int(line.strip().split()[4])
                except :     
                    pass
                else :    
                    if number > self.copies :
                        self.copies = number
        return pagecount * self.copies
        
    def getJobSize(self) :    
        """Count pages in PostScript document."""
        self.copies = 1
        return self.natively() or self.throughGhostScript()
        
def test() :        
    """Test function."""
    if (len(sys.argv) < 2) or ((not sys.stdin.isatty()) and ("-" not in sys.argv[1:])) :
        sys.argv.append("-")
    totalsize = 0    
    for arg in sys.argv[1:] :
        if arg == "-" :
            infile = sys.stdin
            mustclose = 0
        else :    
            infile = open(arg, "rb")
            mustclose = 1
        try :
            parser = Parser(infile, debug=1)
            totalsize += parser.getJobSize()
        except pdlparser.PDLParserError, msg :    
            sys.stderr.write("ERROR: %s\n" % msg)
            sys.stderr.flush()
        if mustclose :    
            infile.close()
    print "%s" % totalsize
    
if __name__ == "__main__" :    
    test()
