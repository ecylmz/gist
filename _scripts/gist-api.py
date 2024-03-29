#!/usr/bin/python
#-*- coding:utf-8 -*-


import requests
import json
import os
import read_config
from htmltmpl import TemplateManager, TemplateProcessor

GIST_API_MAIN_URL = "https://api.github.com/users/"

def fetch_gists_data(user):
    """Sadece github'tan json verisini alır ve veriyi döner."""
    gist_raw_data = requests.get(GIST_API_MAIN_URL+user+"/gists").content
    gist_data = json.loads(gist_raw_data)
    return gist_data

def fetch_label(user):
    """Etiketleme sistemini yapar. Gist sayısı kadar dolaşır ve [ ]
    paternini arar. 'etiket:id' ve 'id:açıklama' sözlüklerini döner.
    """
    gist_data = fetch_gists_data(user)
    gist_count = len(gist_data)
    descriptions = {}
    id_map = {}
    for i in range(gist_count):
        use_label =  unicode(gist_data[i]["description"])
        use_label = use_label.encode("utf-8")
        use_label = str(use_label)
        description = use_label
        label_id = gist_data[i]['id']
        if use_label != '' and use_label != "None":
             use_label = use_label[use_label.index('[') + 1:use_label.index(']')].split(" ")
             for j in range(len(use_label)):
                 if use_label[j] not in id_map:
                     id_map[use_label[j]] = []
                 id_map[use_label[j]].append(int(label_id))
                 descriptions[int(label_id)] = description
    return {'id_map': id_map, 'descriptions' : descriptions}

user = read_config.ConfigSectionMap('user')['name']
LABEL_DATA = fetch_label(user)
main_path = read_config.ConfigSectionMap('user')['main_path']
os.chdir(main_path)

def git_submodule():
    """gistleri submodule olarak master dalına ekler."""
    id_map = LABEL_DATA['id_map']
    os.system("git checkout master")
    for i in range(len(id_map.keys())):
        for j in range(len(id_map[id_map.keys()[i]])):
            os.system("git submodule add git://gist.github.com/%d.git %d" %
                      (id_map[id_map.keys()[i]][j],id_map[id_map.keys()[i]][j]))
    os.system("git commit -a -m 'güncellendi.'")

def sub_page():
    """Her etiket için ayrı bir index.html sayfa üretir."""
    template = TemplateManager().prepare(main_path + "/_scripts/templates/sub_template.tmpl")
    tproc = TemplateProcessor()
    gists = []
    id_map = LABEL_DATA['id_map']
    description = LABEL_DATA['descriptions']
    for i in range(len(id_map.keys())):
        if not os.path.exists(main_path + id_map.keys()[i]):
            os.mkdir(id_map.keys()[i])
    for label in id_map.keys():
        os.chdir(main_path + label)
        gist = {}
        if len(id_map[label]) == 1:
            gist["label"] = label
            gist["id"] = id_map[label][0]
            gist["description"] = description[id_map[label][0]]
            gists.append(gist)
        else:
            for i in range(len(id_map[label])):
                gist = {}
                gist["label"] = label
                gist["id"] = id_map[label][i]
                gist["description"] = description[id_map[label][i]]
                gists.append(gist)
        tproc.set("labels", label)
        tproc.set("Gists", gists)
        content = tproc.process(template)
        f = open("index.html","w")
        f.write(content)
        f.close()
        gists = [] # gists'i sıfırla, çünkü her depo için farklı etiketli gistler var.
        os.system("git add index.html")
        os.system("git commit -a -m 'güncellendi.'")

def main_page():
    """Ana sayfa için index.html sayfası hazırlar."""
    os.system("git checkout gh-pages")
    template = TemplateManager().prepare(main_path + "/_scripts/templates/main_template.tmpl")
    tproc = TemplateProcessor()
    gists = []
    id_map = LABEL_DATA['id_map']
    for label in id_map.keys():
        gist = {}
        gist["label"] = label
        gist["sum_label"] = len(id_map[label])
        gists.append(gist)
    tproc.set("Gists", gists)
    content = tproc.process(template)
    f = open("index.html","w")
    f.write(content)
    f.close()
    os.system("git add index.html")
    os.system("git commit -a -m 'güncellendi.'")
    sub_page()

if __name__ == '__main__':
    git_submodule()
    main_page()
