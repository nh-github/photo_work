#!/usr/bin/env python
"""
SYNOPSIS

    cropresize.py [-h,--help] [-v,--verbose] [--version]
            [--imagedir=IMAGEDIR, -i IMAGEDIR]

DESCRIPTION

    TODO This describes how to use this script. This docstring
    will be printed by the script if there is an error or
    if the user requests help (-h or --help).

EXAMPLES

    cropresize.py -i <dir>
    cropresize.py -i .  #run for current directory
    cropresize.py       #run for current directory (also)

EXIT STATUS

    TODO: List exit codes

AUTHOR

    Noah Hafner <nmh+misc2010@nomh.org>
    ref:    http://code.activestate.com/recipes/528877/ (Noah Spurrier)

LICENSE

    This program is available under a FreeBSD-like license
    Copyright held by Noah Hafner 2010

VERSION

    $Id$
"""

import argparse
import hashlib
import logging
import optparse
import os
import re
import shutil
import subprocess
import sys
import time
import traceback

###
#Configurations:
#external utilities
img_mod='gm mogrify'

#source directory possibilities (regular expressions)
source_dir_list = [
    "jpg$",
    "[0-9]*_PANA$",
    ]
#extensions
imgExt=[#ref:   http://en.wikipedia.org/wiki/JPEG
    "jpg",
    "jpeg",
    "jpe",
    "jif",
    "jfif",
    "jfi",
    ]
rawExt=[#ref:   http://en.wikipedia.org/wiki/Raw_image_format
    '.3fr',
    '.arw','.srf','.sr2',
    '.bay',
    '.crw','.cr2',
    '.cap','.tif','.iiq','.eip',
    '.dcs','.dcr','.drf','.k25','.kdc','.tif',
    '.dng',
    '.erf',
    '.fff',
    '.mef',
    '.mos',
    '.mrw',
    '.nef','.nrw',
    '.orf',
    '.ptx','.pef',
    '.pxn',
    '.r3d',
    '.raf',
    '.raw','.rw2',
    '.raw','.rwl','.dng'
    '.rwz',
    '.x3f',
    '.tiff',
    ]
vidExt=['avi','mpg','mp4','mts','mov']
allExt=['*']    #run this after others - for moving all !jpg out
#file types / image work / whatever
#
#   name    loc     image   resize  crop    redim       crdim
#   800     0800    yes     yes     no      800x800     x
#   1080    1080    yes     yes     yes     2000x2000   1920x1080
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   
#
#   name    loc     image   ext
#   raw     raw     no      rawExt
#   video   vid     no      vidExt
#   misc    misc    no      allExt

#image => !dircheck
outputConfig=[]
#outputConfig.append({'name':'400','loc':'0400','image':True,
#   'resize':True,'crop':False,'resizedims':'400x400'})
outputConfig.append({'name':'800','loc':'0800','image':True,
    'resize':True,'crop':False,'resizedims':'800x800'})
#outputConfig.append({'name':'1080','loc':'1080','image':True,
#   'resize':True,'crop':True,'resizedims':'2000x2000','cropdims':'1920x1080'})
#outputConfig.append({'name':'1200','loc':'1200','image':True,
#   'resize':True,'crop':False,'resizedims':'1200x1200'})
outputConfig.append({'name':'img','loc':None,'image':False,'ext':imgExt})
outputConfig.append({'name':'raw','loc':'raw','image':False,'ext':rawExt})
outputConfig.append({'name':'video','loc':'vid','image':False,'ext':vidExt})
outputConfig.append({'name':'misc','loc':'misc','image':False,'ext':allExt})
#TODO: Set the default log format to something quieter:
#Levels:
#55 no output
#50
#45
#40
#35
#30 one line after finish
#25 summmary
#20 default:
#       start messages
#       maybe other stuff, but one line per output size:
#       0800: 10%...20%...30%...40%...50%...60%...70%...80%...90%...done
#       stop messages, summary
#15 start messages, stop messages, summmary
#10 start messages, per image line, stop messages, summmary
#05 start messages, per image messages, stop messages, summmary
#   
def shutdown_logging():
        logging.shutdown()

