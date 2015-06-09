#!/usr/bin/env python2


import argparse  
import socket
import select
import sys
import signal

class IRCClient:

# parsovani argumentu 
# vytvoreni parseru a jeho pouziti pri spatnem zadani parametru   
    parser = argparse.ArgumentParser(add_help=False, 
    usage='\n Program je nutne spustit s nasledujicimi  parametry\n:'
            ' {-l|-w} -h <host> [-p <port>] [-c <channel>]\n'
            ' kde:\n'  
            '      -l je listening mod\n' 
            '      -w je writinig mod\n '
            '          jeden z techto dvou parametru je POVINNY\n'
            '      -h <host> kde <host> je nazev serveru a je POVINNY \n'
            '      -p <port> kde <port> je cislo portu serveru a je NEPOVINNY\n'
            '          pokud port neni zadan je defaultne nastaven na 6667\n'
            '      -c <channel> kde <channel> je nazev kanalu kam se pripojit a je NEPOVINNY\n'
            '          pokud kanal neni zadan tak se pripoji jen na server\n'     
    )
    # vyuziti groupy pro listening nebo writing mod  - tento argument je povinny   
    group = parser.add_mutually_exclusive_group(required=True)
    #listening mod    
    group.add_argument(    
        '-l',
        action='store_true'
    )
    # writing mod    
    group.add_argument(    
        '-w',
        action='store_true'
    )
    # host
    parser.add_argument(
        '-h',
        required=True,    # tento argument je povinny 
    )
    # port    
    parser.add_argument(
        '-p',
        default=6667,     # nastavim si defaultne port na 6667
        type=int,
    )
    # channel    
    parser.add_argument(
        '-c',
        default=None,     # defaultne bude none
    )
        
    args = parser.parse_args()    
    
    # vytahnu si svoje parametry       
    listening_mod =  args.__dict__["l"] #vraci true pokud byl nastaven
    writing_mod =  args.__dict__["w"]   #vraci true pokud byl nastaven
    arg_host = args.__dict__["h"]   
    arg_port = args.__dict__["p"]
    channel = args.__dict__["c"] 
        
    
    # nadefinuju si funkci posilani "obsahu", kterou budu vyuzivat v celem kodu 
    def send(self, obsah):
        self.sock.send(obsah+"\r\n")
    
    # nadefinuju si odeslani join serveru 
    def join(self):
        #pokud nebyl nastaven kanal tak se nic nestane - nebude se joinovat
        if self.channel != None: 
           self.send("JOIN %s" % self.channel)
    
    # odchytavam si signaly SIGINT a SIGTERM
    def signal_handler(signal, frame):
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
       
    # promenne se kteryma pracuju
    sock = None
    nickname = 'xjurik08'
    readbuffer = ""
    # pomocna promena names_nastaven, ktera mi pomuze pri reseni joinu ktery vypisoval primarne i zpravu NAMES
    names_nastaven = 0
    
    
    def __init__(self):
            self.sock = socket.socket()
            self.sock.settimeout(6) 
            try:
              self.sock.connect((self.arg_host, self.arg_port))
              self.send("NICK %s" % self.nickname)
              self.send("USER %(nick)s %(nick)s %(nick)s :%(nick)s" % {'nick':self.nickname})
              self.join()        
            except Exception, e:
              sys.stderr.write("Nepodarilo se pripojit k serveru\n")
              exit()              
              
            
            
        
