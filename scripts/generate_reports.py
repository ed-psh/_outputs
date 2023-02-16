#!/opt/local/bin/python
# -*- coding: UTF-8 -*-

import os
import re
import oyaml as yaml
from slugify import slugify
import yamlfunctions
from numpy import mean
from pyaltmetric import Altmetric

scriptpath = os.path.dirname(os.path.realpath(__file__))
os.chdir(scriptpath)
sourcedirectory = "../"

def replace_liquid(thistext, ymldic):
    '''
        Replace liquid-style {{page.doi}} tags with the relevant bit from yaml header
    '''
    lm = "\{\{ *page\..*?\}\}"
    for thismatch in re.findall(lm, thistext):
        key = thismatch.replace("{{","").replace("}}","").replace("page.","").strip()
        try:
            ymldic[key]
        except:
            continue
        thistext = thistext.replace(thismatch, ymldic[key])
    return thistext

def get_altmetric(thisdoi):
    a = Altmetric()
    alt = a.doi(thisdoi.split("doi.org/")[1])
    return int(alt["score"])

def replace_imagepath(thistext, root="../../"):
    figureformat = '!\[.*?\]\(.*?\).*?\n'
    figures_found = re.findall(figureformat, thistext)
    for f in figures_found:
        path = f.split("(")[1]
        path = path.split(")")[0]
        ps = 0
        if path.startswith("/"):
            ps = 1
        g = f.replace(path, os.path.abspath(os.path.join(root, path[ps:])))
        thistext = thistext.replace(f, g)
    return thistext

outputfiles = [x for x in os.listdir(sourcedirectory) if not x.startswith(".") and not x.startswith("Icon") and x.endswith(".md") and not x.startswith("_")]

weightdict = {}
outdict = {}
fileduplicates = {}
altdict = {}
listdict = {}

projectdict = {}
for filename in outputfiles:
    print (filename)
    thispath = os.path.join(sourcedirectory, filename)
    with open(thispath) as f:
        text = f.read()
        y, r = yamlfunctions.readheader(text)
        yml = yamlfunctions.getyaml(y)
        if "projects" in yml:
            for project in yml["projects"]:
                try:
                    projectdict[project]
                except:
                    projectdict[project]={}
                projectdict[project][filename]={}
        else:
            continue
        altscore = ""
        ref = ""
        if "doi" in yml:
            try:
                a = get_altmetric(yml["doi"])
            except:
                a = None
                pass
            try:
                fileduplicates[yml["doi"]]
                print ("***Duplicate doi***\n\t{}\n\t{}\n\t{}\n".format(yml["doi"], fileduplicates[yml["doi"]], filename))
            except:
                pass
            fileduplicates[yml["doi"]] = filename
        r = replace_liquid(r, yml)
        r = replace_imagepath(r)
        for project in yml["projects"]:
            projectdict[project][filename]["weight"] = yml["weight"]
            projectdict[project][filename]["title"] = yml["title"].strip()
            projectdict[project][filename]["text"] = r.strip()
            if "doi" in yml:
                projectdict[project][filename]["doi"] = yml["doi"].strip()
                if a:
                    projectdict[project][filename]["score"] = a
                    projectdict[project][filename]["scoretext"] = "Altmetric score: {} [{}]".format(a, yml["doi"])
                else:
                    projectdict[project][filename]["scoretext"] = ""
            else:
                projectdict[project][filename]["scoretext"] = ""


for project in projectdict:
    textfile = os.path.join("reports", "{}.md".format(slugify(project)))
    listfile = os.path.join("reports", "{}_list.md".format(slugify(project)))
    altscoreslist = [projectdict[project][x]["score"] for x in projectdict[project] if "score" in projectdict[project][x]]
    weightdict = {x:projectdict[project][x]["weight"] for x in projectdict[project] if "weight" in projectdict[project][x]}
    summary = "**{} has produced {} papers with an average altmetric score of {:.0f}.**\n\n".format(
                project.upper(),
                len(altscoreslist),
                mean(altscoreslist)
            )
    with open(textfile,"w") as o:
        with open(listfile,"w") as p:
            o.write(summary)
            for k,v, in [(k, weightdict[k]) for k in sorted(weightdict, key=weightdict.get, reverse=False)]:
                if k in projectdict[project]:
                    o.write("{}\n".format("# {}\n\n".format("\n\n".join([
                                    projectdict[project][k]["title"],
                                    projectdict[project][k]["text"],
                                    projectdict[project][k]["scoretext"],
                                    ])
                                )))
                    if "doi" in projectdict[project][k]:
                        p.write("- {} [{}]\n".format(projectdict[project][k]["title"], projectdict[project][k]["doi"]))



















