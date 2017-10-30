# -*- coding: utf-8 -*-
# match property in english (e.g. Population total) with property name in 4th parameter = property, do this separately for each template
# for each template find matching pages in both languages, for each attribute (english) (with translations) check if one language has that attribute and the other doesn't, in this case you can add it in the missing language


import shlex
import requests 
import pickle
import re
from time import sleep

def save_multiling_dict(dict, file):
    pickle.dump(dict, open(file, "wb"))
    print("successfully saved dictionary")

def load_multiling_dict(file):
    return pickle.load(open(file, "rb"))

def get_translation(request, lang_code_source, lang_code_target):
    """ takes as parameters the dict with prop and titles, the lang code source and lang code target
    returns pagename in target language if found, otherwise empty string"""
    request['action'] = 'query'
    request['format'] = 'json'
    request["lllimit"] = 500
    try:
        result = requests.get('https://{}.wikipedia.org/w/api.php'.format(lang_code_source), params=request).json()
    except:
        print("Connection refused by the server..")
        print("ZZzzzz...")
        sleep(5)
        result = requests.get('https://{}.wikipedia.org/w/api.php'.format(lang_code_source), params=request).json()

    if 'error' in result:
        raise Error(result['error'])
    if 'warnings' in result:
        print(result['warnings'])
    if 'query' in result:
        for v in result["query"]["pages"].values():
            if "langlinks" in v:
                for item in v["langlinks"]:
                    if item["lang"] == lang_code_target:
                        return item["*"]
            else:
                return ""

def get_infobox_name_in_dutch(lang, page):
    """"parameters are the language of the source and the pagename
    first gets the dutch translation of the page
    then finds the infobox name based on that dutch page
    returns dutch infobox name if found, otherwise None"""
    page_nl = get_translation({'prop': 'langlinks', "titles":page}, lang, "nl")
    request = {}
    request['action'] = 'query'
    request['format'] = 'json'
    request["prop"] = "revisions"
    request["rvprop"] = "content"
    request["titles"] = page_nl
    request["rvsection"] = 0
    try:
        result = requests.get('https://nl.wikipedia.org/w/api.php', params=request).json()
    except:
        print("Connection refused by the server..")
        print("ZZzzzz...")
        sleep(5)
        result = requests.get('https://nl.wikipedia.org/w/api.php', params=request).json()

    if 'error' in result:
        raise Error(result['error'])
    if 'warnings' in result:
        print(result['warnings'])
    if 'query' in result: 
        for v in result["query"]["pages"].values():
            for key, val in v.items():
                if key == "revisions":
                    data = v["revisions"][0]["*"]
                    index_naambox = data.find("Infobox") # maybe change to {{Infobox
                    if index_naambox == -1:
                        return None
                    index_na_naambox = data.find("\n", index_naambox+8)
                    naam_box = data[index_naambox: index_na_naambox]
                    naam_box = naam_box.replace(" ", "_")
                    return naam_box
    else: 
        return None




def build_multilingual_dict(files):
    """ files is a list with tuples (lang, f1), (lang, f2) 
    for each line in a file we make sure we get the dutch infobox name which serves as key in ling_dict (if not, GERMAN.infoboxname is used)
    to ling_dict[dutchinfoboxname][attributename] we add the (lang, translation) tuple so we get the translation of the attribute and the language specifies the language of the translation
    returns a dict that for each template has attributes with their corresponding translations, as well as the german translation of the infobox if found (useful for later use)"""
    ling_dict = {}
    for lang, file in files:
        for line in file:
            if not line.startswith("#"):
                print(line)
                try:
                    page, attr, val, meta, period = shlex.split(line)
                except ValueError:
                    try:
                        page, attr, val, meta, period = re.findall(r'(?:"[^"]*"|[^\s"])+', line)
                    except ValueError:
                        if (line.find('""')) >= 0:
                            items = re.findall(r'(?:"[^"]*"|[^\s"])+', line)
                            page = items[0]
                            attr = items[1]
                            val = items[2:-2]
                            meta = items[-2]
                            period = items[-1]

                page_name = page.split("/")[-1][:-1]
                attr_short = attr.split("/")[-1][:-1] # last item minus >
                translation_startindex = meta.find("property")
                translation_endindex = meta.find("&", translation_startindex)
                translation = meta[translation_startindex+9: translation_endindex]
                template_startindex = meta.find("template") # get template name without template=, 
                template_endindex = meta.find("&", template_startindex)
                template = meta[template_startindex+9: template_endindex]
                if lang == "de":
                    translated_infobox = get_infobox_name_in_dutch(lang, page_name)
                    if translated_infobox != None:
                        template = translated_infobox
                    else:
                        template = "GERMAN." + meta[template_startindex+9: template_endindex]
                if template in ling_dict:
                    if attr_short in ling_dict[template]:
                        ling_dict[template][attr_short].append((lang, translation))
                    else:
                        ling_dict[template][attr_short] = [(lang, translation)]
                else:
                    ling_dict[template] = {}
                    ling_dict[template][attr_short] = [(lang, translation)] 
                if lang == "de" and not template.startswith("GERMAN."):
                    ling_dict[template]["translation_de"] = meta[template_startindex+9: template_endindex]

    return ling_dict




