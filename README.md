# WeatherFit 날씨 데이터 수집 시스템

## 프로젝트 개요

WeatherFit은 실시간 날씨 데이터와 일기 예보를 수집하여 데이터베이스에 저장하는 시스템입니다. OpenWeather API를 활용하여 현재 날씨와 5일간의 3시간 단위 예보 데이터를 수집하고, 선형 보간법을 통해 시간별 상세 데이터를 생성합니다.

## 시스템 아키텍처

### 1. 현재 날씨 수집 (`currentweather.py`)

- **데이터 소스**: OpenWeather Current Weather API
- **수집 주기**: 1시간
- **위치**: 서울 (위도: 37.5683, 경도: 126.9778)
- **저장 테이블**: `weather`

#### 데이터 모델 (WeatherData)

```python
class WeatherData(Base):
    __tablename__ = 'weather'
    Weather_range_Id = Column(Integer, primary_key=True)
    min_temp = Column(Integer)
    max_temp = Column(Integer)
    weather_condition = Column(Enum('HOT', 'WARM', 'MID', 'COLD', 'CHILL', 'RAIN', 'SNOW'))
    latitude = Column(Integer)
    longitude = Column(Integer)
    weather_date = Column(DateTime)
    weather_time = Column(String(50))
    current_temp = Column(Integer)
    current_humidity = Column(Integer, nullable=False)
    current_wind_speed = Column(Float, nullable=False)
```

### 2. 날씨 예보 수집 (`weatherforecast.py`)

- **데이터 소스**: OpenWeather 5-day/3-hour Forecast API
- **수집 주기**: 3시간 (00:00, 03:00, 06:00, ...)
- **데이터 범위**: 5일간 3시간 단위 예보
- **저장 테이블**: `weather_forecast`

#### 데이터 모델 (WeatherForecast)

```python
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
    forecast_weather_condition = Column(Enum('HOT', 'WARM', 'RAIN', 'COLD', 'CHILL', 'SNOW'))
    forecast_description = Column(String(100), nullable=False)
    forecast_latitude = Column(Float, nullable=False)
    forecast_longitude = Column(Float, nullable=False)
```

## 핵심 기능

### 1. 날씨 상태 분류 (map_weather_condition)

```python
def map_weather_condition(api_condition, temp):
    # 강수 상태 우선 확인
    if any(keyword in api_condition.lower() for keyword in ['rain', 'shower', 'thunderstorm', '비']):
        return 'RAIN'
    elif any(keyword in api_condition.lower() for keyword in ['snow', '눈']):
        return 'SNOW'

    # 기온 기반 분류
    if temp >= 28: return 'HOT'
    elif temp >= 20: return 'WARM'
    elif temp >= 5: return 'COLD'
    else: return 'CHILL'
```

### 2. 시간별 데이터 보간 시스템

#### 2.1 현재-예보 데이터 보간 (interpolate_with_current_data)

- 현재 날씨와 첫 예보 시점 사이의 시간별 데이터 생성
- 선형 보간법을 사용하여 기온, 습도, 풍속 계산
- 정시 단위로 데이터 생성 (예: 16:00, 17:00)

#### 2.2 예보 데이터 보간 (interpolate_hourly_data)

- 3시간 간격 예보 데이터 사이의 시간별 데이터 생성
- 각 3시간 구간에 대해 1시간, 2시간 시점의 데이터 보간
- 날씨 설명은 구간 시작점의 값을 유지

### 3. 데이터 관리

- 48시간 이전의 과거 데이터 자동 삭제
- 중복 데이터 처리 (업데이트 방식)
- 데이터베이스 연결 풀 관리

## 데이터베이스 설정

```python
DATABASE_URL = "mysql+pymysql://[username]:[password]@localhost:3306/weatherfit?charset=utf8mb4"
engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)
```

## 설치 및 실행

### 필수 패키지

```bash
pip install sqlalchemy pymysql requests schedule
```

### 실행 방법

1. 데이터베이스 설정

   - MySQL 데이터베이스 생성
   - 테이블 스키마 적용
   - 접속 정보 설정

2. 프로그램 실행

```bash
# 터미널 1
python currentweather.py

# 터미널 2
python weatherforecast.py
```

## 주의사항

1. OpenWeather API 키 필요
2. MySQL 데이터베이스 사전 설정 필요
3. 두 프로그램 동시 실행 필요
4. 시스템 시간 정확도 중요

## 로깅

- 데이터 수집 성공/실패 로그
- 보간 데이터 생성 과정 로그
- 에러 발생 시 상세 메시지 출력

## 향후 개선사항

1. 로깅 시스템 강화
2. 예외 처리 개선
3. API 요청 실패 시 재시도 로직 추가
4. 데이터 정확도 검증 시스템 추가

---

## 개발 일지 및 문제 해결 기록

### 1. 데이터 수집 시스템 구축 과정

#### 1.1 기본 데이터 수집 구현

- OpenWeather API 연동 구현
- 현재 날씨와 예보 데이터 수집 기능 분리
- SQLAlchemy를 사용한 데이터베이스 모델 설계

#### 1.2 데이터 정규화 및 보간

- 3시간 단위 예보 데이터의 한계 발견
- 선형 보간법을 통한 시간별 데이터 생성 구현
- 현재 날씨와 예보 데이터 간 연속성 확보

### 2. 주요 문제 해결 과정

#### 2.1 데이터 연속성 문제

