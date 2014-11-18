#!/usr/bin/env python

'''
ABOUT:
Runs CALACS and acs_destipe on ACS/WFC images in RAW format.
The input file should be a RAW full-frame or subarray ACS/WFC file.
The output consists of the science-ready FLT and FLC files. 

DEPENDS:
CALACS 8.3.1


USE:
> python acs_destripe_plus.py -filename sub-array-raw-filename


@author: Leonardo UBEDA & Sara Ogaz
@organization: Space Telescope Science Institute
@team: Advanced Camera for Surveys


HISTORY:
@change: 16APR2014 Leonardo version 1.0
                   Based on instructions from Pey-Lian Lim  
         11SEP2014 Ogaz added capabilities for full frame processing
                   and stripe masking
         29OCT2014 Ogaz clean up for posting final script for users
         18NOV2014 Ogaz changed options/switches


'''

import sys,argparse
import os
import acstools
import shutil
from astropy.io import fits
from acstools import calacs
from acstools import acs_destripe
from acstools import acsccd
from acstools import acs2d
from acstools import acscte
 

def destripe_plus(sy,scimask1='None',scimask2='None',cte_correct=True):
    # verify that the RAW image exists in cwd
    cwddir = os.getcwd()
    if not os.path.exists(cwddir+'/'+sy):
        sys.exit(sy + " RAW file does not exist. Quitting now!")

    #check if 2K subarray or full frame
    is_sub2K = False
    header = fits.getheader(sy)
    ctecorr = header['PCTECORR']
    aperture = header['APERTURE']
    subarray_list=['WFC1-2K', 'WFC1-POL0UV', 'WFC1-POL0V', 'WFC1-POL60V',
					'WFC1-POL60UV', 'WFC1-POL120V', 'WFC1-POL120UV', 'WFC1-SMFL',
					'WFC1-IRAMPQ', 'WFC1-MRAMPQ', 'WFC2-2K', 'WFC2-ORAMPQ',
					'WFC2-SMFL', 'WFC2-POL0UV', 'WFC2-POL0V', 'WFC2-MRAMPQ']

    if header['SUBARRAY'] and cte_correct:
        if aperture in subarray_list:
            is_sub2K = True
        else:
            print 'Using non-2K subarray, turning CTE correction off'
            cte_correct = False       

    # run ACSCCD on RAW subarray
    acsccd.acsccd(sy)

    # execute destriping of the subarray (post-SM4 data only)
    acs_destripe.clean(sy.replace('raw','blv_tmp'), 'strp', clobber=False, maxiter=15, sigrej=2.0, mask1=scimask1, mask2=scimask2)
    os.rename(sy.replace('raw','blv_tmp_strp'),sy.replace('raw','blv_tmp'))

    #update subarray header
    if is_sub2K and cte_correct:
        fits.setval(sy.replace('raw','blv_tmp'),'PCTECORR',value='PERFORM')

    # perform CTE correction on destriped image
    if cte_correct:
    	if ctecorr == 'PERFORM':
        	acscte.acscte(sy.replace('raw','blv_tmp'))
        else:
        	print "PCTECORR not set to 'PERFORM', cannot run CTE correction"
        	cte_correct = False
        	
	# run ACS2D to get FLT and FLC images
    acs2d.acs2d(sy.replace('raw','blv_tmp'))
    if cte_correct:
        acs2d.acs2d(sy.replace('raw','blc_tmp'))

    # delete intermediate files
    os.system("rm "+sy.replace('raw','blv_tmp'))
    if cte_correct:
        os.system("rm "+sy.replace('raw','blc_tmp')) 
 
    print '__________________________________________________________'
    print " "
    print "FLT : ", sy.replace('raw','flt')
    if cte_correct:
        print "FLC : ", sy.replace('raw','flc')
    print " "


if __name__=='__main__':
    # Parse input parameters
    parser = argparse.ArgumentParser(description='Apply pixel-based CTE correction and stand alone de-stripe script on specified ACS/WFC RAW full frame or sub-array image.')
    parser.add_argument('-f', '--filename',default='NONE', type=str, help='Input rootname of RAW ACS/WFC image. \
                         Default is NONE - must input image filename.')
    parser.add_argument('--sci1_mask',default='None', type=str, help='Input filename of mask for SCI 1. \
                         Default is None if not using mask.')
    parser.add_argument('--sci2_mask',default='None', type=str, help='Input filename of mask for SCI 2. \
                         Default is None if not using mask.')
    parser.add_argument('-c', '--no_ctecorr',default=True, action='store_false', help='Turn cte correction off. \
                         on or off. Default to on (True).')

    options = parser.parse_args()
    if options.filename == 'NONE': 
        print "  "
        print "Usage       :   python acs_destripe_plus.py --filename full-raw-filename --sci1_mask mask1.fits --sci2_mask mask2.fits"
        print "For example :   python acs_destripe_plus.py --filename jc5001soq_raw.fits"
        print " "        
        sys.exit()

    destripe_plus(options.filename,scimask1=options.sci1_mask,scimask2=options.sci2_mask,cte_correct=options.no_ctecorr)