def setup_logging(cmd_opts=dict()):
    #ref: http://onlamp.com/pub/a/python/2005/06/02/logging.html
    #ref: http://docs.python.org/library/logging.html
    logger = logging.getLogger("stdout")
    logger.setLevel(logging.DEBUG)

    #create console handler (C H) and set level to debug
    ch = logging.StreamHandler()
    # +5 per '-q', -5 per '-v'
    verb_level = 0
    if "verbosity" in cmd_opts and "unverbosity" in cmd_opts:
        verb_level = cmd_opts["unverbosity"] + cmd_opts["verbosity"]
    ch.setLevel(logging.INFO+5*( verb_level ))

    #create formatter
    #Use one formatter if loglevel is below INFO, another if >=INFO
    if 0 < verb_level:
        formatter = logging.Formatter("%(message)s")
    else:
        formatter = \
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s",
            '%Y-%m-%d %H:%M:%S')
    #add formatter to ch 
    ch.setFormatter(formatter)
    #add ch to logger
    logger.addHandler(ch)

    #Add names for half levels
    #ref: http://docs.python.org/library/logging.html
    logging.addLevelName(15, 'halfDEBUG')
    logging.addLevelName(25, 'halfINFO')
    logging.addLevelName(35, 'halfWARNING')
    logging.addLevelName(45, 'halfERROR')
    logging.addLevelName(55, 'halfCRITICAL')

    return logger

def prep_base_dir( log, dir, cmd_opts=dict()):
    #print some info about imagedir
    log.info('dir:'+str(cmd_opts["imagedir"])+' aka '+str(os.path.abspath(cmd_opts["imagedir"])))

    #check for 'jpg' subdirectory - this is where all the input files are, 
    #  so it is a big problem if it is absent
    if not os.path.isdir(dir):
        log.error('missing subdirectory ("jpg") with images')
        sys.exit(-1)

def generate_file_lists(log, basedir):
    """
    generate multiple lists of files on which to then work

    TODO: this should be fixed up with everything else someday
    """
    for outConf in outputConfig:
        if "img" == outConf["name"]:
            patStr = "$|".join(outConf["ext"])+"$"
            img_pat = re.compile(patStr, re.I)
        if "raw" == outConf["name"]:
            patStr = "$|".join(outConf["ext"])+"$"
            raw_pat = re.compile(patStr, re.I)
        if "video" == outConf["name"]:
            patStr = "$|".join(outConf["ext"])+"$"
            vid_pat = re.compile(patStr, re.I)
    jpglist = []
    rawlist = []
    vidlist = []
    otherlist = []
    proc_lists = {"img":[],"raw":[],"vid":[],"misc":[]}
    for root, dirs, files in os.walk(basedir):
        for walked_file in files:
            file_path = os.path.join(root,walked_file)
            #print file_path
            if img_pat.search(file_path):
                jpglist.append(file_path)
                proc_lists["img"].append(file_path)
            elif raw_pat.search(file_path):
                rawlist.append(file_path)
                proc_lists["raw"].append(file_path)
            elif vid_pat.search(file_path):
                vidlist.append(file_path)
                proc_lists["vid"].append(file_path)
            else:
                otherlist.append(file_path)
                proc_lists["misc"].append(file_path)
    #for pl in proc_lists: print pl, proc_lists[pl]
    #return(alllist,jpglist,otherlist) #OLD RETURN
    return(proc_lists)

def _WIP_generate_file_lists(log,basedir):
    contents = os.listdir(basedir)
    source_dirs = []
    source_dirs2 = []
    for pattern in source_dir_list:
        pat = re.compile(pattern)
        for entry in contents:
            entry_path = os.path.join(basedir,entry)
            if os.path.isdir(entry_path) and pat.match(entry):
                source_dirs.append(entry_path)
                source_dirs2.append(entry)
    dir_contents = []
    for source_dir in source_dirs:
        entries = os.listdir(source_dir)
        for entry in entries:
            entry_path = os.path.join(source_dir,entry)
            if os.path.isfile(entry_path):
                dir_contents.append(entry_path)
    all_list = dir_contents
    jpg_list = []
    other_list = []
    for file_path in all_list:
        if re.match('.*.jpg',file_path,re.I):
            jpg_list.append(file_path)
        else:
            other_list.append(file_path)
    dir_info = {}
    dir_info["paths"] = {"base":basedir,"sources":source_dirs,
            "files":dir_contents}
    dir_info["lists"] = {"all":all_list,"jpg":jpg_list,"other":other_list}
    #dir_info[""] = 
    return dir_info
    return(all_list,jpg_list,other_list)

