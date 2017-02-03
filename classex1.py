#!/usr/bin/python

import sys

class Node:
    def __init__(self, nodename):
        self.mynodename = nodename
        self.processlist = []

    def getProcesses(self):
        print ("In getProcesses")
        self.processlist = ["process 1", "process 2", "process 3"]

    def printProcesses(self):
        for process in self.processlist:
            print "Process: " + process


class NodeList:
    def __init__(self, nodelistfile):
        myfile = open (nodelistfile, "r")
        indata = myfile.readlines()
        myfile.close()
        # Nodelist is a list of class Node
        self.nodelist = []
        for node in indata:
            # Instantiate node and append it to the node list.
            nextnode = Node(node.rstrip('\n'))
            self.nodelist.append(nextnode)

    def printNodes(self):
        print ("IN printNodes()")
        for presentnode in self.nodelist:
            print "Present node: " + presentnode.mynodename
        
    def getNodeProcesses(self):
        for presentnode in self.nodelist:
            presentnode.getProcesses()

    def printNodeProcesses(self):
        for presentnode in self.nodelist:
            print "Processes for: " + presentnode.mynodename
            presentnode.printProcesses()

# Main program starts here
print "Hello world"
mynodelist = NodeList("nodes.txt")
mynodelist.printNodes()
print "\nGetting processes..."
mynodelist.getNodeProcesses()
print "\nListing processes..."
mynodelist.printNodeProcesses()


sys.exit()
