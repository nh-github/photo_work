#! /usr/bin/env python
"""
SYNOPSIS
    Small media ingest/prep program

    run on directory containing media (in raw-media or in jpg)

AUTHOR
    Noah Hafner <nmh+misc2013@nomh.org>
    ref:    http://code.activestate.com/recipes/528877/ (Noah Spurrier)

LICENSE
    This program is available under the Apache Artistic license
    Copyright Noah Hafner 2010-2013

VERSION
    2
"""
#refs:
#* http://www.pha.com.au/kb/index.php/Python_Skeleton_Scripts
#* http://stackoverflow.com/questions/2387272/\
#        what-is-the-best-python-library-module-skeleton-code
#* https://github.com/ctb/SomePackage
#* http://pypi.python.org/pypi/skeleton/0.4

import argparse
import glob
import hashlib
import logging
import os
import re
import shutil
import subprocess
import sys
#import time
import traceback


class config_state(object):
    """
    handle configuration details

    provide configuration for processing:
    * defaults
    * load from file / disk
    * command line parameters

        Provide a [hopefully] coherent configuration

        Sources:
            1) built in configuration settings
            2) config file(s)
            3) parse command line parameters

        Config:
            * input
              + directory path(s)
            * output
              + location
              + transform parameters
                @ resolution
                @ cropping
                @ timing (metadata)
                @ watermarking?
                @ metadata redaction
            * tools
              + still image tool (graphics magick)
              + motion image tool (ffmpeg)
              + metadata (exiftool)
              + ???
    """
    def __init__(self, **kwargs):
        self.set_internal_defaults()

    def set_internal_defaults(self, **kwargs):
        self.set_util_default()
        self.set_directories_default()
        self.set_extensions_default()
        self.set_job_spec_default()

    def set_util_default(self, **kwargs):
        self.img_mod = "gm mogrify"
        self.img_exif = "exiftool"
        self.vid_tool = "ffmpeg"

    def set_directories_default(self, **kwargs):
        """
        where to find input media
        """
        self.dir_conf = dict()
        self.dir_conf["base"] = "."
        self.dir_conf["source_patterns"] = [
            "jpg",
            "DCIM/.*$",
            "[0-9]*_PANA$",  # ???
            "raw-media/*_-card/",  # glob, not regexp
        ]
        self.dir_conf["im_sources"] = None
        self.dir_conf["im_out"] = "img"
        self.dir_conf["vid_out"] = "vid"

    def set_extensions_default(self, **kwargs):
        """
        what to use for sorting files

        maybe using file magic would be preferable, but less portable
        """
        # ref  http://en.wikipedia.org/wiki/JPEG
        self.imgExt = [
            "jpg",
            "jpeg",
            "jpe",
            "jif",
            "jfif",
            "jfi",
        ]

        # ref:   http://en.wikipedia.org/wiki/Raw_image_format
        self.rawExt = [
            '.3fr',
            '.arw', '.srf', '.sr2',
            '.bay',
            '.crw', '.cr2',
            '.cap', '.tif', '.iiq', '.eip',
            '.dcs', '.dcr', '.drf', '.k25', '.kdc', '.tif',
            '.dng',
            '.erf',
            '.fff',
            '.mef',
            '.mos',
            '.mrw',
            '.nef', '.nrw',
            '.orf',
            '.ptx', '.pef',
            '.pxn',
            '.r3d',
            '.raf',
            '.raw', '.rw2',
            '.raw', '.rwl', '.dng'
            '.rwz',
            '.x3f',
            '.tiff',
        ]
        self.vidExt = ['avi', 'mpg', 'mp4', 'mts', 'mov']

        #this is a catch-all for moving files out of the input location
        #may be obsolete with the new style of leave the input images
        #in place and provide easier access to converted copies
        self.allExt = ['*']

    def set_job_spec_default(self, **kwargs):
        """
        spec labels (keys) shall be lowercase
        """
        self.output_config = dict()
        self.output_config["default"] = {
            'name': '800', 'loc': '0800', "type": "im",
            'image': True, 'resize': True, 'crop': False,
            'resizedims': '800x800'}
        #outputConfig.append({'name':'1080','loc':'1080',"type":"im",
        #   'resize':True,'crop':True,'resizedims':'2000x2000',
        #   'cropdims':'1920x1080'})
        #outputConfig.append({'name':'vid_thumbs','loc':'th_vid',"type":"vid",
        #   'resize':True,'crop':False,'resizedims':'640x360'})
        #outputConfig.append({'name':'img','loc':None,'image':False,
        #    'ext':imgExt})
        #outputConfig.append({'name':'raw','loc':'raw','image':False,
        #    'ext':rawExt})
        #outputConfig.append({'name':'video','loc':'vid','image':False,
        #    'ext':vidExt})
        #outputConfig.append({'name':'misc','loc':'misc','image':False,
        #    'ext':allExt})

    def update_dirs(self, **kwargs):
        """
        update dir settings, no additions
        """
        keys = self.dir_conf.keys()
        for k in kwargs:
            if not k in keys:
                raise ValueError("bad keyname for dir: {}".format(k))
        self.dir_conf.update(kwargs)

    def get_dirs(self, **kwargs):
        """
        provide configured directories or subset

        return full dict with no args
        return a list of dirs based on kwargs
        """
        if kwargs:
            selected = []
            for k in kwargs:
                if not k in self.dir_conf:
                    raise ValueError("bad keyname for dir: {}".format(k))
            selected.append(self.dir_conf[k])
            return selected
        else:
            return self.dir_conf.copy()

    def get_dir(self, dir):
        """
        get just one dir
        """
        return self.dir_conf[dir]

    def get_job_specs(self, **kwargs):
        """
        provide list of configured job specifications or subset

        no args -> full dict
        iterable "spec_list" -> listed specs
        """
        log = logging.getLogger("base")
        try:
            return [self.output_config[s]
                    for s in kwargs.get("spec_list")]
            #use above rather than below to raise an error when
            #   an invalid spec is provided in the input list
            #  the below just returns None
            #return [self.output_config.get(s)
            #        for s in kwargs.get("spec_list")]
        except Exception, e:
            log.info("exception path")
            if 0 == len(kwargs):
                return self.output_config.copy()
            raise
            print "Problem"
            print e
            print type(kwargs)
            sys.exit(-1)
            #raise ValueError("bad keyname for dir: {}".format(k))

    def get_job_spec(self, spec_name="Default"):
        """
        get just one dir
        """
        return self.output_config[spec_name.lower()]


