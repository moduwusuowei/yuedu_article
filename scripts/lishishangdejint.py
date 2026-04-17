import requests
from faker import Factory
from lxml import etree

url = 'https://tool.lu/todayonhistory/'
headers = {
    'user-agent': Factory.create().user_agent()
}
html = requests.get(url=url,headers=headers)
# print(html.text)
tree = etree.HTML(html.text)
li_list = tree.xpath('//ul[@id="tohlis"]/li')
emjo_list = ['♠','♥','♣','♦']
i = 1
for li in li_list:
    emjo = emjo_list[i%4]
    title = li.xpath('./text()')[0]
    href = li.xpath('./a/@href')[0]
    print(emjo,title,href)
    i += 1
