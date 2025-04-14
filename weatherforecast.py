# 3 hour forecast for 5 days API를 사용할거야

import requests
import json
import schedule
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from currentweather import WeatherData
from models import Session, WeatherForecast, map_weather_condition


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

def interpolate_hourly_data(forecast_list, city_name):
    hourly_data = []
    
    for i in range(len(forecast_list) - 1):
        current = forecast_list[i]
        next_data = forecast_list[i + 1]
        
        current_time = datetime.fromtimestamp(current['dt'])
        next_time = datetime.fromtimestamp(next_data['dt'])
        
        # 현재 시점 데이터 추가
        hourly_data.append({
            'time': current_time,
            'temp': current['main']['temp'],
            'temp_min': current['main']['temp_min'],
            'temp_max': current['main']['temp_max'],
            'humidity': current['main']['humidity'],
            'wind_speed': current['wind']['speed'],
            'description': current['weather'][0]['description'],
            'location_name': city_name
        })
        
        # 중간 시간대 보간
        for hour in range(1, 3):  # 3시간 간격의 중간 1시간, 2시간 시점 보간
            weight = hour / 3.0  # 0.33, 0.66
            interpolated_time = current_time + timedelta(hours=hour)
            
            if interpolated_time >= next_time:
                break
                
            interpolated_data = {
                'time': interpolated_time,
                'temp': current['main']['temp'] * (1-weight) + next_data['main']['temp'] * weight,
                'temp_min': current['main']['temp_min'] * (1-weight) + next_data['main']['temp_min'] * weight,
                'temp_max': current['main']['temp_max'] * (1-weight) + next_data['main']['temp_max'] * weight,
                'humidity': int(current['main']['humidity'] * (1-weight) + next_data['main']['humidity'] * weight),
                'wind_speed': current['wind']['speed'] * (1-weight) + next_data['wind']['speed'] * weight,
                'description': current['weather'][0]['description'],
                'location_name': city_name
            }
            hourly_data.append(interpolated_data)
    
    return hourly_data

def get_current_weather_data(session):
    try:
        # 가장 최근의 현재 날씨 데이터 조회
        current_weather = session.query(WeatherData).order_by(
            WeatherData.weather_date.desc(),
            WeatherData.weather_time.desc()
        ).first()
        
        if current_weather:
            try:
                current_time = datetime.combine(
                    current_weather.weather_date,
                    datetime.strptime(current_weather.weather_time, '%H:%M:%S').time()
                )
            except (ValueError, TypeError):
                print("날씨 시간 데이터 형식 오류")
                return None
                
            return {
                'time': current_time,
                'temp': float(current_weather.current_temp),
                'temp_min': float(current_weather.min_temp),
                'temp_max': float(current_weather.max_temp),
                'humidity': current_weather.current_humidity,
                'wind_speed': current_weather.current_wind_speed,
                'description': current_weather.weather_condition,
                'location_name': current_weather.location_name
            }
        else:
            print("현재 날씨 데이터가 없어 예보 데이터만 처리합니다.")
            return None
    except Exception as e:
        print(f"현재 날씨 데이터 조회 중 오류 발생: {str(e)}")
        return None

def interpolate_with_current_data(current_data, forecast_list, city_name):
    hourly_data = []
    
    if not current_data:
        print("현재 날씨 데이터가 없어 예보 데이터만 처리합니다.")
        return interpolate_hourly_data(forecast_list, city_name)
    
    current_time = current_data['time']
    first_forecast = forecast_list[0]
    first_forecast_time = datetime.fromtimestamp(first_forecast['dt'])
    
    print(f"현재 시각: {current_time}")
    print(f"첫 예보 시각: {first_forecast_time}")
    
    # 현재 시점 데이터 추가
    hourly_data.append({
        'time': current_time,
        'temp': current_data['temp'],
        'temp_min': current_data['temp_min'],
        'temp_max': current_data['temp_max'],
        'humidity': current_data['humidity'],
        'wind_speed': current_data['wind_speed'],
        'description': first_forecast['weather'][0]['description'],
        'location_name': city_name
    })
    print("현재 시점 데이터 추가 완료")
    
    # 현재 시점과 첫 번째 예보 사이 보간
    hours_diff = (first_forecast_time - current_time).total_seconds() / 3600
    print(f"시간 차이: {hours_diff}시간")
    
    if hours_diff > 0:
        next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        print(f"다음 정시: {next_hour}")
        
        current_hour = next_hour
        while current_hour < first_forecast_time:
            progress = (current_hour - current_time).total_seconds() / (first_forecast_time - current_time).total_seconds()
            print(f"보간 시각: {current_hour}, 진행률: {progress}")
            
            interpolated_data = {
                'time': current_hour,
                'temp': current_data['temp'] * (1-progress) + first_forecast['main']['temp'] * progress,
                'temp_min': current_data['temp_min'] * (1-progress) + first_forecast['main']['temp_min'] * progress,
                'temp_max': current_data['temp_max'] * (1-progress) + first_forecast['main']['temp_max'] * progress,
                'humidity': int(current_data['humidity'] * (1-progress) + first_forecast['main']['humidity'] * progress),
                'wind_speed': current_data['wind_speed'] * (1-progress) + first_forecast['wind']['speed'] * progress,
                'description': first_forecast['weather'][0]['description'],
                'location_name': city_name
            }
            hourly_data.append(interpolated_data)
            current_hour += timedelta(hours=1)
            print(f"보간 데이터 추가: {current_hour}")
    
    # 나머지 예보 데이터 보간
    forecast_data = interpolate_hourly_data(forecast_list, city_name)
    print(f"예보 데이터 개수: {len(forecast_data)}")
    hourly_data.extend(forecast_data)
    
    print(f"총 생성된 데이터 개수: {len(hourly_data)}")
    if hourly_data:
        print(f"첫 데이터: {hourly_data[0]['time']}")
        print(f"마지막 데이터: {hourly_data[-1]['time']}")
    return hourly_data

