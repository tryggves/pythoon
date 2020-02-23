#!/usr/bin/python3
import json

my_pylist = {
    "author" : "Tryggve Sorensen",
    "age" : 24,
    "results" : [1, 2, 2, 1]
}

my_parr = [ 25, 26, 27, 28 ]


print(json.dumps(my_pylist, indent=2))
print(json.dumps(my_parr, indent=2))

with open("./commits.json", "r") as read_file:
    data = json.load(read_file)

print("Number of objects: ", len(data))
# count = 0
# for entry in data:
#    count = count+1
#    print("Entry num: ", count, "\tEntry length: ", len(entry))

entry = data[1]
print("Entry type: ", type(entry))
# print(entry)

# Iterate through entry
for item in entry:
    print("Item of type: ", type(item), "\tContent: ", item)
    print(item, " : ", entry[item])
print("Done.")
