import shlex
from swt_project import get_infobox_name_in_dutch, get_translation, save_multiling_dict, load_multiling_dict, get_data, get_common_pages_with_manipulation
import re
import pickle
from collections import Counter

def get_lines(file):
    with open(file, "r", encoding="utf-8") as file:
        return [line for line in file]

def evaluation_step1(files, lang_dict=None):
    """attribute translation to dict
    attribute is list of (lang, file) tuples as parameter 1, parameter 2 is option in case you have stopped evaluation and want to use a temporary dictionary, please also 
    change the file if you do this > don't use the full file but the remainder of the file from where you stopped"""
    print("Welcome to evaluation step 1")
    print("You will get to see an english attribute name e.g. birthYear, and some meta-data, you will have to select the property value from the meta-data")
    print()
    if lang_dict:
        ling_dict = pickle.load(open(lang_dict, "rb"))
    else:
        ling_dict = {}
    for lang, file in files:
        with open(file, "r", encoding="utf-8") as infile:
            file_lines = [line for line in infile]
            for index, line in enumerate(file_lines):
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
                                meta = items[-2]

                    page_name = page.split("/")[-1][:-1]
                    attr_short = attr.split("/")[-1][:-1]
                    print("English attribute name: ", attr_short)
                    print("Find the translation in the metadata")
                    print(meta)
                    translation = input("Type the translation here: ")
                    if translation == "#EXIT":
                        save_multiling_dict(ling_dict, "data1016/temp.pickle")
                        with open("remainder_" + lang + ".tql", "w", encoding="utf-8") as outfile:
                            lines = [line for i, line in enumerate(file_lines) if i >= index]
                            for line in lines:
                                outfile.write(line)
                        print("Your work has been saved")
                        print("Thanks for your hard work, I'll see you later!")
                        return ling_dict
                    else:
                        print()
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


    save_multiling_dict(ling_dict, "data1016/evaluationdict.pickle")
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
    missing_attributes = missing_data[1]
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
                    translations = [item for language, item in translations_list if language == lang]
                    if translations:
                        most_common_translation = Counter(translations).most_common(1)[0][0]
                    
                        corresponding_line_other_lang = next((x for x in page_lines_other_lang if x.split()[1].split("/")[-1][:-1] == item), None)
                        attr_english = corresponding_line_other_lang.split()[1]
                        val_other_lang = " ".join(corresponding_line_other_lang.split()[2:-2])
                        value = normalize_value(val_other_lang, lang)
                        property_begin = meta.find("property")
                        property_end = meta.find("&", property_begin)
                        meta = meta.replace(meta[property_begin:property_end], "property=" + most_common_translation)
                            
                        new_quadruple = "{0} {1} {2} {3} {4}".format(full_page_name, attr_english, value, meta, ".")
                        print(new_quadruple)
                        with open("data1016/newquadruples_evaluation.tql", "a+", encoding="utf-8") as outfile:
                            outfile.write(new_quadruple)
                            outfile.write("\n")



def evaluation_step2(common_pages, ling_dict, lines_nl, lines_de):
    for nl_page, de_page in common_pages:
        page_lines_nl = [line for line in lines_nl if line.split()[0].split("/")[-1][:-1] == nl_page]
        page_lines_de = [line for line in lines_de if line.split()[0].split("/")[-1][:-1] == de_page]
        attributes_nl = sorted([line.split()[1].split("/")[-1][:-1] for line in page_lines_nl])
        attributes_de = sorted([line.split()[1].split("/")[-1][:-1] for line in page_lines_de])
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
        if len(attributes_nl) > len(attributes_de):
            for i, item in enumerate(attributes_de):
                print("{0:<15}\t\t{1:>15}".format(attributes_nl[i], item))
            for i in range(len(attributes_nl) - len(attributes_de)):
                print("{0:>15}".format(attributes_nl[i+len(attributes_de)]))
        else:
            for i, item in enumerate(attributes_nl):
                print("{0:<15}\t\t{1:>15}".format(item, attributes_de[i]))
            for i in range(len(attributes_de) - len(attributes_nl)):
                print("\t\t\t\t\t{0:>15}".format(attributes_de[i+len(attributes_nl)]))
        
        print()
        missing_dutch = input("Which Dutch attributes are missing that are present for GERMAN? FORMAT: NONE if none are missing, otherwise type attributes separated by commas (e.g. name, birthDate, age etc.):\n")
        print()
        missing_german = input("Which German attributes are missing that are present for DUTCH? FORMAT: NONE if none are missing, otherwise type attributes separated by commas (e.g. name, birthDate, age etc.):\n")
        print()
        for item in [("nl", missing_dutch, ling_dict, template, page_lines_de, meta_nl, full_page_nl), ("de", missing_german, ling_dict, template, page_lines_nl, meta_de, full_page_de)]:
            get_missing_quadruples(item)

        
        
FILES_NL = "../data1016/literals_nl_evaluation.tql"
FILES_DE = "../data1016/literals_de_evaluation.tql"


#ling_dict = evaluation_step1([("nl", FILES_NL), ("de", FILES_DE)])


data = load_multiling_dict("data1016/evaluationdictfinal.pickle")
#print(ling_dict)

common_pages = get_common_pages(FILES_NL, FILES_DE)
print(common_pages)
nl_lines = get_lines(FILES_NL)
de_lines = get_lines(FILES_DE)

evaluation_step2(common_pages, data, nl_lines, de_lines)



# code/postal code, foundation / founding year, 
# postal code / nick voor steden
# some never occur in both: flag, blazon NL, areaWater, areaTotal, areaLand DE
# gold list > postal code nickname, tennis tournaments

# TO: aanpassing swt > tuples
# run evaluation op swt