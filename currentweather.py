import requests
import json
import schedule
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Session, WeatherData, map_weather_condition


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
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(String(100))
    weather_date = Column(DateTime)
    weather_time = Column(String(50))
    current_temp = Column(Integer)
    current_humidity = Column(Integer, nullable=False)
    current_wind_speed = Column(Float, nullable=False)

# DB 세션 생성
Session = sessionmaker(bind=engine)

def get_weather_data():
    # 좀 더 구체적인 위치 정보로 API 요청
    lat = 37.5683  # 서울시청 위치
    lon = 126.9778
    apikey = "a9f63a12503b84b4885a74632dab5ab3"
    lang = "ko"
    
    api = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={apikey}&lang={lang}&units=metric"
    
    try:
        result = requests.get(api)
        data = json.loads(result.text)
        
        if result.status_code == 200:
            current_datetime = datetime.now()
            
            # 위치 정보 구성
            location_parts = []
            if "name" in data:
                location_parts.append(data["name"])
            if "sys" in data and "country" in data["sys"]:
                if data["sys"]["country"] == "KR":
                    location_parts.append("대한민국")
            
            location_name = " ".join(location_parts)
            
            session = Session()
            
            try:
                # 가장 최근 데이터 하나만 남기고 모두 삭제
                latest_data = session.query(WeatherData).order_by(
                    WeatherData.weather_date.desc(),
                    WeatherData.weather_time.desc()
                ).first()
                
                if latest_data:
                    # 최신 데이터보다 오래된 데이터 모두 삭제
                    session.query(WeatherData).filter(
                        (WeatherData.weather_date < latest_data.weather_date) |
                        ((WeatherData.weather_date == latest_data.weather_date) & 
                         (WeatherData.weather_time < latest_data.weather_time))
                    ).delete(synchronize_session=False)
                
                # 새로운 데이터 추가
                weather_data = WeatherData(
                    min_temp=int(data["main"]["temp_min"]),
                    max_temp=int(data["main"]["temp_max"]),
                    weather_condition=map_weather_condition(data["weather"][0]["description"], data["main"]["temp"]),
                    latitude=float(data["coord"]["lat"]),
                    longitude=float(data["coord"]["lon"]),
                    location_name=location_name,
                    weather_date=current_datetime.date(),
                    weather_time=current_datetime.strftime("%H:%M:%S"),
                    current_temp=int(data["main"]["temp"]),
                    current_humidity=data["main"]["humidity"],
                    current_wind_speed=data["wind"]["speed"]
                )
                
                session.add(weather_data)
                session.commit()
                
                print(f"{datetime.now()}: 날씨 데이터가 성공적으로 업데이트되었습니다.")
                print(f"위치: {location_name}")
                print(f"위도: {data['coord']['lat']}, 경도: {data['coord']['lon']}")
                
            except Exception as e:
                print(f"데이터베이스 작업 중 오류 발생: {str(e)}")
                session.rollback()
            finally:
                session.close()
            
        else:
            print(f"API 호출 실패: {data.get('message', '알 수 없는 에러')}")
            
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    print("현재 날씨 수집 프로그램이 시작되었습니다.")
    print("현재 시각:", datetime.now())
    
    # 1시간마다 데이터 수집
    schedule.every(1).hours.do(get_weather_data)
    
    # 프로그램 시작시 즉시 첫 데이터 수집
    try:
        get_weather_data()
    except Exception as e:
        print(f"초기 데이터 수집 중 오류 발생: {str(e)}")
    
    print("스케줄러가 시작되었습니다. 1시간 간격으로 데이터를 수집합니다.")
    
    # 스케줄러 실행
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            print(f"스케줄러 실행 중 오류 발생: {str(e)}")
            time.sleep(60)
            continue
