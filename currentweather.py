import requests
import json
import schedule
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# pip install sqlalchemy
# pip install pymysql
# DB 설정
DATABASE_URL = "mysql+pymysql://root:Lee289473007216!@localhost:3306/weatherfit?charset=utf8mb4"
engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)
Base = declarative_base()

# 기존 테이블 구조에 맞게 모델 수정
class WeatherData(Base):
    __tablename__ = 'weather'  
    
    Weather_range_Id = Column(Integer, primary_key=True)
    min_temp = Column(Integer)
    max_temp = Column(Integer)
    weather_condition = Column(Enum('HOT', 'WARM', 'MID', 'COLD', 'CHILL', 'RAIN', 'SNOW', name='weather_condition_enum'))
    latitude = Column(Integer)
    longitude = Column(Integer)
    weather_date = Column(DateTime)
    weather_time = Column(String(50))
    current_temp = Column(Integer)
    current_humidity = Column(Integer, nullable=False)
    current_wind_speed = Column(Float, nullable=False)

# DB 세션 생성
Session = sessionmaker(bind=engine)

def map_weather_condition(api_condition, temp):
    # 비/눈 상태 우선 확인
    if any(keyword in api_condition.lower() for keyword in ['rain', 'shower', 'thunderstorm', '비']):
        return 'RAIN'
    elif any(keyword in api_condition.lower() for keyword in ['snow', '눈']):
        return 'SNOW'
    
    # 비/눈이 아닌 경우 기온 기준으로 판단
    if temp >= 28:
        return 'HOT'
    elif temp >= 20:
        return 'WARM'
    elif temp >= 5:
        return 'COLD'
    else:
        return 'CHILL'

def get_weather_data():
    city = "Seoul"
    apikey = "a9f63a12503b84b4885a74632dab5ab3"
    lang = "ko"
    
    api = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={apikey}&lang={lang}&units=metric"
    
    try:
        result = requests.get(api)
        data = json.loads(result.text)
        
        if result.status_code == 200:
            current_datetime = datetime.now()
            
            session = Session()
            weather_data = WeatherData(
                min_temp=int(data["main"]["temp_min"]),
                max_temp=int(data["main"]["temp_max"]),
                weather_condition=map_weather_condition(data["weather"][0]["description"], data["main"]["temp"]),
                latitude=int(data["coord"]["lat"]),
                longitude=int(data["coord"]["lon"]),
                weather_date=current_datetime.date(),
                weather_time=current_datetime.strftime("%H:%M:%S"),
                current_temp=int(data["main"]["temp"]),
                current_humidity=data["main"]["humidity"],
                current_wind_speed=data["wind"]["speed"]
            )
            
            session.add(weather_data)
            session.commit()
            session.close()
            
            print(f"{datetime.now()}: 날씨 데이터가 성공적으로 저장되었습니다.")
            
        else:
            print(f"에러 발생: {data.get('message', '알 수 없는 에러')}")
            
    except Exception as e:
        print(f"데이터 저장 중 오류 발생: {str(e)}")

# 1시간마다 데이터 수집
schedule.every(1).hours.do(get_weather_data)

# 프로그램 시작시 즉시 첫 데이터 수집
get_weather_data()

# 스케줄러 실행
while True:
    schedule.run_pending()
    time.sleep(1)
