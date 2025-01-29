import requests
import json

city = "Seoul"
apikey = ""
lang = "ko"

api = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={apikey}&lang={lang}&units=metric"

result = requests.get(api)
data = json.loads(result.text)

if result.status_code != 200:
    print(f"에러 발생: {data.get('message', '알 수 없는 에러')}")
else:
    print(data["name"],"의 날씨입니다.")
    # 자세한 날씨 : weather - description
    print("날씨는 ",data["weather"][0]["description"],"입니다.")
    # 현재 온도 : main - temp
    print("현재 온도는 ",data["main"]["temp"],"입니다.")
    # 체감 온도 : main - feels_like
    print("하지만 체감 온도는 ",data["main"]["feels_like"],"입니다.")
    # 최저 기온 : main - temp_min
    print("최저 기온은 ",data["main"]["temp_min"],"입니다.")
    # 최고 기온 : main - temp_max
    print("최고 기온은 ",data["main"]["temp_max"],"입니다.")
    # 습도 : main - humidity
    print("습도는 ",data["main"]["humidity"],"입니다.")
    # 기압 : main - pressure
    print("기압은 ",data["main"]["pressure"],"입니다.")
    # 풍향 : wind - deg
    print("풍향은 ",data["wind"]["deg"],"입니다.")
    # 풍속 : wind - speed
    print("풍속은 ",data["wind"]["speed"],"입니다.")

	 
# 1시간 마다 실시간 반영
# 가져온 데이터 DB에 저장하고, SPringBoot에서 콜하면 될 듯.
