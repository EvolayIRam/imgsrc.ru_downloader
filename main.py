import sqlite3
import re
import time as tm
from bs4 import BeautifulSoup
import requests
import os
from datetime import datetime



url = "https://imgsrc.ru/cat/25-priroda.html"
payload = {}
headers = {
    'Cookie': ''
}
response = requests.request("GET", url, headers=headers, data=payload)
soup = BeautifulSoup(response.text, features="lxml")


# try:
for tr in soup.find_all('tr')[2:]:
    tds = tr.find_all('td')

    #print(tds[0])
    if tds[0].find('a') is None:
        print('All done')
        break
    href_dirty = ((tds[0].find('a')).get('href'))  # href

    href = re.sub("^\s+|\n|\r|\s+$", '', href_dirty)
    if "?preword=show" in href:
        href = href.replace('?preword=show', '')
        print('Очищенная ссылка: ',href)
    href_text = "".join(c for c in href if c.isalpha())
    autdesc_dirty = tds[0].find('a').text  # author and desc
    autdesc = re.sub("^\s+|\n|\r|\s+$", '', autdesc_dirty)
    section = tds[1].text  # section
    num = tds[2].text  # num photos
    views = tds[3].text  # views
    votes = tds[4].text  # votes
    comments = tds[5].text  # comments
    modifieded = tds[6].text  # modifieded

    current_datetime = datetime.now()

    href_sql = {
        'href': href,
        'autdesc': autdesc,
        'section': section,
        'num': num,
        'views': views,
        'votes': votes,
        'comments': comments,
        'modifieded': modifieded,
        'added': current_datetime,
    }



    with sqlite3.connect('db.db') as connection:
        cursor = connection.cursor()
        cursor.execute("""
                SELECT href FROM imgsrc WHERE href = (?)
                """, (href,))
        result = cursor.fetchone()
        if result is None:

            cursor.execute("""
                                 INSERT INTO imgsrc VALUES
                                     (NULL, :href, :autdesc, :section, :num, :views, :votes, :comments, :modifieded,:added)
                                 """, href_sql)
            connection.commit()




            text = f"""
Ссылка: {'https://imgsrc.ru' + href}
Автор и название: {autdesc}
Раздел: {section}
Кол-во фотографий: {num}
Просмотры: {views}
Голоса: {votes}
Комментариев: {comments}
Изменение: {modifieded}
                    """
            # print(text)
            chat_id = ''
            TOKEN = ''
            url_bot = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'}
            response = requests.post(url=url_bot, data=data)
            print('Telegramm server response:',response)
            tm.sleep(2)


            if not os.path.isdir(f'images/{href.replace("/", "#").replace(".html", "")}'):
                os.mkdir(f'images/{href.replace("/", "#").replace(".html", "")}')  # создаю папку
                url = ('https://imgsrc.ru' + href)
                print('Downloading url:',url)
                endstring = "user.php"
                finished = False
                while not finished:
                    result = requests.get(url)
                    soup = BeautifulSoup(result.content, "html.parser")
                    element_by_id = soup.find("a", {"id": "next_url"})
                    if endstring in url:
                        finished = True
                    else:
                        next_image = element_by_id.get("href")
                        find_image = element_by_id.find("img")
                        current_image = find_image.get("src")
                    url = "https://imgsrc.ru" + next_image
                    dl_image = "https:" + current_image
                    if finished:
                        break
                    image_name = dl_image.split("/")[-1]
                    response = requests.get(dl_image)
                    if response.status_code:
                        with open(f'images/{href.replace("/", "#").replace(".html", "")}/{image_name}', 'ab') as file:
                            file.write(response.content)