class foo(object):
    def __init__(self, **kwargs):
        pass

    def setup(self):
        """
        setup infrastructure

        Stuffs:
            * Start logging
            * determine configuration
              1) built in configuration settings
              2) config file(s)
              3) parse command line parameters
        """
        self.setup_logging()
        parsed_args = self.cmd_param()
        self.setup_config(parsed_args)

    def setup_logging(self):
        """
        Start logging, determine configuration

        Start base level of logging
        """
        log = logging.getLogger("base")
        #logging.basicConfig(format="%(levelname)s %(funcName)s"+
        #                    " %(message)s")

        #fmt = ("%(levelname)-7s %(asctime)s, "
        fmt = ("%(lineno)s:%(funcName)s  %(levelname)-7s %(message)s")
        logging.basicConfig(format=fmt, datefmt='%H:%M:%S')
        log.setLevel(1)
        log.debug("check")
        log.info("check")

        trace_log = logging.getLogger("trace")
        trace_log.setLevel(20)
        trace_log.info("exit")
        return

    def cmd_param(self):
        """
        parse command line parameters
        -i    image directory(s)
        -prep create/move/rearrange directory(s)
        ...and more
        """
        trace_log = logging.getLogger("trace")
        trace_log.info("enter")
        parser = argparse.ArgumentParser(
            description='Small media ingest/prep program',
            add_help=True,)
        parser.add_argument(
            '-V', '-version', '--version',
            action='version', version='%(prog)s 2.0')

        parser.add_argument(
            '-i', '--imagedir', action='store', default='.',
            help="base directory [for dated set] containing images",
            #", examples: <dir>/jpg/<images>; "
            #"<dir>/<raw-media>/*-card/**/<images>",
            dest='imagedir')
        parser.add_argument(
            '-p', '--prep', action='store_true',
            help='create empty directory structure for new set')
        parser.add_argument(
            '-c', '--convert', action='store_true',
            help='convert input media and create small previews')
        parser.add_argument(
            '-s', '--settings-file', action='store_true',
            help='file from which to load settings')

        parser.add_argument(
            '-n', '--dry-run', action='store_true',
            help="don't change any files")
        parser.add_argument(
            '-d', '--debug', action='count', default=0,
            help='more verbose debugging output')
        parser.add_argument(
            '--log', default=sys.stdout, type=argparse.FileType('w'),
            help='destination for log messages')
        parser.add_argument(
            '-v', '--verbose', action='count', default=0,
            help='more verbose output')
        args = parser.parse_args()

        trace_log.info("exit")
        return args

    def setup_config(self, args):
        """
        turn on config stuff
        """
        trace_log = logging.getLogger("trace")
        trace_log.info("enter")

        self.conf = config_state()
        self.conf.update_dirs()
        self.conf.update_dirs(base=args.imagedir)
        base = self.conf.get_dir("base")
        pats = self.conf.get_dir("source_patterns")
        in_dirs = []
        for pat in pats:
            for in_dir in glob.glob(os.path.join(base, pat)):
                if os.path.exists(in_dir):
                    in_dirs.append(in_dir)
        self.conf.update_dirs(im_sources=in_dirs)

    def conv_img(self, jobID=None):
        """
        load details from config

        #TODO: multiple job spec (specify as parameter?)
        or is this a preconv source file lister?
        """
        trace_log = logging.getLogger("trace")
        trace_log.info("enter")
        trace_log.info("exit")
        return

    def list_input_files(self, job_spec=None):
        """
        load details from config

        #TODO: multiple job spec (specify as parameter?)
        or is this a preconv source file lister?
        """
        trace_log = logging.getLogger("trace")
        trace_log.info("enter")
        log = logging.getLogger("base")
        src_paths = []
        for in_dir in self.conf.get_dir("im_sources"):
            for root, dirs, files in os.walk(in_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    if self.check_file_type(foo, file_path):
                        src_paths.append(file_path)
        log.warn("prints to follow")
        print ("listed {} files; starting with: \n  {}"
               "".format(len(src_paths), src_paths[0]))
        trace_log.error("early return")
        return

        base_dir = "."
        in_media = "raw-media"
        in_dir = os.path.join(base_dir, in_media)
        out_dir = os.path.join(base_dir, "preview")
        out_dir = out_dir
        image_paths = []
        for root, dirs, files in os.walk(in_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if self.check_file_type(foo, file_path):
                    image_paths.append(os.path.join(root, file_name))
                #ext = os.path.splitext(file_name.lower())[-1][1:]
                #if "jpg" == ext:

        print "file extensions"
        "jpg"
        #image_tool = "gm convert"
        #image_params = "-resize", "600x600"
        #image_output = "preview"
        trace_log.info("exit")
        pass

    def check_file_type(self, ft, file_path):
        """
        check if path is of type or not

        examples:
        * cft(config_img, "example/image.jpg") -> True
        * cft(config_img, "example/foo.txt") -> False
        """
        trace_log = logging.getLogger("trace")
        trace_log.info("enter")
        trace_log.info("exit")
        return False

    def prep(self):
        """
        generate directory structure for new media
        """
        trace_log = logging.getLogger("trace")
        trace_log.info("enter")
        trace_log.info("exit")
        pass

    def preconv(self):
        """
        gather sets of files for processing

        list of files w/ each entry noting:
            file path,
            name,
            output path,
            :cc

        """
        trace_log = logging.getLogger("trace")
        trace_log.info("enter")

        self.list_input_files(job_spec=self.conf.get_job_spec())

        trace_log.info("exit")
        pass

    def conv(self):
        """
        gather sets of files for processing

        list of files w/ each entry noting:
            file path,
            name,
            output path,
            :cc

        """
        trace_log = logging.getLogger("trace")
        trace_log.info("enter")
        log = logging.getLogger("base")

        self.preconv()
        log.info("skip image conversion")
        #self.conv_img()
        log.info("skip video conversion")
        #self.conv_vid()

        trace_log.info("exit")
        pass

    def clean():
        trace_log = logging.getLogger("trace")
        trace_log.info("enter")
        trace_log.info("exit")
        pass


def main():
    #prep a dir
    #-> <base_dir>/raw-media/<datecode>-card/???
    #copy card (by hand)
    #convert media
    #options:
    # -v - more info
    # -d - debug ???
    # -n - don't alter filesystem
    # -p - prep a dir
    # -c - convert media

    conv_obj = foo()
    conv_obj.setup()  # parse parameters, config, log
    #conv_obj.prep()  # create file list(s) check directory access
    conv_obj.conv()  # convert inputs w/out convertions
    #conv_obj.clean()  # remove temp files?


if __name__ == '__main__' or __name__ == sys.argv[0]:
    try:
        sys.exit(main())
    except KeyboardInterrupt, e:
        print "break, %s" % str(e)
    except SystemExit, e:  # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)


#
#
#
#
#
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
    ch.setLevel(logging.INFO + 5 * (verb_level))

    #create formatter
    #Use one formatter if loglevel is below INFO, another if >=INFO
    if 0 < verb_level:
        formatter = logging.Formatter("%(message)s")
    else:
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        formatter = \
            logging.Formatter(fmt, '%Y-%m-%d %H:%M:%S')
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


def prep_base_dir(log, dir, cmd_opts=dict()):
    #print some info about imagedir
    msg_bits = ['dir:',
                str(cmd_opts["imagedir"]),
                ' aka ',
                str(os.path.abspath(cmd_opts["imagedir"]))]
    log.info(msg_bits)

    #check for 'jpg' subdirectory - this is where all the input files are,
    #  so it is a big problem if it is absent
    if not os.path.isdir(dir):
        log.error('missing subdirectory ("jpg") with images')
        sys.exit(-1)


def _WIP_generate_file_lists(log, basedir):
    """
    glob patterns

    take basedir
    load config (or what?)
    """
    contents = os.listdir(basedir)
    source_dirs = []
    source_dirs2 = []
    for pattern in source_dirs:
        pat = re.compile(pattern)
        for entry in contents:
            entry_path = os.path.join(basedir, entry)
            if os.path.isdir(entry_path) and pat.match(entry):
                source_dirs.append(entry_path)
                source_dirs2.append(entry)
    dir_contents = []
    for source_dir in source_dirs:
        entries = os.listdir(source_dir)
        for entry in entries:
            entry_path = os.path.join(source_dir, entry)
            if os.path.isfile(entry_path):
                dir_contents.append(entry_path)
    all_list = dir_contents
    jpg_list = []
    other_list = []
    for file_path in all_list:
        if re.match('.*.jpg', file_path, re.I):
            jpg_list.append(file_path)
        else:
            other_list.append(file_path)
    dir_info = {}
    dir_info["paths"] = {"base": basedir,
                         "sources": source_dirs,
                         "files": dir_contents}
    dir_info["lists"] = {"all": all_list,
                         "jpg": jpg_list,
                         "other": other_list}
    #dir_info[""] =
    return dir_info
    return(all_list, jpg_list, other_list)


def handle_non_jpg(log, basedir):
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
    #proc_lists = generate_file_lists(log, basedir)
    proc_lists = None
    log.info("trace: handle_non_jpg enter")
    log.warn("NOTE: hardcoding configuration; TODO: rework config framework")
    #pathStyle_old = re.compile("^[^A-Za-z0-9]*jpg", re.I)
    pathStyle_new = re.compile("^[^A-Za-z0-9]*raw-media", re.I)
    outdirs = "({})".format(")|(".join(["vid-sm", "0800", "raw",
                                        "misc", "work"]))
    pathStyle_output = re.compile("^[^A-Za-z0-9]*%s" % outdirs, re.I)
    keys_names = [  # this is a kluge to map sorting methods
        ("raw", "raw"),
        ("vid", "video"),
        ("misc", "misc"),
    ]
    log.info("TODO: unify processing, esp vid/img")
    for key, name in keys_names:
        #= {"img":[],"raw":[],"vid":[],"misc":[]}
        if "img" == key:
            continue
        for path in proc_lists[key]:
            if pathStyle_new.search(path) or pathStyle_output.search(path):
                #log.info("new style proc: %s"%path)
                continue
            else:
                #log.info("OLD style proc: %s"%path)
                pass
            # "lookup" for named output config
            outputConfig = []
            for filetype in outputConfig:
                if filetype["image"]:
                    continue  # image processing, deal later
                if name == filetype["name"]:
                    print "moving?!?", path
                    config = filetype
                    outdir = os.path.join(basedir, config["loc"])
                    infile = os.path.join(basedir, path)
                    outfile = os.path.join(outdir, os.path.basename(path))
                    if not os.path.exists(infile):
                        log.warn("missing: %s" % path)
                        continue
                    if not os.path.exists(outdir):
                        log.warn("creating: %s" % outdir)
                        os.mkdir(outdir)
                    #log.info("not moving:\n\t\t%s\n\t\t%s"%(infile,outfile))
                    os.rename(infile, outfile)
    log.info("trace: handle_non_jpg exit")
    return


def placeholder():
    outputConfig = []
    otherlist = []
    basedir = ""
    indir = ""
    for filetype in outputConfig:
        if filetype['image'] is False:
            for ext in filetype['ext']:
                for file in otherlist:
                    if re.match('.*.' + ext, file, re.I):
                        outdir = os.path.join(basedir, filetype['loc'])
                        infile = os.path.join(indir, file)
                        outfile = os.path.join(outdir, file)
                        if not os.path.exists(infile):
                            continue
                        if not os.path.exists(outdir):
                            os.mkdir(outdir)
                        os.rename(infile, outfile)


def convert_jpg(log, basedir, cmd_opts=dict()):
    """
    resize/crop images

    run convert/gm convert on jpg files
    also, consider ffmpeg for video files
    maybe use config to set raw conversion (thumbnailing?)
    """
    log.info("trace: convert_jpg enter")
    log.warn("NOTE: hardcoding configuration; TODO: rework config framework")
    #proc_lists = generate_file_lists(log, basedir)
    proc_lists = []
    pathStyle_old = re.compile("^[^A-Za-z0-9]*jpg", re.I)
    pathStyle_new = re.compile("^[^A-Za-z0-9]*raw-media", re.I)
    keys_names = [  # this is a kluge to map sorting methods
        ("raw", "raw"),
        ("vid", "video"),
        ("misc", "misc"),
    ]
    foo = (pathStyle_old, pathStyle_new, keys_names)
    foo = foo
    outputConfig = []
    for img_file in proc_lists["img"]:
        for filetype in outputConfig:
            if filetype["image"]:
                outdir = os.path.join(basedir, filetype['loc'])
                if not os.path.exists(outdir):
                    os.mkdir(outdir)
                outfile = os.path.join(outdir, os.path.basename(img_file))
                infile = img_file
                if os.path.exists(outfile):
                    log.warn("skipping existant file: %s" % outfile)
                        #filetype['name']+'/'+str(file)+' exists, skipping')
                    continue
                shutil.copy2(infile, outfile)
                subprocess.call(["gm", "mogrify", "-quality", "50",
                                 "-resize", filetype["resizedims"], outfile])
                if filetype['crop']:
                    subprocess.call(['gm', 'mogrify', '-gravity center',
                                     '-extent', filetype['cropdims'], outfile])
                log.info("proccessed %s" % outfile)
    for filetype in outputConfig:
        if "video" == filetype["name"]:
            for vid_file in proc_lists["vid"]:
                log.warn("TODO: integrate hardcoded config into framework")
                outdir = os.path.join(basedir, 'vid-sm')
                if not os.path.exists(outdir):
                    os.mkdir(outdir)
                log.warn("Hardcoding raw-media directory name here")
                sha = hashlib.sha256()
                sha.update(vid_file)
                sub_hash = sha.hexdigest()[0:6]
                med_strip = vid_file.split("raw-media")[1][1:]
                vid_card_date = med_strip[0:11]
                print vid_file
                print "hash", sub_hash
                print "date", vid_card_date
                infile = vid_file
                out_pre = vid_card_date
                outbase = os.path.splitext(os.path.basename(vid_file))[0]
                out_ext = "webm"
                outname = "{}_{}.{}".format(out_pre, outbase, out_ext)
                outfile = os.path.join(outdir, outname)
                print infile
                print outfile
                print os.path.exists(outfile)
                if os.path.exists(outfile):
                    log.warn("skipping existant file: %s" % outfile)
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
    log.info("TODO: unify processing, esp vid/img")
    log.info("trace: convert_jpg exit")
    return
