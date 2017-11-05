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

def get_lines(file):
    with open(file, "r", encoding="utf-8") as file:
        return [line for line in file]

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


#print(get_infobox_name_in_dutch("de", "Tony Blair"))

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


def get_common_pages(file_nl, file_de):
    with open(file_nl, encoding="utf-8") as file_nl, open(file_de, encoding="utf-8") as file_de:
        nl_data = get_data(file_nl)
        de_data = get_data(file_de)
    common_without_manipulation = set(nl_data.keys()) & set(de_data.keys())
    common_without_manipulation = set((item, item)for item in common_without_manipulation)
    common_with_manipulation_nl = get_common_pages_with_manipulation(nl_data, de_data, common_without_manipulation, "nl", "de")
    common_with_manipulation_de = get_common_pages_with_manipulation(de_data, nl_data, common_without_manipulation, "de", "nl")
    common_pages = common_with_manipulation_nl | common_with_manipulation_de  | common_without_manipulation# these are the ones that you can compare to add missing attributes

    return common_pages


def get_common_pages_with_manipulation(lang1, lang2, common_without_manipulation, lang_code_source, lang_code_target):
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
                    if lang_code_target == "nl": # als het DE - NL vertaling is draaien we de volgorde om voor consistentie over alle resultaten
                        common_with_manipulation.add((translation, k))
                    else:
                        common_with_manipulation.add((k, translation))



    return common_with_manipulation

def get_data(file):
    """ get data from file"""
    data = {}
    for line in file:
        if not line.startswith("#"):
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
            template = template_startindex = meta.find("template")
            template_endindex = meta.find("&", template_startindex)
            template = meta[template_startindex+9: template_endindex]
            if page_name in data:
                data[page_name]["page"].append(page)
                data[page_name]["attribute"].append(attr)
                data[page_name]["value"].append(val)
                data[page_name]["template"].append(template)
            else:
                data[page_name] = {}
                data[page_name]["page"] = []
                data[page_name]["page"].append(page)
                data[page_name]["attribute"] = []
                data[page_name]["attribute"].append(attr)
                data[page_name]["value"] = []
                data[page_name]["value"].append(val)
                data[page_name]["template"] = []
                data[page_name]["template"].append(template)

    return data

def normalize_value(value, target_lang):
    index_apestaartje = value.find("@")
    if index_apestaartje >= 0:
        value = value.replace(value[index_apestaartje:], "@" + target_lang)
    brackets_left = value.find("(")
    brackets_right = value.find(")")
    if brackets_left >= 0 and brackets_right >= 0 and brackets_right > brackets_left:
        if value[brackets_left-1] == " ":
            value = value.replace(value[brackets_left-1:brackets_right+1], "")
        else:
            value = value.replace(value[brackets_left:brackets_right+1], "")

    return value

def get_missing_quadruples(missing_data):
    lang = missing_data[0]
    missing_attributes = str(missing_data[1])
    ling_dict = missing_data[2]
    template = missing_data[3]
    page_lines_other_lang = missing_data[4]
    meta = missing_data[5]
    full_page_name = missing_data[6]
    if template in ling_dict:
        if missing_attributes != "NONE":
            for item in missing_attributes.split(","):
                item = item.strip()
                if item in ling_dict[template]:
                    translations_list = ling_dict[template][item]
                    for tup in translations_list:
                        if tup[0] == lang:
                            translation = tup[1]
                            corresponding_line_other_lang = next((x for x in page_lines_other_lang if x.split()[1].split("/")[-1][:-1] == item), None)
                            attr_english = corresponding_line_other_lang.split()[1]
                            val_other_lang = " ".join(corresponding_line_other_lang.split()[2:-2])
                            value = normalize_value(val_other_lang, lang)
                            property_begin = meta.find("property")
                            property_end = meta.find("&", property_begin)
                            meta = meta.replace(meta[property_begin:property_end], "property=" + translation)

                            new_quadruple = "{0} {1} {2} {3} {4}".format(full_page_name, attr_english, value, meta, ".")
                            with open("data1016/newquadruples.tql", "a+") as outfile:
                                outfile.write(new_quadruple)
                                outfile.write("\n")


def evaluation_step2(common_pages, ling_dict, lines_nl, lines_de):
    for nl_page, de_page in common_pages:
        page_lines_nl = [line for line in lines_nl if line.split()[0].split("/")[-1][:-1] == nl_page]
        page_lines_de = [line for line in lines_de if line.split()[0].split("/")[-1][:-1] == de_page]
        attributes_nl = sorted([line.split()[1].split("/")[-1][:-1] for line in page_lines_nl])
        attributes_de = sorted([line.split()[1].split("/")[-1][:-1] for line in page_lines_de])

        set_NL = set(sorted([line.split()[1].split("/")[-1][:-1] for line in page_lines_nl]))
        set_DE = set(sorted([line.split()[1].split("/")[-1][:-1] for line in page_lines_de]))

        meta_nl = page_lines_nl[0].split()[-2]
        meta_de = page_lines_de[0].split()[-2]
        full_page_nl = page_lines_nl[0].split()[0]
        full_page_de = page_lines_de[0].split()[0]
        template_startindex = meta_nl.find("template")
        template_endindex = meta_nl.find("&", template_startindex)
        template = meta_nl[template_startindex+9: template_endindex] # we gaan ervan uit dat voor de NL pagina's de template altijd hetzelfde is voor alle attributen (voor DE is dit niet altijd zo!)

        print("{0}{1}".format("template name: ", template))
        print("{0}\t\t{1}".format(nl_page, de_page))
        print()
        print("{0:<15}\t\t{1:>15}".format("Attributes NL", "Attributes DE"))
        print()
        for i, item in enumerate(attributes_nl):
            print("{0:<15}\t\t{1:>15}".format(item, attributes_de[i]))

        print()
        missing_dutch = set_DE.difference(set_NL)
        # x = input("Which Dutch attributes are missing that are present for GERMAN? FORMAT: NONE if none are missing, otherwise type attributes separated by commas (e.g. name, birthDate, age etc.):\n")
        print()
        missing_german = set_NL.difference(set_DE)
        # input("Which German attributes are missing that are present for DUTCH? FORMAT: NONE if none are missing, otherwise type attributes separated by commas (e.g. name, birthDate, age etc.):\n")
        print()

        #######################################################################

        for item in [("nl", missing_dutch, ling_dict, template, page_lines_de, meta_nl, full_page_nl), ("de", missing_german, ling_dict, template, page_lines_nl, meta_de, full_page_de)]:
            get_missing_quadruples(item)

if __name__ == "__main__":

    FILE_NL = "data1016/testeval_nl.tql"
    FILE_DE = "data1016/testeval_de.tql"
    with open(FILE_NL, encoding="utf-8") as f1, open(FILE_DE, encoding="utf-8") as f2:
        ## STEP 1: get all attribute translations
        translation_dict = build_multilingual_dict([("nl", f1), ("de", f2)])
        save_multiling_dict(translation_dict, "multilingdict_tiny.pickle")

        data = load_multiling_dict("multilingdict_tiny.pickle")
        print(data)

    ### STEP 2: get all matching pages in both languages and compare so you can add missing attributes
    common_pages = get_common_pages(FILE_NL, FILE_DE)
    nl_lines = get_lines(FILE_NL)
    de_lines = get_lines(FILE_DE)
    evaluation_step2(common_pages, data, nl_lines, de_lines)
