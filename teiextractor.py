import sys
import xml.etree.ElementTree as ET


class Utterance():
  def __init__(self,unsegmentedwords, glosses):
    self.unsegmentedwords = unsegmentedwords
    self.glosses = glosses 
    self.segmentedwords = []
    self.joiners = [] #there is only one joiner per word for this use case
    for i,w in enumerate(unsegmentedwords):
      joiner = ''
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
    print("u%s: a ligt:Utterance"%ID)
    self._wordtierRDF(ID,self.unsegmentedwords,ID)
    self._morphemetierRDF(i,self.segmentedwords,glosses,ID)
    
  def _wordtierRDF(self,number,tier,parent):
    print("\n:wt%s a wordtier;"%number)
    print(' partof :u%s;'%parent)
    print(' rdfs:label "%s."'%' '.join(tier))
    for i,word in enumerate(tier):
      print("\n:w%s.%s a word;"%(number,i))
      print('       rdfs:label "%s".'%word)
    
  def _morphemetierRDF(self,number,segmentedwords,glosses,parent):
    print("\n:mt%s a morphemetier;"%number)
    print("        olia:hasParent u%s;"%parent)
    print('        rdfs:label "%s";'%"xyz")
    ID = "mt%i"%number 
    for wordnumber,gloss in enumerate(glosses):
        if gloss['grammaticalgloss'] == '': #monomorphemic
          print("\n:mt%sm%s.0 a morpheme;"%(parent,wordnumber))
          print("  partof :mt%s;"%number)
          print('  label "%s"@sk ;'%self.segmentedwords[wordnumber])
          print('  label "%s"@en ;'%gloss['lexicalgloss'])
          print('  next :mt%sm%s.%s .'%(parent,wordnumber+1,0))
        else:
          try:
            stem,suffix = self.segmentedwords[wordnumber].split('-') #bimorphemic segmentable
            print("\n:mt%sm%s.0 a morpheme;"%(parent,wordnumber))
            print("  partof :mt%s;"%number)
            print('  label "%s"@sk ;'%stem)
            print('  label "%s"@en ;'%gloss['lexicalgloss'])
            print('  next :mt%sm%s.%s .'%(parent,wordnumber,1))
          
            print("\n:mt%sm%s.1 a morpheme;"%(parent,wordnumber))
            print("  partof :mt%s;"%number)
            print('  label "%s"@sk ;'%suffix)
            print('  label "%s"@en ;'%gloss['grammaticalgloss'])
            print('  next :mt%sm%s.%s .'%(parent,wordnumber+1,0))
          except ValueError:  #bimorphemic non-segmentable
            print("\n:mt%sm%s.0 a morpheme;"%(parent,wordnumber))
            print("  partof :mt%s;"%number)
            print('  label "%s"@sk ;'%segmentedwords[0])
            print('  label "%s"@en ;'%"%s.%s"%(gloss['lexicalgloss'],gloss["grammaticalgloss"]))
            print('  next :mt%sm%s.%s .'%(parent,wordnumber+1,0))
          
            
      
    
  
  def toRDF(self,ID):
    self._utteranceRDF(ID)
    

filename = sys.argv[1]

tree = ET.parse(filename)
root = tree.getroot()

lgs = root.findall(".//{http://www.tei-c.org/ns/1.0}lg")
print(len(lgs))
print("Preamble")
print("%s a document;")
for lg in lgs: 
  ls = lg.findall("{http://www.tei-c.org/ns/1.0}l")  
  #ls = lg.findall("{http://www.tei-c.org/ns/1.0}l[string(@ana)='']")
  full_ls = ls[::2] #<l>s which contain the full line with all words
  ls_with_fs = ls[1:][::2] #<l>s with have <f>s
  lpairs = zip(full_ls,ls_with_fs)
  utteranceID=0
  for lpair in lpairs: 
    full = lpair[0]
    gra_lemma= lpair[1].findall(".//{http://www.tei-c.org/ns/1.0}f[@name='gra_lemma']/{http://www.tei-c.org/ns/1.0}string")
    morphosyntax = lpair[1].findall(".//{http://www.tei-c.org/ns/1.0}f[@name='morphosyntax']")
    imt = zip(gra_lemma, morphosyntax)
    unsegmentedwords = full.text.strip().split()
    glosses = []
    for i,item in enumerate(imt):
      grammaticalgloss = None
      lexicalgloss = item[0].text.strip().replace(' ~ ','~').replace('-','')
      try:
        #collect all morphosyntactic categories
        grammaticalgloss = '.'.join([el.attrib['value'] for el in item[1].findall('.//{http://www.tei-c.org/ns/1.0}symbol')])
      except AttributeError:
        pass 
      glosses.append({'lexicalgloss':lexicalgloss,'grammaticalgloss':grammaticalgloss}) 
    if glosses != []:      
      u = Utterance(unsegmentedwords,glosses)
      u.toRDF(utteranceID)
      utteranceID += 1
