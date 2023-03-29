from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


def kyochonUrl(sido1=0, sido2=0, txt=""):
    """
    교촌 시/도별 가맹점 검색 url
    :param sido1: 시/도 번호 (int)
    :param sido2: 군/구 번호 (int)
    :param txt: 검색 키워드 (string)
    :return: 교촌 시/도별 가맹점 검색 url (string)
    """
    return f"https://www.kyochon.com/shop/domestic.asp?sido1={sido1}&sido2={sido2}&txtsearch={txt}"


def kyochonLocationDataUrl(sido="sido"):
    """
    교촌 시/도 데이터 파일 url
    :param sido: 지역 이름 - 영문 (string)
    :return: 교촌 시/도 데이터 파일 url (string)
    """
    return f"https://www.kyochon.com/common/xml/district/{sido}.xml"


def translateLocation(location):
    """
    지역 이름 번역
    :param location: 지역 이름 - 한글 (string)
    :return: 지역 이름 - 영문 (string)
    """
    translate_dict = {'서울': 'seoul', '부산': 'busan', '대구': 'daegoo', '인천': 'incheon', '광주': 'gwangjoo',
                      '대전': 'daejeon', '울산': 'woolsan', '세종': 'sejong', '경기': 'gyeongi', '강원': 'gangwon',
                      '충북': 'choongbook', '충남': 'choongnam', '전북': 'jeonbook', '전남': 'jeonnam', '경북': 'gyeongbook',
                      '경남': 'gyeongnam', '제주': 'jeju'}
    return translate_dict[location]


def xmlDataParsing(url, tag):
    """
    xml의 data를 parsing
    :param url: 사이트의 url (string)
    :param tag: parsing 할 tag (string)
    :return: parsing한 데이터의 텍스트 (list(string))
    """
    xmlFile = urllib.request.urlopen(url).read().decode('utf-8')
    soup = BeautifulSoup(xmlFile, 'html.parser')
    return [t.text for t in soup.find_all(tag)]


def htmlParsing(url, tag, attrs={}, children=[]):
    """
    html의 data를 parsing
    :param url: 사이트의 url (string)
    :param tag: parsing 할 tag (string)
    :param attrs: parsing 할 tag의 속성 값 (dict(string: string))
    :param children: parsing 할 tag의 자식의 tag (list(string))
    :return: children 값을 주었을 때, [{자식1의 태그명: 자식1의 텍스트, ...}, ...] (list(dict(string:string)))
             children 값을 주지 않았을 때, [{태그명: 텍스트}, ...] (list(dict(string:string)))
    """
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html, 'html.parser')
    tags = soup.find_all(tag, attrs=attrs)
    if len(children) != 0:
        return list(map(lambda x: {childTag: x.find(childTag).text for childTag in children}, tags))
    else:
        return list(map(lambda x: {tag: x.text}, tags))


if __name__ == '__main__':
    # 전체 결과를 저장할 배열
    result = []

    # sido1의 데이터를 가져오기 위해 xml data parsing
    sido1List = xmlDataParsing(kyochonLocationDataUrl(), 'sidonm')

    for idx1, sido1 in enumerate(sido1List):
        # 시/도별 결과 데이터를 저장할 배열
        sido1Result = []

        # sido2의 데이터를 가져오기 위해 url을 찾고, xml data parsing
        location_en = translateLocation(sido1)
        locationDataUrl = kyochonLocationDataUrl(location_en)
        sido2List = xmlDataParsing(locationDataUrl, "sigungunm")

        for idx2, sido2 in enumerate(sido2List):
            # 시/도, 군/구 데이터는 1번부터 시작하므로 각각 +1을 하여 url 생성
            storeItemsUrl = kyochonUrl(idx1 + 1, idx2 + 1)

            # 가맹점들을 찾기 위해 store_item클래스를 가진 span태그의 strong과 em태그의 자식들을 parsing
            storeItems = htmlParsing(storeItemsUrl, 'span', {'class': 'store_item'}, ['strong', 'em'])

            # 주소의 데이터를 처리하고, [가맹점 이름, 시/도, 군/구, 주소] 형식으로 배열을 변경
            storeItems = list(map(lambda x: [x['strong'], sido1, sido2, x['em'].strip().split('\r')[0]], storeItems))
            sido1Result += storeItems
        result += sido1Result

    # 결과를 csv 파일로 저장
    kyochon_tbl = pd.DataFrame(result, columns=['store', 'sido', 'gungu', 'store_address'])
    kyochon_tbl.to_csv('./kyochon_store_items.csv', encoding="cp949", mode="w", index=True)
