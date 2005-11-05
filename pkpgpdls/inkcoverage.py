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

from PIL import Image

def getPercentCMYK(img, nbpix) :
    """Extracts the percents of Cyan, Magenta, Yellow, and Black from a picture.
     
       PIL doesn't produce useable CMYK for our algorithm, so we use the algorithm from PrintBill.
       Psyco speeds this function up by around 2.5 times on my computer.
    """
    if img.mode != "RGB" :
        img = img.convert("RGB")
    cyan = magenta = yellow = black = 0    
    for (r, g, b) in img.getdata() :
        if r == g == b :
            black += 255 - r
        else :    
            cyan += 255 - r
            magenta += 255 - g
            yellow += 255 - b
    return { "C" : 100.0 * (cyan / 255.0) / nbpix,
             "M" : 100.0 * (magenta / 255.0) / nbpix,
             "Y" : 100.0 * (yellow / 255.0) / nbpix,
             "K" : 100.0 * (black / 255.0) / nbpix,
           }
        
def getPercent(img, nbpix) :
    """Extracts the percents per color component from a picture.
      
       Faster without Pysco.
    """
    result = {}     
    bands = img.split()
    for (i, bandname) in enumerate(img.getbands()) :
        result[bandname] = 100.0 * (reduce(lambda current, next: current + (next[1] * next[0]), enumerate(bands[i].histogram()), 0) / 255.0) / nbpix
    return result    
        
def getPercentBlack(img, nbpix) :
    """Extracts the percents of Black from a picture, once converted to gray levels."""
    if img.mode != "L" :
        img = img.convert("L")
    return { "L" : 100.0 - getPercent(img, nbpix)["L"] }
    
def getPercentRGB(img, nbpix) :
    """Extracts the percents of Red, Green, Blue from a picture, once converted to RGB."""
    if img.mode != "RGB" :
        img = img.convert("RGB")
    return getPercent(img, nbpix)    
    
def getPercentCMY(img, nbpix) :
    """Extracts the percents of Cyan, Magenta, and Yellow from a picture once converted to RGB."""
    result = getPercentRGB(img, nbpix)
    return { "C" : 100.0 - result["R"],
             "M" : 100.0 - result["G"],
             "Y" : 100.0 - result["B"],
           }
    
def getPercents(fname) :
    """Extracts the ink percentages from an image."""
    image = Image.open(fname)
    nbpixels = image.size[0] * image.size[1]
    black = getPercentBlack(image, nbpixels)
    rgb = getPercentRGB(image, nbpixels)
    cmy = getPercentCMY(image, nbpixels)
    cmyk = getPercentCMYK(image, nbpixels)
    print "Black : ", black
    print "RGB : ", rgb
    print "CMY : ", cmy
    print "CMYK : ", cmyk

if __name__ == "__main__" :
    getPercents(sys.argv[1])