def get_common_with_manipulation(lang1, lang2, common_without_manipulation, lang_code_source, lang_code_target):
    """parameters: source_lang, target_lang, set of items that are already found without manipulation, lang_code source and lang_code target
    it checks if a page match (in both languages) was already found with common_without_manipulation, if not it gets the translation from source to target
    if this translation is found in the pages of target_language, it is converted to proper format and added to common_with_manipulation
    returns the set common_with_manipulation"""
    common_with_manipulation = set()
    for k, v in lang1.items():
        if k in common_without_manipulation:
            pass 
        else:
            translation = get_translation({'prop': 'langlinks', "titles":k}, lang_code_source, lang_code_target)
            if translation:
                translation = translation.replace(" ", "_")
                if translation in lang2.keys():
                    print(translation)
                    common_with_manipulation.add(translation)
            
                    

    return common_with_manipulation

def get_data(file):
    """ TO DO: add translation step for German template name  """
    data = {}
    for line in file:
        if not line.startswith("#"):
            print(line)
            #print(shlex.split(line))
            page, attribute, value, metadata, period = shlex.split(line)
            page_name = page.split("/")[-1][:-1]
            template = template_startindex = meta.find("template") 
            template_endindex = meta.find("&", template_startindex)
            template = meta[template_startindex+9: template_endindex]
            if page_name in nl_data:
                data[page_name]["page"].append(page)
                data[page_name]["attribute"].append(attribute)
                data[page_name]["value"].append(value)
                data[page_name]["template"].append(template)
            else:
                nl_data[page_name] = {}
                nl_data[page_name]["page"] = []
                nl_data[page_name]["page"].append(page)
                nl_data[page_name]["attribute"] = []
                nl_data[page_name]["attribute"].append(attribute)
                nl_data[page_name]["value"] = []
                nl_data[page_name]["value"].append(value)
                nl_data[page_name]["template"] = []
                nl_data[page_name]["template"].append(template)

    return data

with open("data1016/literals_nl_short.tql", encoding="utf-8") as f1, open("data1016/literals_de_short.tql", encoding="utf-8") as f2:
    ## STEP 1: get all attribute translations

    translation_dict = build_multilingual_dict([("nl", f1), ("de", f2)])
    save_multiling_dict(translation_dict, "multilingdict_short.pickle")

    data = load_multiling_dict("multilingdict_short.pickle")
    print(data)


    ### STEP 2: get all matching pages in both languages and compare so you can add missing attributes
    # nl_data = get_data(f1)
    # de_data = get_data(f2)
    # common_without_manipulation = set(nl_data.keys()) & set(de_data.keys())
    #common_with_manipulation_nl = get_common_with_manipulation(nl_data, de_data, common_without_manipulation, "nl", "de")
    #common_with_manipulation_de = get_common_with_manipulation(de_data, nl_data, common_without_manipulation, "de", "nl")
    #common_pages = common_with_manipulation_nl | common_with_manipulation_de # these are the ones that you can compare to add missing attributes

