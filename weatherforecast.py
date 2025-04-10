# 3 hour forecast for 5 days API를 사용할거야

import requests
import json
import schedule
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# DB 연결 설정
DATABASE_URL = "mysql+pymysql://root:Lee289473007216!@localhost:3306/weatherfit?charset=utf8mb4"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# WeatherForecast 모델 정의
class WeatherForecast(Base):
    __tablename__ = 'weather_forecast'
    
    id = Column(Integer, primary_key=True)
    forecast_date = Column(String(10), nullable=False)
    forecast_time = Column(String(8), nullable=False)
    temp = Column(Float, nullable=False)
    temp_min = Column(Float, nullable=False)
    temp_max = Column(Float, nullable=False)
    humidity = Column(Integer, nullable=False)
    wind_speed = Column(Float, nullable=False)
    weather_condition = Column(Enum('HOT', 'WARM', 'RAIN', 'COLD', 'CHILL', 'SNOW', name='weather_condition'))
    description = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

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

def get_weather_forecast():
    city = "Seoul"
    api_key = "a9f63a12503b84b4885a74632dab5ab3"
    lang = "ko"
    
    # API 호출
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=kr"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            session = sessionmaker(bind=engine)()
            
            for forecast in data['list']:  # 여기서 40개의 데이터를 순회
                dt = datetime.fromtimestamp(forecast['dt'])
                
                weather_data = WeatherForecast(
                    forecast_date=dt.strftime('%Y-%m-%d'),
                    forecast_time=dt.strftime('%H:%M:%S'),
                    temp=forecast['main']['temp'],
                    temp_min=forecast['main']['temp_min'],
                    temp_max=forecast['main']['temp_max'],
                    humidity=forecast['main']['humidity'],
                    wind_speed=forecast['wind']['speed'],
                    weather_condition=map_weather_condition(
                        forecast['weather'][0]['description'],
                        forecast['main']['temp']
                    ),
                    description=forecast['weather'][0]['description'],
                    latitude=data['city']['coord']['lat'],
                    longitude=data['city']['coord']['lon']
                )
                
                session.add(weather_data)
            
            session.commit()
            session.close()
            print(f"{datetime.now()}: 날씨 예보 데이터가 성공적으로 저장되었습니다.")
            
        else:
            print(f"에러 발생: {data.get('message', '알 수 없는 에러')}")
            
    except Exception as e:
        print(f"데이터 저장 중 오류 발생: {str(e)}")

# 매일 자정에 데이터 수집
schedule.every().day.at("00:00").do(get_weather_forecast)

# 프로그램 시작시 즉시 첫 데이터 수집
get_weather_forecast()

# 스케줄러 실행
while True:
    schedule.run_pending()
    time.sleep(1)


