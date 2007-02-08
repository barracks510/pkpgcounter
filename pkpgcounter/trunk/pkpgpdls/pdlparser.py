#
# pkpgcounter : a generic Page Description Language parser
#
# (c) 2003, 2004, 2005, 2006, 2007 Jerome Alet <alet@librelogiciel.com>
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

"""This module defines the base class for all Page Description Language parsers."""

import sys
import os
import popen2

KILOBYTE = 1024    
MEGABYTE = 1024 * KILOBYTE    
FIRSTBLOCKSIZE = 16 * KILOBYTE
LASTBLOCKSIZE = int(KILOBYTE / 4)

class PDLParserError(Exception):
    """An exception for PDLParser related stuff."""
    def __init__(self, message = ""):
        self.message = message
        Exception.__init__(self, message)
    def __repr__(self):
        return self.message
    __str__ = __repr__
        
class PDLParser :
    """Generic PDL parser."""
    totiffcommands = None        # Default command to convert to TIFF
    def __init__(self, infile, debug=0, firstblock=None, lastblock=None) :
        """Initialize the generic parser."""
        self.infile = infile
        self.debug = debug
        if firstblock is None :
            self.infile.seek(0)
            firstblock = self.infile.read(FIRSTBLOCKSIZE)
            try :
                self.infile.seek(-LASTBLOCKSIZE, 2)
                lastblock = self.infile.read(LASTBLOCKSIZE)
            except IOError :    
                lastblock = ""
            self.infile.seek(0)
        self.firstblock = firstblock
        self.lastblock = lastblock
        if not self.isValid() :
            raise PDLParserError, "Invalid file format !"
        try :
            import psyco 
        except ImportError :    
            pass # Psyco is not installed
        else :    
            # Psyco is installed, tell it to compile
            # the CPU intensive methods : PCL and PCLXL
            # parsing will greatly benefit from this.
            psyco.bind(self.getJobSize)
            
    def logdebug(self, message) :       
        """Logs a debug message if needed."""
        if self.debug :
            sys.stderr.write("%s\n" % message)
            
    def isValid(self) :    
        """Returns True if data is in the expected format, else False."""
        raise RuntimeError, "Not implemented !"
        
    def getJobSize(self) :    
        """Counts pages in a document."""
        raise RuntimeError, "Not implemented !"
        
    def convertToTiffMultiPage24NC(self, fname, dpi) :
        """Converts the input file to TIFF format, X dpi, 24 bits per pixel, uncompressed.
           Writes TIFF datas to the file named by fname.
        """   
        if self.totiffcommands :
            for totiffcommand in self.totiffcommands :
                self.infile.seek(0)
                error = False
                commandline = totiffcommand % locals()
                child = popen2.Popen4(commandline)
                try :
                    try :
                        data = self.infile.read(MEGABYTE)    
                        while data :
                            child.tochild.write(data)
                            child.tochild.flush()
                            data = self.infile.read(MEGABYTE)
                    except (IOError, OSError) :    
                        error = True
                finally :    
                    child.tochild.close()    
                    dummy = child.fromchild.read()
                    child.fromchild.close()
                    
                try :
                    status = child.wait()
                except OSError :    
                    error = True
                else :    
                    if os.WIFEXITED(status) :
                        if os.WEXITSTATUS(status) :
                            error = True
                    else :        
                        error = True
                    
                if not os.path.exists(fname) :
                    error = True
                elif not os.stat(fname).st_size :
                    error = True
                else :        
                    break       # Conversion worked fine it seems.
                self.logdebug("Command failed : %s" % repr(commandline))
            if error :
                raise PDLParserError, "Problem during conversion to TIFF."
        else :        
            raise PDLParserError, "Impossible to compute ink coverage for this file format."
            
def test(parserclass) :        
    """Test function."""
    if (len(sys.argv) < 2) or ((not sys.stdin.isatty()) and ("-" not in sys.argv[1:])) :
        sys.argv.append("-")
    totalsize = 0    
    for arg in sys.argv[1:] :
        if arg == "-" :
            infile = sys.stdin
            mustclose = 0
        else :    
            infile = open(arg, "rbU")
            mustclose = 1
        try :
            parser = parserclass(infile, debug=1)
            totalsize += parser.getJobSize()
        except PDLParserError, msg :    
            sys.stderr.write("ERROR: %s\n" % msg)
            sys.stderr.flush()
        if mustclose :    
            infile.close()
    print "%s" % totalsize
    
