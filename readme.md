# Semantic Web Project

# Steps that are already done:
1. Create multilingual dictionary that has templates as keys, and within each template dict, attributes as keys with a list of translations for that attribute in nl and de 
2. Function that gets the data and checks for identical pagenames in nl and de, returns the set common_without_manipulation
3. Function that takes the data and for all articles that didn't have identical pagenames, translates pagename from lang1 to lang2 and checks if translation is in lang2 keys
   If it is found, it is added to a set of all common pagenames that are found with this manipulation (common_with_manipulation)
4. Combine the sets common_without_manipulation and common_with_manipulation into common_pages

# Steps to be implemented
5. Write function that iterates over common_pages and finds those pages in nl_data and de_data, check out the attributes of those pages and find missing attributes for either NL or DE
6. In the multilingual dictionary, have a look at the translations of the attributes in each template and only keep those translations that occur more than 3 (?) times
7. Look up the attribute names of step 5 in the multilingual dictionary to find the translation (Naam found for NL > search DE > Name == DE)
8. Map the value from source to target language (Naam/Name attribute NL-DE found in step 6) (John Smith as value for NL), map John Smith to DE > result for DE Name John Smith
9. Put it all together into a quadruple
10. Count number of new quadruples
11. Do evaluation on test set

# Potential issues
1. The values might need to be translated (years and names usually not, but for example names of paintings are usually translated: De Nachtwacht, The Nightwatch etc. etc. )



NOTE: in the repo the shorter files are included (literals_nl_short literals_de_short literals_nl_excerpt literals_de_excerpt), use these to test the system, the other files 
which are too big to be included in the repo, are only for running complete working system (takes way too long otherwise)
the files the shorter ones are based on are: mappingbased_literals_de.tql mappingbased_literals_nl.tql from a dump dating from October 2016
there are also mappingbased_objects_nl (and de) which we can also use
NOTE2: we already have pickle files for literals short and literals excerpt, use these to load the multilingual dictionary (faster)