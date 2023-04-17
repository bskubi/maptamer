import requests
from bs4 import BeautifulSoup, SoupStrainer
import re
import os

#Extract individual aptamer targets and urls
#Uses url as key, target as value
page_title_abstract = {}
year_start = 1991
year_end = 2023
for year in range(year_start, year_end+1):
    files = os.listdir("./Pages/" + str(year))
    pages = 0
    for file in files:
        if ".html" in file:
            pages += 1
    for page in range(1, 1+pages):
        print(year, page)
        filename = './Pages/' + str(year) + "/" + str(page) + '.html'
        with open(filename, 'r') as f:
            contents = f.read()
            soup = BeautifulSoup(contents, 'html.parser')
            titles = []
            abstracts = []
            for title in soup.findAll(class_='ddmDocTitle'):
                title_text = title.text
                title_text = title_text.replace('\n', ' ')
                title_text = title_text.replace('\t', ' ')
                titles.append(title.text)
            for j in range(1, len(titles)):
                abstract_div = soup.find(id="previewAbstract"+str(j))
                abstract = abstract_div.find(class_="txt")
                if abstract is None:
                    abstract = abstract_div.text
                else:
                    abstract = abstract.text
                if abstract is not None:
                    abstract = abstract.replace('\n', ' ')
                    abstract = abstract.replace('\t', ' ')
                abstracts.append(abstract)

            title_abstract_pairs = []
            for i in range(0, len(abstracts)):
                title_abstract_pairs.append([titles[i], abstracts[i]])
            page_title_abstract[(year, page)] = title_abstract_pairs

with open("output.csv", "w", encoding="utf8") as f:
    f.write("Year\tPage\tTitle\tAbstract\n")
    keys = list(page_title_abstract.keys())
    keys.sort()
    for k in keys:
        for paper in page_title_abstract[k]:
            f.write(str(k[0]) + "\t" + str(k[1]) + "\t" + paper[0] + "\t" + paper[1] + "\n")

