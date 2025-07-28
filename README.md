# Your AI Lawyer

### instalare ollama ###

  curl -fsSL https://ollama.com/install.sh | sh

### instalare mistral 7B (just enough pentru rulare locala) ###

  ollama run mistral

### structra ###

  scraper.py 
  |_ scrapeuieste siteuri legislative (lege5, legislatie.just, ansvsa, anpc etc)
  
  search.py
  |_ cauta cele mai relevante legi conform promptului
  
  main.py
  |_ impune context pentru LLM
  |_ trimite textul scrapeuit catre LLM si asteapta raspuns
  |_ afiseaza litere si alineate de lege

