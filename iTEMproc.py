#!/usr/bin/python

# TODO: The handling of node names in the input is limited to names starting with 'lmig'.
# This is awkward and should be fixed.

# iTEMproc.py Release 1.1
# Support node list from file rather than querying SGE using qconf command

import sys
import getopt
import subprocess 
import getpass

def usage():
    Usage = """Usage:  iTEMproc.py  [-a|--allproc] [-h|--help] [[-p|--procfile=]|[-n|--nodefile] filename]
               [-l|--list] [[-u|--user=] username] [-v|--version]
                 options:
                    -a|--allproc                    list all iTEM processes for any user. This ignores
                                                    the option -u. This option will not attempt to kill any
                                                    processes (implies option -l|--list).
                    -h|--help                       print this usage
                    -p|--procfile= filename         provide list of node/processes in file with filename
                    -n|--nodefile= filename         provide list of nodes in file with name filename
                    -l|--list                       list the nodes and your iTEM processes
                                                    but don't remove them
                    -u|--user= username             look for iTEM processes owned by username
                    -v|--version                    print version information
                
                This program will get the list of compute nodes registered in lem20c128g queue, and 
                find all iTEM processes on those nodes owned by you (or the user specified with -u option).
                Then you can choose to kill all those processes.

                Option -l|--list will output a list of the processes found and will NOT attempt to kill.
                This is a safe option if you just want to look at what you have currently running on the
                cluster nodes. You can save the list to a file and optionally edit it to provide it as 
                input to this program (see option -p).

                Option -p|--procfile will take the list of processes to kill from a file rather than checking
                the compute nodes for processes. The format of the file content is the same as that produced
                by the -l|--list option. Hence, you can first execute this program with the -l|--list option,
                save the output to file, optionally edit the file and finally call this program with the
                -p|--procfile option to have more control over the processes you want to kill.

                Option -n|--nodefile will take the list of node hostnames as input for searching processes
                instead of quering for the node names in the EM queue. Hence you can provide your own list
                of nodes where you want to search/kill your processes.
                Note! Options -p|--procfile and -n|--nodefile are mutually exclusive.

                Option -u|--username allows you to input the user name whose iTEM processes you are looking
                for. Normally, this would be yourself (this is the default if you don't specify any) as you
                are only allowed to kill processes owned by yourself. However, sometimes you want to find
                other user's processes.
"""
    print Usage

def killprocesses_fromlist(processlist, username):
    """Kill processes in list.
    Input: processlist is the list of lines created by the getProcesses() function. This list is verbose
           for reporting to user, and hence some filtering is needed in order to sort out what is
           needed for issuing the remote kill command.
           See getProcesses() function for description of format of the list.
    Input: username is the process owner.
    """
    numlines = len(processlist)
    i = 0
    while i<numlines:
    
        # print line
        # if line starts with lmig, register it as node 
        # and get all pids til next lmig or eof
        line = processlist[i]
        if (line.startswith('lmig')):
            print "Node: " + line
            j = i+1
            mypid = []
            while j < numlines:
                pidline = processlist[j]
                # Test for the next node. This will break to the outer loop
                if (pidline.startswith('lmig')):
                    break
                # Skip lines containing info data only processing lines starting with the user name
                if (pidline.startswith(username)):
                    words = pidline.split()
                    # PID is the second word in the list
                    pid = words[1]
                    mypid.append(pid)
                    j = j+1
                else:
                    # Skip this line and process the next line
                    j = j+1
            i = j
            # Test that there are actually some PIDs to kill
            if (len(mypid) > 0):
                mykillstr = 'ssh ' + line.strip() + ' \'kill'
                for itempid in mypid:
                    mykillstr = mykillstr + ' ' + itempid

                mykillstr = mykillstr + '\''
                
                print mykillstr
                subprocess.call(mykillstr, shell=True)
                subprocess.call("sleep 1", shell=True)