#************************************************************************************
#     WRITING MOD    
#     pokud byl nastaven writing mod tak zacnem
#     v tomto kousku kodu vyuziju funkci select ktera se bude rozhodovat co obslouzi
#     pokud driv prisel socket s nejakou zpravou tak ji vypisu
#     pokud jsem vsak byl rychlejsi na prikazove radce tak prvni obslouzi muj prikaz
    
            if self.writing_mod==True:
                while True: 
                  #nadefinuju si select ktery mi bude obshluhovat bud prichozi sockety nebo prikazovou radku(odchozi)
                  sockets = [sys.stdin,self.sock]
                  readsocks, writesocks, errsocks = select.select(sockets, [], [])
                  for so in readsocks:    
                    if so == self.sock:
                        # zpracovani socketu
                        self.readbuffer=self.readbuffer+self.sock.recv(1024)
                        temp=self.readbuffer.split("\n")
                        self.readbuffer=temp.pop( )  # posledni nemusi prijit cela, proto pop
                                          
                        for data in temp:
                            data = str(data).strip()
            
                            if data == '':
                                continue
                            #print data
                            
                            # data si nasplituju od 3. mezery
                            # od treti protoze v mem zadani vyuziju vse az od prave teto mezery                                    
                            coming = data.split(" ",3) 
                                                                                                     
                            # pokud je na prvnim miste zpravy PING tak se me server pta jestli ziju
                            if coming[0] == "PING":
                              n = data.split(':')[1]
                            # odpovidam PONG - ano ziju
                              self.send('PONG :' + n)                               
                            # nyni si budu tisknout na zaklade toho co mi prislo 
                            elif coming[1] == "353":            #/names  NAMES zprava
                              if self.names_nastaven == 1:      # pokud byla poslano NAMES (po odeslani zpravy bylo nastaveno = 1 viz.nize)
                                name_list = data.split(":",2)   # split od druheho vyskytu dvojtecky - muj list s jmenama
                                print name_list[2]              # tak si seznam jmen vypisu
                                self.names_nastaven = 0         # a nastavim si names opet na 0 (bude probihat cyklus)
                            elif coming[1] == "311":            #/whois  WHOIS zprava
                              print coming[3]
                            elif coming[1] == "319":            #/whois
                              print coming[3]
                            elif coming[1] == "312":            #/whois
                              print coming[3]
                            elif coming[1] == "318":            #/whois
                              print coming[3]
                            elif coming[1] == "322":             #/list   
                            # potrebuju list dle zadani bez dvojtecky
                              list_upr = coming[3].split(":",1)
                              list_upr = ' '.join(list_upr) 
                              print list_upr 
                            # odchytim si aspon par chyb na ktere jsem narazil
                            # ostatni chyby - tedy alespon ty zakladnejsi jsem osetril behem psani
                            elif coming[1] == "401":
                              sys.stderr.write("ERROR - kanal nebo nick neexistuje\n")
                            elif coming[1] == "404":
                              sys.stderr.write("ERROR - nelze odeslat zpravu kanalu\n")
                    
                    # ************************************************************************                                                      
                    # zde je obsluha pro stdin 
                    # pokud jsem neco napsal a nasledne potvrdil na mem stdinu tak me obslouzi          
                    elif so == sys.stdin:
                        # ulozim si co jsem napsal
                        my_in = sys.stdin.readline()
                        if my_in == "\n":      #pokud jen mackam enter tak pokracuj
                          continue
                        else:                    
                          # rozdelim si do pomocne mou zpravu
                          pomocna = my_in.split(" ")
                          # kdyby byl napsany jen 1 prikaz tak si odstranim \n
                          prvni = pomocna[0]
                          prvni = prvni.rstrip('\n')
                          # pokud prvni znak neni lomeno
                          # tak je to dobra <sprava> protoze si celou spravu muzu
                          # opet spojit a celou ji odeslat kanalu jako PRIVMSG
                          if prvni[:1] !="/":
                            sprava =  ' '.join(pomocna)
                            self.send("PRIVMSG %s :%s" % (self.channel, sprava))                                            
                          # jinak prvni znak byl / a ja zacnu rozlisovat co je na stdinu  
                          else:
                            # ********************************************************                
                            # pokud jsou zadany 2 nebo vice parametru
                            # ******************************************************** 
                            if len(pomocna) >=2:                   
                                if  prvni == "/quit":               # quit musi musi met 2 a vic
                                    pomocna =  ' '.join(pomocna)    # spojim si muj text mezerama
                                    pomocna = pomocna.split(" ",1)  # a rozdel mi od 1 mezery na elementy                                        
                                    pomocna = pomocna[1:]           # odstranim si prvni 2 elementy v listu                    
                                    zprava = pomocna[0]             # a ziskavam svou zpravu
                                    zprava = zprava.strip('\n')
                                    self.send("QUIT :%s" % zprava)
                                    exit()                          # vypnu   
                                elif len(pomocna) == 2:             # presne 2 parametry ma JOIN, NAMES a WHOIS
                                  druhy = pomocna[1]
                                  druhy = druhy.rstrip('\n')
                                  # pokud je na prvnim miste /join
                                  # tak si zkontroluju jestli nahodou neni kanal None
                                  # kdyz je None tak kanal nebyl zadan jako argument programu ale
                                  # byl zadan az nyni v stdinu pri writing modu 
                                  if  prvni == "/join":
                                    if self.channel == None:
                                      if druhy[:1] !="#":           # casta chyba, kanal musi byt zadavan s #
                                        sys.stderr.write("ERROR - byl zadan spatne kanal - bez #\n")
                                      else:                                         
                                        self.channel = druhy
                                        self.send("JOIN %s" % self.channel)
                                    # pokud ale byl zadany tak se z nej odpojim a pripojim se 
                                    # na prave zadany kanal ve writing modu a zaroven si tento kanal
                                    # ulozim pro dalsi pruchod   
                                    else:
                                     if self.channel != None:
                                      self.send("PART %s" % self.channel )   # odchazim
                                      self.send("JOIN %s" % druhy )          # joinuji se
                                      self.channel = druhy
                                  # pokud byl zadany /names tak si do pomocne names_nastaven ulozim 1
                                  # a pote poslu zpravu NAMES s parametrem kanal    
                                  elif  prvni == "/names":
                                    self.names_nastaven = 1    
                                    self.send("NAMES %s" % druhy)
                                  # pokud byl zadany /whois tak poslu zpravu WHOIS s parametrem kanal
                                  elif  prvni == "/whois":
                                    druhy = pomocna[1]
                                    self.send("WHOIS %s" % druhy)
                                  # v ostatnich pripadech mi vypis chybu
                                  else:
                                    sys.stderr.write("ERROR - chybne zadany parametry\n")
                                elif len(pomocna) >= 3:             # tri a vice parametru 
                                  if prvni == "/msg":
                                    druhy = pomocna[1]              # ulozim si druhy parametr - komu odesilam                  
                                    pomocna =  ' '.join(pomocna)    # spojim si muj text mezerama
                                    pomocna = pomocna.split(" ",2)  # a rozdel mi od 2 mezery na elementy                                        
                                    pomocna = pomocna[2:]           # odstranim si prvni 2 elementy v listu                    
                                    zprava = pomocna[0]             # konecne moje cela "zprava" pro /msg                                                                                                                                               
                                    self.send("PRIVMSG %s :%s" % (druhy, zprava))
                                  else:
                                    sys.stderr.write("ERROR - chybne zadany parametry\n")
                                     
                            # ********************************************************
                            #        pokud je zadany 1 parametr
                            # ********************************************************  
                            # muze jednat jen o CLOSE a LIST                        
                            elif len(pomocna) == 1:
                              if prvni == "/close":
                                  if self.channel == None:
                                    sys.stderr.write("ERROR - Nelze se odpojit z kanalu protoze na zadnem nejsem\n")
                                  else:
                                    # jsem v kanalu a posilam zpravu PART ze odchazim
                                    self.send("PART %s" % self.channel)
                                    self.channel = None
                              elif prvni == "/list":
                                  self.send("LIST")
                              # jinak mi vypis chybu
                              else:
                                sys.stderr.write("ERROR - chybne zadany parametry\n")                                 
                            else:
                              sys.stderr.write("ERROR - chybne zadany parametry\n")                             
                                                         