def get_weather_forecast():
    lat = 37.5683
    lon = 126.9778
    api_key = "a9f63a12503b84b4885a74632dab5ab3"
    
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
    print(f"API URL: {url}")
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"API 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            session = Session()
            
            try:
                # 위치 정보 구성
                location_parts = []
                if "city" in data:
                    if "name" in data["city"]:
                        location_parts.append(data["city"]["name"])
                    if "country" in data["city"] and data["city"]["country"] == "KR":
                        location_parts.append("대한민국")
                
                location_name = " ".join(location_parts) if location_parts else "서울"
                print(f"위치 정보: {location_name}")
                
                # 현재 날씨 데이터 가져오기 (없어도 계속 진행)
                current_data = get_current_weather_data(session)
                if current_data:
                    print(f"현재 날씨 데이터: {current_data}")
                else:
                    print("현재 날씨 데이터를 찾을 수 없습니다.")
                
                # API 응답 데이터 확인
                if 'list' in data and len(data['list']) > 0:
                    print(f"예보 데이터 개수: {len(data['list'])}")
                else:
                    print("예보 데이터가 없습니다.")
                    return
                
                # 현재 데이터와 예보 데이터 사이 보간 수행
                hourly_data = interpolate_with_current_data(current_data, data['list'], location_name)
                print(f"생성된 시간별 데이터 개수: {len(hourly_data)}")

                current_time = datetime.now()
                
                for hour_data in hourly_data:
                    dt = hour_data['time']
                    
                    existing_data = session.query(WeatherForecast).filter(
                        WeatherForecast.forecast_date == dt.strftime('%Y-%m-%d'),
                        WeatherForecast.forecast_time == dt.strftime('%H:%M:%S')
                    ).first()
                    
                    weather_data = WeatherForecast(
                        forecast_date=dt.strftime('%Y-%m-%d'),
                        forecast_time=dt.strftime('%H:%M:%S'),
                        forecast_temp=hour_data['temp'],
                        forecast_temp_min=hour_data['temp_min'],
                        forecast_temp_max=hour_data['temp_max'],
                        forecast_humidity=hour_data['humidity'],
                        forecast_wind_speed=hour_data['wind_speed'],
                        forecast_weather_condition=map_weather_condition(
                            hour_data['description'],
                            hour_data['temp']
                        ),
                        forecast_description=hour_data['description'],
                        forecast_latitude=lat,
                        forecast_longitude=lon,
                        forecast_location_name=location_name
                    )
                    
                    if existing_data:
                        for key, value in weather_data.__dict__.items():
                            if key != '_sa_instance_state' and key != 'id':
                                setattr(existing_data, key, value)
                    else:
                        session.add(weather_data)
                
                # 48시간 이전의 오래된 데이터 삭제
                old_data_cutoff = current_time - timedelta(hours=48)
                old_data_cutoff_str = old_data_cutoff.strftime('%Y-%m-%d %H:%M:%S')
                
                session.query(WeatherForecast).filter(
                    func.concat(WeatherForecast.forecast_date, ' ', WeatherForecast.forecast_time) < old_data_cutoff_str
                ).delete(synchronize_session=False)
                
                # 변경사항 커밋
                session.commit()
                print(f"{datetime.now()}: 날씨 예보 데이터가 성공적으로 업데이트되었습니다.")
                
            except Exception as e:
                print(f"데이터 처리 중 오류 발생: {str(e)}")
                session.rollback()
            finally:
                session.close()
                
        else:
            print(f"API 호출 실패: {data.get('message', '알 수 없는 에러')}")
            
    except Exception as e:
        print(f"API 요청 중 오류 발생: {str(e)}")

# 3시간 간격으로 실행 스케줄 설정
schedule.every().day.at("00:00").do(get_weather_forecast)
schedule.every().day.at("03:00").do(get_weather_forecast)
schedule.every().day.at("06:00").do(get_weather_forecast)
schedule.every().day.at("09:00").do(get_weather_forecast)
schedule.every().day.at("12:00").do(get_weather_forecast)
schedule.every().day.at("15:00").do(get_weather_forecast)
schedule.every().day.at("18:00").do(get_weather_forecast)
schedule.every().day.at("21:00").do(get_weather_forecast)

if __name__ == "__main__":
    print("날씨 예보 수집 프로그램이 시작되었습니다.")
    print("현재 시각:", datetime.now())
    
    # 프로그램 시작시 즉시 첫 데이터 수집
    try:
        get_weather_forecast()
    except Exception as e:
        print(f"초기 데이터 수집 중 오류 발생: {str(e)}")
    
    print("스케줄러가 시작되었습니다. 3시간 간격으로 데이터를 수집합니다.")
    
    # 스케줄러 실행
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            print(f"스케줄러 실행 중 오류 발생: {str(e)}")
            time.sleep(60)
            continue


