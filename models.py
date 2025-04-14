from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# DB 설정
DATABASE_URL = "mysql+pymysql://root:Lee289473007216!@localhost:3306/weatherfit?charset=utf8mb4"
engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# 현재 날씨 데이터 모델
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

# 날씨 예보 데이터 모델
class WeatherForecast(Base):
    __tablename__ = 'weather_forecast'
    
    id = Column(Integer, primary_key=True)
    forecast_date = Column(String(10), nullable=False)
    forecast_time = Column(String(8), nullable=False)
    forecast_temp = Column(Float, nullable=False)
    forecast_temp_min = Column(Float, nullable=False)
    forecast_temp_max = Column(Float, nullable=False)
    forecast_humidity = Column(Integer, nullable=False)
    forecast_wind_speed = Column(Float, nullable=False)
    forecast_weather_condition = Column(Enum('HOT', 'WARM', 'RAIN', 'COLD', 'CHILL', 'SNOW', name='weather_condition'))
    forecast_description = Column(String(100), nullable=False)
    forecast_latitude = Column(Float, nullable=False)
    forecast_longitude = Column(Float, nullable=False)
    forecast_location_name = Column(String(100), nullable=False)

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