#************************************************************************************
#     LISTENING MOD    
#     pokud byl nastaven listening mod
#     v tomto kousku kodu si jen parsuju zpravy NOTICE a PRIVSMG  dle zadani 
            
            elif self.listening_mod == True: 
                while True:
                  sockets = [sys.stdin,self.sock]
                  readsocks, writesocks, errsocks = select.select(sockets, [], [])
                  for so in readsocks:    
                    if so == self.sock: 
                        self.readbuffer=self.readbuffer+self.sock.recv(1024)
                        temp=self.readbuffer.split("\n")
                        self.readbuffer=temp.pop()    
                                              
                        for data in temp:
                            data = str(data).strip()
            
                            if data == '':
                                continue
                            #print data
                                                                 
                            coming = data.split(" ",3)    # rozdeluji od 3 mezery - data ktere budu potrebovat
                            
                            if coming[0] == "PING":       # PING zprava
                                n = data.split(':')[1]
                                self.send('PONG :' + n)
                            elif ((coming[1] == "PRIVMSG") or (coming[1] == "NOTICE")):                    
                                #zpracuju si zpravu
                                odesilatel = coming[0][1:]
                                parse_nick = odesilatel.split("!") # rozdelim si podle "!" abych si vytahl odesilatele
                                odesilatel = parse_nick[0]                
                                komu = coming[2]
                                obsah_zpravy  = coming[3][1:]
                                                      
                                #tisknu si zpravu ve spravnem formatu
                                print komu+':'+odesilatel+':'+obsah_zpravy  

    
client = IRCClient()