**문제**: 현재 날씨(16:15)와 첫 예보(18:00) 사이 데이터 공백 발생

```python
# 초기 접근 방식 (문제 있음)
hours_diff = int((first_forecast_time - current_time).total_seconds() / 3600)
# 17시 데이터가 생성되지 않는 문제 발생
```

**해결**:

```python
# 개선된 보간 로직
next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
while current_hour < first_forecast_time:
    progress = (current_hour - current_time).total_seconds() / (first_forecast_time - current_time).total_seconds()
    # 시간별 데이터 생성
```

#### 2.2 날씨 상태 분류 개선

**초기 버전**:

```python
def map_weather_condition(temp):
    if temp >= 28: return 'HOT'
    elif temp >= 20: return 'WARM'
    # ...
```

**개선된 버전**:

```python
def map_weather_condition(api_condition, temp):
    # 강수 상태 우선 확인
    if any(keyword in api_condition.lower() for keyword in ['rain', 'shower', 'thunderstorm', '비']):
        return 'RAIN'
    # ...
```

#### 2.3 데이터베이스 동시성 문제

- 연결 풀 설정 추가
- 세션 관리 개선
- 중복 데이터 처리 로직 구현

### 3. 성능 최적화 과정

#### 3.1 데이터 수집 주기 최적화

- 현재 날씨: 1시간 간격
- 예보 데이터: 3시간 간격
- 보간 데이터: 1시간 단위 생성

#### 3.2 데이터베이스 최적화

```python
engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)
```

### 4. 주요 학습 포인트

1. **시계열 데이터 처리**

   - 시간 기반 데이터의 연속성 확보
   - 선형 보간법을 통한 데이터 보완
   - 시간대 처리의 중요성

2. **데이터베이스 설계**

   - 테이블 정규화
   - 인덱스 설계
   - 연결 풀 관리

3. **API 통합**

   - 외부 API 응답 처리
   - 에러 핸들링
   - 데이터 정합성 확보

4. **코드 구조화**
   - 기능별 모듈 분리
   - 재사용 가능한 함수 설계
   - 유지보수 용이성 고려

### 5. 향후 개발 계획

1. **데이터 품질 개선**

   - 보간 알고리즘 정확도 향상
   - 이상치 탐지 시스템 추가
   - 데이터 검증 로직 강화

2. **시스템 안정성 강화**

   - 로깅 시스템 개선
   - 에러 복구 메커니즘 추가
   - 모니터링 시스템 구축

3. **기능 확장**
   - 추가 기상 정보 수집
   - 데이터 분석 기능 추가
   - API 서비스 구축

### 6. 주요 오류 해결 기록

#### 6.1 스케줄러 충돌 문제

**문제**:

- `weatherforecast.py`에서 `from currentweather import WeatherData`를 import하면서 `currentweather.py`의 스케줄러가 함께 실행되는 문제 발생
- 두 스케줄러가 동시에 실행되어 충돌 발생

**해결**:

- 공통 모델과 설정을 `models.py`로 분리
- 각 스크립트의 실행 로직을 `if __name__ == "__main__":`으로 분리
- 데이터베이스 모델과 유틸리티 함수를 공유하면서도 독립적으로 실행되도록 개선

```python
# models.py - 공통 모델 정의
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

class WeatherData(Base):
    __tablename__ = 'weather'
    # ... 모델 정의 ...

class WeatherForecast(Base):
    __tablename__ = 'weather_forecast'
    # ... 모델 정의 ...
```

#### 6.2 위치 정보 참조 오류

**문제**:

- OpenWeather API의 forecast 응답에서 `name` 필드를 직접 참조하려고 시도하여 오류 발생
- 예보 데이터의 각 시간별 데이터에는 도시 정보가 포함되어 있지 않음

**해결**:

- API 응답의 최상위 레벨에 있는 `city` 객체에서 위치 정보를 추출하도록 수정
- 위치 정보를 함수 매개변수로 전달하여 모든 보간 데이터에 일관되게 적용
- 국가 코드가 'KR'인 경우 "대한민국" 추가하여 위치 정보 상세화

```python
location_parts = []
if "city" in data:
    if "name" in data["city"]:
        location_parts.append(data["city"]["name"])
    if "country" in data["city"] and data["city"]["country"] == "KR":
        location_parts.append("대한민국")

location_name = " ".join(location_parts) if location_parts else "서울"
```

#### 6.3 데이터 연속성 및 세션 관리

**문제**:

- 데이터베이스 세션이 적절히 닫히지 않는 문제
- 예외 발생 시 세션 롤백이 누락되는 경우 발생
- 오래된 데이터가 계속 누적되는 문제

**해결**:

- 세션 관리를 try-finally 블록으로 개선
- 예외 처리 시 명시적 롤백 추가
- 48시간 이전의 오래된 데이터 자동 삭제 로직 구현
- 데이터베이스 연결 풀 설정 최적화

```python
try:
    # 데이터베이스 작업 수행
    session.commit()
except Exception as e:
    print(f"오류 발생: {str(e)}")
    session.rollback()
finally:
    session.close()
```

### 7. 시스템 모니터링 및 개선사항

#### 7.1 현재 구현된 모니터링

- API 요청 URL 및 응답 상태 코드 로깅
- 데이터 처리 단계별 상세 로그 출력
- 예외 발생 시 상세 에러 메시지 기록
- 데이터 수집 및 보간 결과 수량 확인
