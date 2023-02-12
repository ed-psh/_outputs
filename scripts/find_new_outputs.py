'''
Search the internet for outputs that don't match the existing ones.
Where a new output is found, automatically create a new draft filename beginning with underscore '_xxx.md'
'''
import argparse
from scholarly import scholarly
#-----------------------------
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--use-proxy',    action="store_true", default=False,    help='use proxy for scholar')
args = parser.parse_args()
#-----------------------------
def search_scholar(id, filename):
	author = scholarly.search_author_id(id)
	author = scholarly.fill(author, sections=["publications"])
	with open(filename, "w") as o:
		o.write("index,citations,year,title\n")
		for i,x in enumerate(author['publications']):
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
#-----------------------------
if args.use_proxy:
	from scholarly import ProxyGenerator
	# Set up a ProxyGenerator object to use free proxies
	# This needs to be done only once per session
	pg = ProxyGenerator()
	pg.FreeProxies()
	scholarly.use_proxy(pg)

# search google scholar and store all titles in a csv file
search_scholar("pZcYYCkAAAAJ", "catalog/googlescholar.csv")







