import sys
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import time
from SSHManager import SSHManager
import os

local_path = "/home/ec2-user/daily_crawling/"
remote_path = "/home/centos/result_from_servers/"


def get_page_url(page_num, user_code, maker_code, cityCode):
    """
    >>>input 페이지 번호, 차량종류번호, 브랜드번호, 중고차판매지역번호
    >>>output 쿼리로 필터링 적용된 url
    """
    url = (
        "https://www.kbchachacha.com/public/search/list.empty?page="
        + str(page_num)
        + "&sort=-orderDate&useCode="
        + str(user_code)
        + "&makerCode="
        + str(maker_code)
        + "&cityCode="
        + str(cityCode)
        + "&_pageSize=3&pageSize=4"
    )
    return url


def get_car_urls(user_code):
    """
    >>> 3개의 필터로 각각 필터링한  url에 접근해서 각 페이지의 차량 url 수집
    """
    car_url_list = list()
    maker_codes = [
        "101",
        "102",
        "103",
        "105",
        "104",
        "189",
        "106",
        "107",
        "108",
        "109",
        "112",
        "160",
        "116",
        "122",
        "133",
        "115",
        "110",
        "170",
        "153",
        "114",
        "128",
        "123",
        "124",
        "117",
        "136",
        "121",
        "137",
        "146",
        "118",
        "142",
        "113",
        "138",
        "130",
        "180",
        "166",
        "125",
        "150",
        "148",
        "119",
        "156",
        "129",
        "140",
        "111",
        "190",
        "191",
        "132",
        "152",
        "161",
        "157",
        "134",
        "181",
        "141",
        "154",
        "126",
        "173",
        "139",
        "169",
        "143",
        "167",
        "127",
        "192",
    ]
    cityCodes = [
        "021012",
        "021009",
        "021007",
        "021006",
        "021005",
        "021008",
        "021011",
        "021002",
        "021001",
        "021003",
        "021004",
        "021013",
        "021014",
        "021016",
        "021017",
        "021015",
    ]
    for maker_code in maker_codes:
        for cityCode in cityCodes:
            print(maker_code)
            page_num = 0
            while True:
                page_num += 1
                url = get_page_url(page_num, user_code, maker_code, cityCode)
                time.sleep(0.3)
                response = requests.get(url)
                soup = bs(response.text, "html.parser")
                ####종료 조건 ###############
                # if page_num == 3:
                #     break
                if soup.find("span", {"class": "txt"}) is not None:
                    print("종료")
                    break
                if soup.find("h2") is None:
                    print("종료, blocked")
                    break
                car_list = soup.find_all("div", {"class": "area"})

                for car in car_list:
                    items = car.find_all("a")
                    for item in items:
                        if "detail.kbc?carSeq" in item["href"]:
                            item_href = item["href"]
                            price = car.find("strong", {"class", "pay"}).text.strip()
                            if "https://" in item_href:
                                car_url_list.append(item_href + "///" + price)
                            else:
                                car_url_list.append(
                                    "https://www.kbchachacha.com"
                                    + item_href
                                    + "///"
                                    + price
                                )

    return car_url_list


if __name__ == "__main__":
    server_num = int(sys.argv[1])
    s_time = time.time()
    car_url_list = list()
    user_codes = [
        ["002001", "002007"],
        ["002005"],
        ["002004"],
        ["002003", "002006", "002010"],
        ["002008"],
        ["002002", "002009", "002011", "002012"],
    ]
    df = pd.DataFrame(columns=["url"])
    for user_code in user_codes[server_num - 1]:
        car_url_list = car_url_list + get_car_urls(user_code)
        print(len(car_url_list))
    car_url_list = list(set(car_url_list))
    print(len(car_url_list))
    df["url"] = car_url_list
    df.to_csv(
        local_path + "filtered_url_{server_num}.csv".format(server_num=server_num)
    )
    print("총 실행시간", time.time() - s_time)
    ssh_manager = SSHManager()
    for _ in range(10):
        try:
            ssh_manager.create_ssh_client(
                "133.186.150.193",
                "centos",
                "gozjRjwu~!",
                key_filename=local_path + "shopify.pem",
            )  # 세션생성
            break
        except Exception as e:
            print(f"error : {e}")
            time.sleep(10)

    ssh_manager.send_file(
        local_path + "filtered_url_{server_num}.csv".format(server_num=server_num),
        remote_path + "filtered_url_{server_num}.csv".format(server_num=server_num),
    )  # 파일전송
    os.remove(
        local_path + "filtered_url_{server_num}.csv".format(server_num=server_num)
    )
    ssh_manager.close_ssh_client()  # 세션종료