def killprocesses_fromfile(filename, username):
    """Kill processes where the input is provided in a text file.
    Input: filename is the name of the file with list of node and processes to kill.
    The format of this file is the same as the output from this script given the -l or
    --list flag: Sequence of [host, process] sections where each section is comprised of:
    1) One line with the name of the node
    2) One line with heading for the data on consequtive lines.
    3) One or more lines with iTEM process information.
    Example:
    lmigi499.lon.compute.pgs.com
    UID        PID  PPID  C STIME TTY          TIME CMD
    jmalmber  3814     1 95  2016 ?        36-12:08:49 /cfs/empi/trysoe/TEMrad_dev/invpemrad.BETA_5.1.1-mpi513-b1 init.ini pinit.ini
    jmalmber 30493     1 99 Jan18 ?        8-16:48:44 /pgs/em/item init.ini pinit.ini
    jmalmber 30494     1 92 Jan18 ?        8-01:51:49 /pgs/em/item init.ini pinit.ini

    Input: username is the user owning the processes to be killed and has to match the 
    process list in the file.
    """

    myfile = open(filename, "r")
    indata = myfile.readlines()
    myfile.close()
    numlines = len(indata)

    # Do a sanity check of the input before passing to the actuall kill function
    if (len(indata) < 3):
        print "ERROR: Input file seems to lack data. Please check."
        sys.exit(1)
    if (not indata[0].startswith('lmig')):
        print "ERROR: Expected node name in first line of input. Please check."
        print "Indata: " + indata[0]
        sys.exit(1)
    if (not indata[1].startswith('UID')):
        print "ERROR: Expected process info heading starting with UID in second line of input. Please check."
        print "Indata: " + indata[1]
        sys.exit(1)
    if (not indata[2].startswith(username)):
        print "ERROR: Expected process owner " + username + "in third line of input. Please check."
        print "Indata: " + indata[2]
        sys.exit(1)

    # Passed sanity checks. Do the killing
    killprocesses_fromlist (indata, username)


# Get the processes from the compute nodes given in the list of nodes
def getProcesses(nodelist, user):
    """Get the iTEM processes owned by the user.
       Input: nodelist is a list of node names
       Input: user is user name owning the iTEM processes.
       Output: Process list including node names and iTEM processes. Thiss list is
               still a bit verbose to facilitate outputting information to the user.
               It needs further filtering to automate mass killing of processes.

               Format:
               lmigi499.lon.compute.pgs.com
               UID        PID  PPID  C STIME TTY          TIME CMD
               jmalmber  3814     1 95  2016 ?        36-12:08:49 /cfs/empi/trysoe/TEMrad_dev/invpemrad.BETA_5.1.1-mpi513-b1 init.ini pinit.ini
               jmalmber 30493     1 99 Jan18 ?        8-16:48:44 /pgs/em/item init.ini pinit.ini
               jmalmber 30494     1 92 Jan18 ?        8-01:51:49 /pgs/em/item init.ini pinit.ini
    """
    # print "In procedure getProcesses"
    # Prepare the output
    processlist = []
    for node in nodelist:
        print "Get processes for node " + node + "..."
        if (not _allProcesses):
            execstring = "ps -f -u " + user
        else:
            execstring = "ps -ef"

        proc = subprocess.Popen(['ssh', node, execstring], stdout=subprocess.PIPE)
        processes = proc.stdout.readlines()
        # print "Number of lines: %d" % (len(processes))

        # Make the process report - shread off non-iTEM processes, blank lines etc
        foundprocess = 0
        numlines = len(processes)
        for lineidx in range(numlines):
            pline = processes[lineidx]
            # print pline
            # Look for lines with iTEM processes
            if pline.rstrip().endswith('init.ini pinit.ini'):
                if not foundprocess:
                    # print "Found first iTEM process"
                    foundprocess = 1
                    processlist.append(node)
                    processlist.append(processes[0].rstrip('\n'))

                processlist.append(pline.rstrip('\n'))

    return processlist

