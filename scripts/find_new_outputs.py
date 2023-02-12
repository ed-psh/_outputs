'''
Search the internet for outputs that don't match the existing ones.
Where a new output is found, automatically create a new draft filename beginning with underscore '_xxx.md'
'''

pubmed_search_terms = [
    "Baillie Gifford Pandemic Science Hub[Affiliation]",
    "ISARIC4C[Author - Corporate]",
    "ISARIC-4C[Author - Corporate]",
    "ISARIC 4C[Author - Corporate]",
    "ISARIC4C Consortium[Author - Corporate]",
    "(Baillie JK[Author] AND Semple MG[Author])",
    "(Baillie JK[Author] AND Semple M[Author])",
    "(Baillie K[Author] AND Semple MG[Author])",
    "(CO-CIN) NOT (Cinaciguat)",
    "GenOMICC[Author - Corporate]",
    "(Baillie JK[Author] AND Pairo-Castineira E[Author])",
    "PHOSP COVID[ti]",
    "PHOSP-COVID[ti]",
    "PHOSP[Author - Corporate]",
    "PHOSP-COVID Collaborative Group[Author - Corporate]",
    "HEAL COVID[Author - Corporate]",
    "((HEAL COVID) AND (Summers[Author])) AND (Toshner[Author])",
    '"Outbreak Data Analysis Platform"',
    ]

scholar_search_ids = [
    "pZcYYCkAAAAJ", # Calum's ISARIC4C one
    ]

scholarjson = "catalog/google-scholar.json"
pbibjson = "catalog/pbib.json"
alreadyjson = "catalog/already.json"

#-----------------------------
import os
import json
import slugify # pip install python-slugify
import argparse
import oyaml as yaml
import yamlfunctions
import pubmedfunctions
from scholarly import scholarly
#-----------------------------
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--use-proxy',    action="store_true", default=False,    help='use proxy for scholar')
parser.add_argument('-s', '--skipnewsearch',    action="store_true", default=False,    help='skip scholar and pubmed searches')
args = parser.parse_args()
#-----------------------------
def search_scholar(ids):
    titlelist = []
    for thisid in ids:
        author = scholarly.search_author_id(thisid)
        author = scholarly.fill(author, sections=["publications"])
        for i,x in enumerate(author['publications']):
            titlelist.append(x['bib']['title'])
    return list(set(titlelist))
#-----------------------------
if not args.skipnewsearch:
    # GOOGLE SCHOLAR
    if args.use_proxy:
        from scholarly import ProxyGenerator # Set up a ProxyGenerator object to use free proxies. This needs to be done only once per session
        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg)
    scholartitles = search_scholar(scholar_search_ids)
    print (len(scholartitles), "papers found in scholar")
    with open(scholarjson,"w") as o:
        json.dump(scholartitles, o)

    # PUBMED
    search_string = " OR ".join("({})".format(x) for x in pubmed_search_terms)
    ids = list(set(pubmedfunctions.search_pubmed(search_string)))
    pbiblist = pubmedfunctions.p2b(ids)
    pbib = {}
    for entry in pbiblist:
        try:
            pbib[entry["doi"].lower()] = entry
        except:
            print ("no doi for {}".format(entry))
    print (len(ids), "papers found in pubmed")

    try:
        with open(alreadyjson) as f:
            already = json.load(f)
    except:
        already = []
    n = 0
    for t in scholartitles:
        if t not in already:
            newbib = pubmedfunctions.searchtitle(t)
            if newbib:
                already.append(t)
                if "doi" in newbib:
                    if newbib["doi"] not in pbib.keys():
                        pbib[newbib["doi"]] = newbib
                        n+=1

    print ("{} added from pubmed search of scholar titles")
    with open(pbibjson,"w") as o:
        json.dump(pbib, o, indent=4)
    with open(alreadyjson,"w") as o:
        json.dump(list(set(already)), o, indent=4)

if os.path.exists(scholarjson):
    with open(scholarjson) as f:
        scholartitles = json.load(f)
else:
    scholartitles = {}

if os.path.exists(pbibjson):
    with open(pbibjson) as f:
        pbib = json.load(f)
else:
    pbib = {}

outputdir = os.path.abspath("../")
ignorelist = ["__README.md"]
files = [x for x in os.listdir(outputdir) if not x.startswith(".") and not x in ignorelist]
for i,thisfile in enumerate(files):
    filepath = os.path.join(outputdir, thisfile)
    if os.path.isdir(filepath):
        continue
    with open(filepath) as f:
        text = f.read()
        h,r = yamlfunctions.readheader(text)
        y = yamlfunctions.getyaml(h)
        if "doi" in y:
            try:
                doi = y["doi"].split("doi.org/")[1].lower()
            except Exception as e:
                print ("DOI not formatted as expected for {} ({})".format(thisfile, e))
                continue
            if doi in pbib:
                del pbib[doi]

outputfields = [
    "Title",
    "Month",
    "Year",
    "Journal",
    ]

for i,key in enumerate(pbib.keys()):
    filename = "_{}.md".format(slugify.slugify(pbib[key]["Title"].lower()[:18]))
    print ("Creating file {} for doi {}".format(filename, key))
    y = {x.lower():pbib[key][x] for x in pbib[key] if x in outputfields}
    y["projects"] = ["example-project"]
    y["featured"] = "false"
    y["weight"] = 200
    if "doi" in pbib[key]:
        y["doi"] = "https://doi.org/{}".format(pbib[key]["doi"])
    r = ""
    if "Abstract" in pbib[key]:
        r = pbib[key]["Abstract"]
    newcontents = "---\n{}---\n\n{}".format(yaml.dump(y).replace("\n\n","\n"),r)
    with open(os.path.join(outputdir,filename),"w") as o:
        o.write(newcontents)








