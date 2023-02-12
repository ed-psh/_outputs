#!/opt/local/bin/python
# -*- coding: UTF-8 -*-

'''
find all md files matching the patter [title]({{page.doi}})
delete that line
put title-text in yaml
'''

import os
import re
import oyaml as yaml
import yamlfunctions
from dateutil import parser

outputdir = os.path.abspath("../")
ignorelist = ["__README.md"]
files = [x for x in os.listdir(outputdir) if not x.startswith(".") and not x in ignorelist]

for i,thisfile in enumerate(files):
    filepath = os.path.join(outputdir, thisfile)
    if os.path.isdir(filepath):
        continue
    new_yaml = {}
    with open(filepath) as f:
        text = f.read()
    links = re.findall(r"\[.+?\]\(\{\{page\.doi\}\}\)", text)
    if len(links) > 0:
        link_text = links[0].split("]")[0][1:]
        print (thisfile)
        print (link_text)
        for j in range(4,1,-1):
            try:
                datesource = " ".join(link_text.split(" ")[-j:])
            except:
                continue
            try:
                dt = parser.parse(datesource)
            except:
                continue
            month = '{:%B}'.format(dt)
            year = '{:%Y}'.format(dt)
            journal = " ".join(link_text.split(" ")[:-j])
            print ("   {} {} {}\n".format(journal, month, year))

            new_yaml["journal"] = journal
            new_yaml["month"] = month
            new_yaml["year"] = year
            break

        h,r = yamlfunctions.readheader(text)
        y = yamlfunctions.getyaml(h)
        y = yamlfunctions.mergeyaml(y,new_yaml)
        r = r.replace(links[0],"")
        r = r.replace("\n\n","\n")
        newcontents = "---\n{}---\n\n{}".format(yaml.dump(y).replace("\n\n","\n"),r)
        with open(filepath,"w") as o:
            o.write(newcontents)









