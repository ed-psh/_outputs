import re
import sys
import select
import difflib
import requests
from Bio import Entrez
from Bio import Medline
from lxml import etree
import xml.etree.ElementTree as ET
no_user_response_count =0
#------ PUBMED FUCTIONS -------

Entrez.email = "psh@ed.ac.uk"
Entrez.tool = "PSH_Outputs"

def search_pubmed(search_string, restrictfields=""):
    '''return a list of pmids for articles found by a search string'''
    if search_string is None:
        return []
    if len(search_string.strip())==0:
        return []
    max_returns = 500
    days = "all"
    try:
        handle = Entrez.esearch(db="pubmed", term=search_string, retmax=max_returns, rettype="medline", field=restrictfields)
        r = Entrez.read(handle)
    except Exception as e:
        print ("pubmed search failure:", e)
        return []
    return r['IdList']

# --------------------


def p2b(pmidlist):
    ''' by Nick Loman '''

    if type(pmidlist) != list:
        pmidlist = [str(pmidlist)]

    ## Fetch XML data from Entrez.
    efetch = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    url = '{}?db=pubmed&id={}&rettype=abstract'.format(efetch, ','.join(pmidlist))
    try:
        r = requests.get(url)
    except:
        return []
    ##print(r.text) # to examine the returned xml
    ## Loop over the PubMed IDs and parse the XML using https://docs.python.org/2/library/xml.etree.elementtree.html
    bibout = []
    par = etree.XMLParser(encoding='utf-8', recover=True)
    root = ET.fromstring(r.text, parser=par)
    if root:
        for PubmedArticle in root.iter('PubmedArticle'):
            PMID = PubmedArticle.find('./MedlineCitation/PMID')
            ISSN = PubmedArticle.find('./MedlineCitation/Article/Journal/ISSN')
            Volume = PubmedArticle.find('./MedlineCitation/Article/Journal/JournalIssue/Volume')
            Issue = PubmedArticle.find('./MedlineCitation/Article/Journal/JournalIssue/Issue')
            Year = PubmedArticle.find('./MedlineCitation/Article/Journal/JournalIssue/PubDate/Year')
            Month = PubmedArticle.find('./MedlineCitation/Article/Journal/JournalIssue/PubDate/Month')
            Title = PubmedArticle.find('./MedlineCitation/Article/Journal/Title')
            ArticleTitle = PubmedArticle.find('./MedlineCitation/Article/ArticleTitle')
            MedlinePgn = PubmedArticle.find('./MedlineCitation/Article/Pagination/MedlinePgn')
            Abstract = PubmedArticle.find('./MedlineCitation/Article/Abstract/AbstractText')
            # jkb additions
            PMCID = None
            DOI = None
            theseids = PubmedArticle.findall('./PubmedData/ArticleIdList/ArticleId')
            for thisid in theseids:
                if thisid.attrib['IdType'] == 'pmc':
                    PMCID = thisid
                elif thisid.attrib['IdType'] == 'doi':
                    DOI = thisid
            # format author list
            authors = []
            for Author in PubmedArticle.iter('Author'):
                try:
                    LastName = Author.find('LastName').text
                    ForeName = Author.find('ForeName').text
                except AttributeError:  # e.g. CollectiveName
                    continue
                authors.append('{}, {}'.format(LastName, ForeName))
            ## Use InvestigatorList instead of AuthorList
            if len(authors) == 0:
                ## './MedlineCitation/Article/Journal/InvestigatorList'
                for Investigator in PubmedArticle.iter('Investigator'):
                    try:
                        LastName = Investigator.find('LastName').text
                        ForeName = Investigator.find('ForeName').text
                    except AttributeError:  # e.g. CollectiveName
                        continue
                    authors.append('{}, {}'.format(LastName, ForeName))
            if Year is None:
                _ = PubmedArticle.find('./MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate')
                Year = _.text[:4]
                Month = '{:02d}'.format(list(calendar.month_abbr).index(_.text[5:8]))
            else:
                Year = Year.text
                if Month is not None:
                    Month = Month.text
            '''
            try:
                for _ in (PMID.text, Volume.text, Title.text, ArticleTitle.text, MedlinePgn.text, Abstract.text, ''.join(authors)):
                    if _ is None:
                        continue
                    assert '{' not in _, _
                    assert '}' not in _, _
            except AttributeError:
                pass
            '''

            # make the bibtex formatted output.
            bib = {}
            if len(authors)>0:
                authorname = authors[0].split(',')[0]
            else:
                authorname = ''
            try:
                titlewords = [x for x in ArticleTitle.text.split(' ') if len(x)>3]
            except:
                print ("PUBMED ERROR - no article title for PMID:{}: {}".format(PMID.text, ArticleTitle.text))
                continue
            if len(titlewords)>2:
                titlestring = ''.join(titlewords[:3])
            elif len(titlewords)>0:
                titlestring = ''.join(titlewords)
            else:
                titlestring = ''
            if len(authorname+titlestring)==0:
                titlestring = "PMID{}_".format(PMID.text)
            new_id = '{}{}{}'.format(authorname, titlestring, Year).lower()
            new_id = re.sub(r'\W+', '', new_id)
            try:
                bib["ID"] = latexchars.replace_accents(new_id)
            except:
                bib["ID"] = new_id
            bib["Author"] = ' and '.join(authors)
            bib["Title"] = ArticleTitle.text
            bib["Journal"] = Title.text
            bib["Year"] = Year
            if Volume is not None:
                bib["Volume"] = Volume.text
            if Issue is not None:
                bib["Number"] = Issue.text
            if MedlinePgn is not None:
                bib["Pages"] = MedlinePgn.text
            if Month is not None:
                bib["Month"] = Month
            # bib[""] = (' Abstract={{{}}},'.format(Abstract.text))
            if PMCID is not None:
                bib["pmcid"] = PMCID.text
            if DOI is not None:
                bib["doi"] = DOI.text
            if ISSN is not None:
                bib["ISSN"] = ISSN.text
            bib["pmid"] = PMID.text
            # always return clean latex
            try:            
                bib = {d:latex_to_unicode(bib[d]) for d in bib.keys()}
            except:
                pass
            bibout.append(bib)
    return bibout