def handle_non_jpg(log,basedir):
    """
    Move non-jpg files
    
    old style, <base>/jpg:
    * move raw (CR2) to <base>/raw
    * move vid (MOV) to <base>/vid
    * move other (non-jpg) files to <base>/misc

    new style, <base>/raw-media (maybe also media-raw later on)
    * move nothing
    * maybe remove macos added files (.DS_Store, .Trashes, ...)
    """
    #indir = os.path.join(basedir,'jpg')
    #create lists of jpg and other files
    #(alllist,jpglist,otherlist) = generate_file_lists(log,basedir)
    proc_lists = generate_file_lists(log, basedir)
    log.info("trace: handle_non_jpg enter")
    log.warn("NOTE: hardcoding configuration; TODO: rework config framework")
    pathStyle_old = re.compile("^[^A-Za-z0-9]*jpg", re.I)
    pathStyle_new = re.compile("^[^A-Za-z0-9]*raw-media", re.I)
    outdirs = "({})".format(")|(".join(["vid-sm", "0800", "raw",
        "misc", "work"]))
    pathStyle_output = re.compile("^[^A-Za-z0-9]*%s"%outdirs, re.I)
    keys_names = [  #this is a kluge to map sorting methods
        ( "raw","raw"),
        ( "vid","video"),
        ( "misc","misc"),
        ]
    log.info("TODO: unify processing, esp vid/img")
    for key, name in keys_names:
        #= {"img":[],"raw":[],"vid":[],"misc":[]}
        if "img" == key: continue
        for path in proc_lists[key]:
            if pathStyle_new.search(path) or pathStyle_output.search(path):
                #log.info("new style proc: %s"%path)
                continue
            else:
                #log.info("OLD style proc: %s"%path)
                pass
            # "lookup" for named output config
            for filetype in outputConfig:
                if filetype["image"]: continue  #image processing, deal later
                if name == filetype["name"]:
                    print "moving?!?", path
                    config = filetype
                    outdir = os.path.join(basedir, config["loc"])
                    infile = os.path.join(basedir, path)
                    outfile = os.path.join(outdir, os.path.basename(path))
                    if not os.path.exists(infile):
                        log.warn("missing: %s"%path)
                        continue
                    if not os.path.exists(outdir):
                        log.warn("creating: %s"%outdir)
                        os.mkdir(outdir)
                    #log.info("not moving:\n\t\t%s\n\t\t%s"%(infile,outfile))
                    os.rename(infile,outfile)
    log.info("trace: handle_non_jpg exit")
    return

def placeholder():
    for filetype in outputConfig:
        if filetype['image'] is False:
            for ext in filetype['ext']:
                for file in otherlist:
                    if re.match('.*.'+ext,file,re.I):
                        outdir = os.path.join(basedir,filetype['loc'])
                        infile=os.path.join(indir,file)
                        outfile=os.path.join(outdir,file)
                        if not os.path.exists(infile):  continue
                        if not os.path.exists(outdir):  os.mkdir(outdir)
                        os.rename(infile,outfile)

