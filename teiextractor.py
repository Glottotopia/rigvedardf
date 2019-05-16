import sys
import xml.etree.ElementTree as ET


class Utterance():
  def __init__(self,unsegmentedwords, glosses,sentenceID):
    self.unsegmentedwords = unsegmentedwords
    self.glosses = glosses 
    self.segmentedwords = []
    self.sentenceID = sentenceID
    self.joiners = [] #there is only one joiner per word for this use case
    for i,w in enumerate(unsegmentedwords):
      joiner = ''
      if(len(unsegmentedwords)!=len(glosses)):
        return #faulty XML
      lg = self.glosses[i]['lexicalgloss'] 
      gg = self.glosses[i]['grammaticalgloss'] 
      if lg in self.unsegmentedwords[i]:
        self.segmentedwords.append(self.unsegmentedwords[i].replace(lg,'%s-'%lg))
        joiner = '-'
      else:
        self.segmentedwords.append(self.unsegmentedwords[i])
        if gg != '': #there is a grammaticalgloss, but we do not know the segmentation
          joiner = '.'
      self.joiners.append('-')
      
  def _utteranceRDF(self,ID):
    print("\n:u%s: a ligt:Utterance ;"%ID)
    print('\tCoNNL:ID "%s" .'%sentenceID)
    print('\tdcterms:isPartOf "rigveda:%s" ;'%sentenceID[:-1].replace('.',''))
    self._wordtierRDF(ID,self.unsegmentedwords,ID)
    self._morphemetierRDF(ID,self.segmentedwords,glosses,ID)
    
  def _wordtierRDF(self,number,tier,parent):
    print("\n:wt%s a ligt:wordtier ;"%number)
    print('	powla:hasParent :u%s ;'%parent)
    print('	rdfs:label "%s"@sk .'%' '.join(tier))
    for wordnumber,word in enumerate(tier):
      print("\n:w%s.%s a ligt:word;"%(number,wordnumber))
      print('	dcterms:isPartOf :wt%s ;'%number)
      if wordnumber+1 < len(tier):
        nextnumber = wordnumber + 1
        print('	ligt:next :wt%s.%s ;'%(number,nextnumber))
      print('	rdfs:label "%s"@sk .'%word)
    
  def _morphemetierRDF(self,number,segmentedwords,glosses,parent):
    print("\n:mt%s a ligt:morphemetier ;"%number)
    print("	powla:hasParent :u%s ;"%parent)
    ID = "mt%s"%number 
    if len(segmentedwords) != len(glosses):
      #print("number of words do not match across lines")
      return
    for wordnumber,gloss in enumerate(glosses):
        if gloss['grammaticalgloss'] == '': #monomorphemic
          print("\n:mt%sm%s.0 a ligt:morph ;"%(parent,wordnumber))
          print("	dcterms:isPartOf :mt%s ;"%number)
          print("	dcterms:isPartOf :w%s.%i ;"%(number,wordnumber))
          print('	rdfs:label "%s"@sk ;'%self.segmentedwords[wordnumber])
          print('	rdfs:label "%s"@en ;'%gloss['lexicalgloss'])           
          if wordnumber+1 < len(glosses):
            nextnumber = wordnumber + 1
            print('	ligt:next :mt%sm%s.%s .'%(parent,wordnumber+1,0))
        else:
          try:
            stem,suffix = self.segmentedwords[wordnumber].split('-') #bimorphemic segmentable
            print("\n:mt%sm%s.0 a ligt:morph ;"%(parent,wordnumber))
            print("	dcterms:isPartOf :mt%s ;"%number)
            print("	dcterms:isPartOf :w%s.%i ;"%(number,wordnumber))
            print('	rdfs:label "%s"@sk ;'%stem)
            print('	rdfs:label "%s"@en ;'%gloss['lexicalgloss'])
            print('	ligt:next :mt%sm%s.%s .'%(parent,wordnumber,1))
          
            print("\n:mt%sm%s.1 a ligt:morph ;"%(parent,wordnumber))
            print("	dcterms:isPartOf :mt%s ;"%number)
            print("	dcterms:isPartOf :w%s.%i ;"%(number,wordnumber))
            print('	rdfs:label "%s"@sk ;'%suffix)
            print('	rdfs:label "%s"@en ;'%gloss['grammaticalgloss'])            
            if wordnumber+1 < len(glosses):
              nextnumber = wordnumber + 1
              print('	ligt:next :mt%sm%s.%s .'%(parent,wordnumber+1,0))
          except ValueError:  #bimorphemic non-segmentable
            print("\n:mt%sm%s.0 a ligt:morph ;"%(parent,wordnumber))
            print("	dcterms:isPartOf :mt%s ;"%number)
            print("	dcterms:isPartOf :w%s.%i ;"%(number,wordnumber))
            print('	rdfs:label "%s"@sk ;'%segmentedwords[0])
            print('	rdfs:label "%s"@en ;'%"%s.%s"%(gloss['lexicalgloss'],gloss["grammaticalgloss"]))           
            if wordnumber+1 < len(glosses):
              nextnumber = wordnumber + 1
              print('	ligt:next :mt%sm%s.%s .'%(parent,wordnumber+1,0))
          
            
      
    
  
  def toRDF(self,ID):
    self._utteranceRDF(ID)
    

