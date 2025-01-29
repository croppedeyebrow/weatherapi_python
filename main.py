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
    print(data)

	 