def searchtitle(thistitle):
    global no_user_response_count
    thistitle = str(thistitle.strip())
    ask = True
    if no_user_response_count > 2:
        print ("No user response to previous 3 queries. Running in silent mode.")
        ask = False
    #print ("searching pubmed for this title:\t{}".format(thistitle))
    pub = search_pubmed(thistitle, "title")
    if len(pub) == 1:
        pmid = pub[0]
        pubent = p2b(pmid)
        if len(pubent) > 0:
            if pubent[0] != 'null' and pubent[0] != None:
                # compare titles. If they are almost identical, just go for it
                s = difflib.SequenceMatcher(None, thistitle, pubent[0]['Title'])
                diffratio = s.ratio()
                if diffratio > 0.99:
                    return pubent[0]
                # if titles don't match, ask user
                if ask:
                    question = "--------------\n\
    New citation (PMID:{}) found in Pubmed. Please check that input is the same as the found citation for this reference block: \n\
    \n\n{}\n{}\n\n{}\n\n\
    Enter y/n within 10 seconds".format(
                        pmid,
                        "{:>12}:    {}".format('Input Title', thistitle),
                        "{:>12}:    {}".format('Found Title', pubent[0]['Title']),
                        '\n'.join( ["{:>12}:    {}".format(x,pubent[0][x]) for x in pubent[0] if x != "Title"])
                        )
                    #q = input (question)
                    print (question)
                    i,o,e = select.select([sys.stdin],[],[],10) # 10 second timeout
                    if i==[] and o==[] and e==[]:
                        no_user_response_count += 1
                    if i:
                        q = sys.stdin.readline().strip()
                        q = q.strip().upper()
                        if q == "Y":
                            print ('--confirmed--')
                            return pubent[0]
        return None



