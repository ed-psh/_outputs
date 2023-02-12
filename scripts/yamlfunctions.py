import re
import oyaml as yaml

#-------------
def getyaml(text):
    h,r = readheader(text)
    if h.startswith("---"):
        h = h[4:-3] # strip yaml identifiers
    yml = yaml.load(h, Loader=yaml.Loader)
    if yml:
        return yml
    else:
        return {}

def mergeyaml(priority_yaml, extra_yaml):
    # keep the contents of the first yaml if there is a conflict
    if not(priority_yaml):
        priority_yaml = {}
    if extra_yaml:
        for item in extra_yaml:
            try:
                priority_yaml[item]
            except:
                priority_yaml[item] = extra_yaml[item]
    return priority_yaml

def readheader(filecontents):
    '''
        Read a valid markdown yaml header
        Input is full text of file
        Returns list of header items + full text of remainder
    '''
    t = filecontents.strip()
    t = t.replace('\r','\n')
    h = ""
    remainder = filecontents
    lines = [x for x in t.split('\n')] # don't strip because indentation matters
    if lines[0].strip() == '---':
        h1 = re.findall( '---[\s\S]+?---',filecontents)
        h2 = re.findall( '---[\s\S]+?\.\.\.',filecontents)
        if len(h1)>0 and len(h2)>0:
            #print ("both yaml header formats match! Taking the shorter one")
            if len(h1[0]) < len(h2[0]):
                h=h1[0]
                #print ("Choosing ---/---\n", h)
            else:
                h=h2[0]
                #print ("Choosing ---/...\n", h)
        elif len(h1)>0:
            h = h1[0]
        elif len(h2)>0:
            h = h2[0]
        remainder = filecontents.replace(h,'')
    return h, remainder
#-------------
