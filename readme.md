# Semantic Web Project

# Steps that are already done:
1. Create multilingual dictionary that has templates as keys, and within each template dict, attributes as keys with a list of translations for that attribute in nl and de 
2. Function that gets the data and checks for identical pagenames in nl and de, returns the set common_without_manipulation
3. Function that takes the data and for all articles that didn't have identical pagenames, translates pagename from lang1 to lang2 and checks if translation is in lang2 keys
   If it is found, it is added to a set of all common pagenames that are found with this manipulation (common_with_manipulation)
4. Combine the sets common_without_manipulation and common_with_manipulation into common_pages

# TO DO
5. AUTOMATISEER INPUT MISSING DATA NL EN MISSING DATA DE (dus: welke wel in NL en niet in DE en welke wel in DE en niet in NL voor pagina X)
6. in functie get_missing_quadruples stel een minimaal aantal 'occurrences' van tuple vertaling dus > ("de", "NAME") minimaal 3 keer ofzo
7. Count number of new quadruples in official data
8. Do evaluation on test set, compare automatically with manually generated quadruples + automatically  / manually generated dictionary
9. Write report (literature :( ))
10. Prepare presentation

# Potential issues
1. The values might need to be translated (years and names usually not, but for example names of paintings are usually translated: De Nachtwacht, The Nightwatch etc. etc. )



NOTE: in the repo the shorter files are included (literals_nl_short literals_de_short literals_nl_excerpt literals_de_excerpt), use these to test the system, the other files 
which are too big to be included in the repo, are only for running complete working system (takes way too long otherwise)
the files the shorter ones are based on are: mappingbased_literals_de.tql mappingbased_literals_nl.tql from a dump dating from October 2016
there are also mappingbased_objects_nl (and de) which we can also use
NOTE2: we already have pickle files for literals short and literals excerpt, use these to load the multilingual dictionary (faster)


