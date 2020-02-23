#!/usr/bin/python3

# coding=Latin-1

print( "hello world!")
print ("""
Here are some fundamental programming constructs
in Python.
""")

# Comments are prefixed by the pound character.

# if elif else statement
# the elif is used instead of switch-case constructs in C/C++/Java
#x = int(raw_input("Please enter integer: "))
x = 0
if x < 0:
    x = 0
    print ('Negative changed to zero')
elif x == 0:
    print ('Zero!')
elif x == 1:
    print ('Single')
else:
    print ('More')

# Here are list examples
list1 = ['per', 'pal', 'espen askeladd']

print (list1)