filename = sys.argv[1]
bookID = filename[-11:-8]

tree = ET.parse(filename)
root = tree.getroot()

divs = root.findall('.//{http://www.tei-c.org/ns/1.0}div[@type="verse"]')

lgs = root.findall(".//{http://www.tei-c.org/ns/1.0}lg")

print("""@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
@prefix dcterms: <http://purl.org/dc/terms/>.  
@prefix ligt: <http://purl.org/liodi/ligt#>.  
@prefix powla: <http://purl.org/powla/powla.owl#>. 
@prefix CoNNL: <http://ufal.mff.cuni.cz/conll2009-st/task-description.html#>.  
@prefix rigveda: <https:/vedaweb.uni-koeln.de#>.    
""")
print("x a document ;")
utteranceID=0 
for lg in lgs: 
  ls = lg.findall("{http://www.tei-c.org/ns/1.0}l")  
  #ls = lg.findall("{http://www.tei-c.org/ns/1.0}l[string(@ana)='']")
  full_ls = ls[::2] #<l>s which contain the full line with all words
  ls_with_fs = ls[1:][::2] #<l>s with have <f>s
  lpairs = zip(full_ls,ls_with_fs)
  for lpair in lpairs: 
    full = lpair[0]
    sentenceID = None
    try:
      sentenceID = full.find('.').attrib.get('n')
    except KeyError:
      pass
    gra_lemma= lpair[1].findall(".//{http://www.tei-c.org/ns/1.0}f[@name='gra_lemma']/{http://www.tei-c.org/ns/1.0}string")
    morphosyntax = lpair[1].findall(".//{http://www.tei-c.org/ns/1.0}f[@name='morphosyntax']")
    imt = zip(gra_lemma, morphosyntax)
    unsegmentedwords = full.text.strip().split()
    glosses = []
    for i,item in enumerate(imt):
      grammaticalgloss = None
      lexicalgloss = item[0].text.strip().replace('	~ ','~').replace('-','')
      try:
        #collect all morphosyntactic categories
        grammaticalgloss = '.'.join([el.attrib['value'] for el in item[1].findall('.//{http://www.tei-c.org/ns/1.0}symbol')])
      except AttributeError:
        pass 
      glosses.append({'lexicalgloss':lexicalgloss,'grammaticalgloss':grammaticalgloss}) 
    if glosses != []:      
      u = Utterance(unsegmentedwords,glosses,sentenceID)
      u.toRDF("%s_%s"%(bookID,utteranceID))
      utteranceID += 1