def convert_jpg(log, basedir, cmd_opts=dict()):
    """
    resize/crop images
    
    run convert/gm convert on jpg files
    also, consider ffmpeg for video files
    maybe use config to set raw conversion (thumbnailing?)
    """
    log.info("trace: convert_jpg enter")
    log.warn("NOTE: hardcoding configuration; TODO: rework config framework")
    proc_lists = generate_file_lists(log, basedir)
    pathStyle_old = re.compile("^[^A-Za-z0-9]*jpg", re.I)
    pathStyle_new = re.compile("^[^A-Za-z0-9]*raw-media", re.I)
    keys_names = [  #this is a kluge to map sorting methods
        ( "raw","raw"),
        ( "vid","video"),
        ( "misc","misc"),
        ]
    for img_file in proc_lists["img"]:
        for filetype in outputConfig:
            if filetype["image"]:
                outdir = os.path.join(basedir,filetype['loc'])
                if not os.path.exists(outdir):  os.mkdir(outdir)
                outfile = os.path.join(outdir, os.path.basename(img_file))
                infile = img_file
                if os.path.exists(outfile):
                    log.warn("skipping existant file: %s"%outfile)
                        #filetype['name']+'/'+str(file)+' exists, skipping')
                    continue
                shutil.copy2(infile,outfile)
                subprocess.call(["gm", "mogrify", "-quality", "50",
                    "-resize", filetype["resizedims"], outfile])
                if filetype['crop']:
                    subprocess.call(['gm', 'mogrify', '-gravity center',
                        '-extent', filetype['cropdims'], outfile])
                log.info("proccessed %s"%outfile)
    for filetype in outputConfig:
        if "video" == filetype["name"]:
            for vid_file in proc_lists["vid"]:
                log.warn("TODO: integrate hardcoded config into framework")
                outdir = os.path.join(basedir,'vid-sm')
                if not os.path.exists(outdir):  os.mkdir(outdir)
                log.warn("Hardcoding raw-media directory name here")
                sha = hashlib.sha256()
                sha.update(vid_file)
                sub_hash = sha.hexdigest()[0:6]
                med_strip = vid_file.split("raw-media")[1][1:]
                vid_card_date = med_strip[0:11]
                #print vid_file
                #print "hash", sub_hash
                #print "date", vid_card_date
                infile = vid_file
                out_pre= vid_card_date
                outbase = os.path.splitext( os.path.basename(vid_file) )[0]
                out_ext = "webm"
                outname = "{}_{}.{}".format(out_pre, outbase, out_ext)
                outfile = os.path.join(outdir, outname)
                print infile
                print outfile
                print os.path.exists(outfile)
                if os.path.exists(outfile):
                    log.warn("skipping existant file: %s"%outfile)
                    continue
                #print "\n>>>>>SKIP FFMPEG CALL FOR NOW<<<<<\n"
                #continue
                log.warn("TODO: autoscale to keep aspect ratio w/ ffmpeg")
                subprocess.call(["ffmpeg", "-i", infile, "-vf",
                    "scale=640:360", outfile])
                print vid_file
                print filetype


    #time for i in [0FMP]*[IVS];
    #    do out=`echo $i | sed -Ee 's/(MTS)|(AVI)|(MOV)/webm/'`;
    #    ffmpeg -i $i -vf scale=640:360 ${out} ;
    #    done &&
    #rm opsnr.stt &&
    #mkdir ../vid-sm && mv *webm ../vid-sm/ && cd ../vid-sm/ && echo '<!DOCTYPE html> <html> <head> <title> video </title> </head> <body>' > _vid-sm.html &&
    #for i in *webm ;
    #    do echo '<video controls> <source src="'$i'"> '$i' </video> <br>' ;
    #    done >> _vid-sm.html &&
    #echo '</body> </html>' >> _vid-sm.html'

    log.info("TODO: unify processing, esp vid/img")
    log.info("trace: convert_jpg exit")
    return