# Get the list of nodes in the EM queue and make a file where 
# each node is put on one line.
def getNodes():
    """Get the list of nodes in the EM queue and make a list  where 
    each element contains the node name. This list is returned from the function."""
    
    nodelist = []

    if (_usenodefile):
        # Get all the nodes from file
        myfile = open (nodefile, "r")
        for nextline in myfile:
            nodelist.append(nextline.rstrip('\n'))
    else:
        # Call the SGE qconf command to get the list of nodes for the EM queue
        proc = subprocess.Popen(['qconf','-shgrp', '@lem20c128g'], stdout=subprocess.PIPE)
        nodes = proc.stdout.readlines()
        numlines = len(nodes)
        i = 0
        while i<numlines:
            line = nodes[i]
            # This is normally the first line - skip it
            if line.startswith('group_name'):
                i = i+1
                continue
            else:
                # Shread off the first word and then tread the rest as host names
                hostnames = line.split()
                for name in hostnames:
                    # Skip the beginning hostlist and trailing \ and treat the rest as real hosts
                    if (name in ('hostlist', '\\')): continue
                    else:
                        nodelist.append(name)

                # Advance to the next line
                i = i+1
            
    # Done with all the lines - return list
    return nodelist


    
# This is the main program
def main(argv):
    versioninfo = "iTEMproc.py Version 1.1_alpha 2017-02-03"
    username = getpass.getuser()
    global _listProcesses    # Option -l|--list
    _listProcesses = 0
    global _allProcesses     # Option -a|--allprocs
    _allProcesses = 0
    global _useprocfile      # Option -p|--procfile
    _useprocfile = 0
    procfile = ""
    global _usenodefile      # Option -n|--nodefile
    _usenodefile = 0
    global nodefile
    nodefile = ""
    

    # Parse parameters.
    try:
        opts, args = getopt.getopt(argv, "ahp:n:lu:v", ["allproc", "help", "procfile=", "nodefile=", "list", "user=", "version"])
    except getopt.GetoptError:
        print "ERROR: Unknown option\n"
        usage()
        sys.exit(2)

    # opts contain list of tuples (flag, argument) where argument is None if flag does not take any argument
    for opt, arg in opts:
        if opt in ("-a", "--allprocs"):
            _allProcesses = 1
            _listProcesses = 1
        elif opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-p", "--procfile"):
            if (_usenodefile):
                print "Don't use option -p|--procfile and -n|--nodefile at the same time!\n"
                usage()
                sys.exit(2)
            _useprocfile = 1
            procfile = arg
        elif opt in ("-n", "--nodefile"):
            if (_useprocfile):
                print "Don't use option -p|--procfile and -n|--nodefile at the same time!\n"
                usage()
                sys.exit(2)
            _usenodefile = 1
            nodefile = arg
            
        elif opt in ("-l", "--list"):
            _listProcesses = 1
        elif opt in ('-u', "--user"):
            username = arg
        elif opt in ('-v', "--version"):
            print versioninfo
            sys.exit()

    Welcome = """
====================================================
=        iTEM process management program           =
===================================================="""

    print Welcome
    nodelist = getNodes()

    # Check if the process list is given in file in which case we bypass the processing of
    # nodes and getting the process list.
    if (len(procfile) > 0):
        print "Input data provided in file: " + procfile
        answer = raw_input ("\n\nContinuing will kill your iTEM processes specified in the file. Do you want to proceed? [y/n]: ")
        if (not answer == 'y'):
            print "You decided to quit. Exiting without killing processes."
            sys.exit(0)

        killprocesses_fromfile(procfile, username)
        sys.exit(0)

    print "Got %d nodes in EM queue." % (len(nodelist))
    if (not _allProcesses):
        print "Look for processes owned by " + username + "..."
    else:
        print "Look for all iTEM processes..."

    processlist = getProcesses(nodelist, username)

    if (not _allProcesses):
        print "Process status for user: " + username
    else:
        print "Process status all users:"
    for line in processlist:
        print line

    if _listProcesses:
        sys.exit(0)

    if (len(processlist) == 0):
        print "No processes found."
        sys.exit (0)

    # This section calls the kill processes functionality.
    # Provide a warning to the destructive nature of this funcionality.
    answer = raw_input ("\n\nContinuing will kill all your iTEM processes. Do you want to proceed? [y/n]: ")
    if (not answer == 'y'):
        print "You decided to quit. Exiting without killing processes."
        sys.exit(0)

    if (len(processlist) > 0):
        killprocesses_fromlist(processlist, username)
    else: 
        print "No processes to kill."

    sys.exit(0)

# This calls the main program, tearing off the name of the script from the arguments
# passing the rest to the main program.
if __name__ == "__main__":
    main(sys.argv[1:])
