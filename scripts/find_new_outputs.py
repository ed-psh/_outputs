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
parser.add_argument('-n', '--newsearch',    action="store_true", default=False,    help='use proxy for scholar')
args = parser.parse_args()
#-----------------------------
def search_scholar(ids, filename):
    titlelist = []
    with open(filename, "w") as o:
        for thisid in ids:
            author = scholarly.search_author_id(thisid)
            author = scholarly.fill(author, sections=["publications"])
            o.write("index,citations,year,title\n")
            for i,x in enumerate(author['publications']):
                titlelist.append(x['bib']['title'])
                try:
                    if 'pub_year' in x['bib']:
                        o.write("{},{},{},{}\n".format(
                            i+1,
                            x["num_citations"],
                            x['bib']['pub_year'],
                            x['bib']['title'],
                            ))
                    else:
                        o.write("{},{},,{}\n".format(
                            i+1,
                            x["num_citations"],
                            x['bib']['title'],
                            ))
                except:
                    print ("failed:\n{}".format(x))
    return list(set(titlelist))

#-----------------------------
# search google scholar and store all titles in a csv file
args.newsearch = True

if args.newsearch:
    # GOOGLE SCHOLAR
    if args.use_proxy:
        from scholarly import ProxyGenerator # Set up a ProxyGenerator object to use free proxies. This needs to be done only once per session
        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg)
    scholartitles = search_scholar(scholar_search_ids, "catalog/google-scholar.csv")
    print (len(scholartitles), "papers found in scholar")
    with open("catalog/google-scholar.json","w") as o:
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
        with open("already.json") as f:
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
    with open("catalog/pbib.json","w") as o:
        json.dump(pbib, o)
    with open("catalog/already.json","w") as o:
            json.dump(already, o)

with open("catalog/google-scholar.json") as f:
    scholartitles = json.load(f)

with open("catalog/pbib.json") as f:
    pbib = json.load(f)

#m = difflib.get_close_matches(a, affiliations, 6, args.similarity)[1:]

print (pbib.keys())

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
                print (e)
                continue
            print (thisfile, doi)
            if doi in pbib:
                print ("==> already have a file for {}".format(doi))
                del pbib[doi]

print ("pbib len now:", len(pbib))

outputfields = [
    "Title",
    "Month",
    "Year",
    "Journal",
    "doi",
    ]

for i,key in enumerate(pbib.keys()):
    filename = "_{}.md".format(slugify.slugify(pbib[key]["Title"].lower()[:18]))
    y = {x.lower():pbib[key][x] for x in pbib[key] if x in outputfields}
    y["projects"] = ["example-project"]
    y["featured"] = "true"
    y["weight"] = 200
    r = ""
    if "Abstract" in pbib[key]:
        r = pbib[key]["Abstract"]
    newcontents = "---\n{}---\n\n{}".format(yaml.dump(y).replace("\n\n","\n"),r)
    with open(os.path.join(outputdir,filename),"w") as o:
        o.write(newcontents)