def old_convert_jpg(log, basedir):
    indir = os.path.join(basedir,'jpg')
    #create lists of jpg and other files
    (alllist,jpglist,otherlist) = generate_file_lists(log,basedir)

    #Only print the progress meter output at the default level
    prog_flag=options.unverbosity==options.verbosity

    for filetype in outputConfig:
        if filetype['image'] is True:
            outdir = os.path.join(basedir,filetype['loc'])
            if not os.path.exists(outdir):  os.mkdir(outdir)
            #use prog_flag (verbosity stuff) with print because logging
            #  can't put multiple messages/strings on a line
            if prog_flag:
                print filetype['name'].rjust(5)+': ',
                sys.stdout.flush()
            prev_portion=10 #initialize here to avoid whining
            for index, file in enumerate(jpglist):
                if prog_flag:
                    portion=((100.0*index)/len(jpglist))
                    if portion>prev_portion:
                        sys.stdout.write('%02d...'%(prev_portion))
                        sys.stdout.flush()
                        prev_portion+=10
                else: pass
                log.log(15,filetype['name']+'/'+str(file))
                infile=os.path.join(indir,file)
                outfile=os.path.join(outdir,file)
                if os.path.exists(outfile):
                    log.log(15,filetype['name']+'/'+str(file)+' exists, skipping')
                    continue
                #copy file to output location and then use mogrify on it
                shutil.copy2(infile,outfile)
                if not filetype['crop']:    
                    #TODO: abstract image work
                    #subprocess.call([img_mod, '-resize', 
                    subprocess.call(['gm', 'mogrify', '-resize', 
                        filetype['resizedims'], outfile])
                else:
                    #subprocess.call([img_mod, '-resize', 
                    subprocess.call(['gm', 'mogrify', '-resize', 
                        filetype['resizedims']+'^', outfile])
                    #subprocess.Popen(img_mod+' -gravity center -extent '
                    subprocess.call(['gm', 'mogrify', 
                        '-gravity center', '-extent',
                        filetype['cropdims'],
                        outfile])
            if prog_flag: 
                print 'done\n',

def parse_command_line():
    """
    New style / updated parameter extraction

    This should be a simple upgrade from optparse to argparse
    """
    parser = argparse.ArgumentParser(description='Process media')
    #parser.add_argument('-v', '--verbose')
    parser.add_argument('-v', '--verbose', action='count', dest='verbosity',default=0, help='verbose output')
    parser.add_argument('-q', '--quiet', action='count', dest='unverbosity',default=0, help='quiet output')
    parser.add_argument('-i', '--imagedir', action='store', default='.', help='directory containing images, examples: <dir>/jpg/<images>; <dir>/<raw-media>/*/DCIM/<addl_dir>/<images>', dest='imagedir')
    return vars(parser.parse_args())

def main ():

    options = parse_command_line()
    print "early return"
    # use a dict for the summary info.
    # fix to be a class, so self.summary_info works...
    summary_info = {}
    #add: directory
    #start,prep_start,conv_start,stop times
    #directories created
    #files:
    #   moved
    #   converted
    #   skipped

    #note the time for summary
    time_start = time.time()

    log=setup_logging()
    log.info('Image Processing!')
    
    #it would be nice to be able to run on multiple directories, glob
    basedir=options['imagedir']

    #note the time for summary
    time_start_prep = time.time()

    #directory setup and related work
    prep_base_dir(log, basedir, cmd_opts=options)
    handle_non_jpg(log, basedir)

    #note the time for summary
    time_start_conv = time.time()

    #image conversion
    convert_jpg(log,basedir)

    #note the time for summary
    time_stop_conv = time.time()

    time_conv = time_stop_conv-time_start_conv 
    time_prep = time_start_conv-time_start_prep

    log.info("summary:")
    ##files, non-image, image, converted
    log.info("\tprep time:\t"+str(time_prep))
    log.info("\twork time:\t"+str(time_conv))

    shutdown_logging()

if __name__ == '__main__':
    try:
        #start_time = time.time()
        parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'], version='$Id$')
        #parser.add_option ('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_option ('-v', '--verbose', action='count', dest='verbosity',default=0, help='verbose output')
        parser.add_option ('-q', '--quiet', action='count', dest='unverbosity',default=0, help='quiet output')
        parser.add_option ('-i', '--imagedir', action='store', default='.', help='directory containing images, examples: <dir>/jpg/<images>; <dir>/<raw-media>/*/DCIM/<addl_dir>/<images>', dest='imagedir')
        #parser.add_option ('-i', '--imagedir', action='store', default='.', help='directory containing images, examples:\n<dir>,\n<dir>', dest='imagedir')
        #(options, args) = parser.parse_args()
        main()
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)
