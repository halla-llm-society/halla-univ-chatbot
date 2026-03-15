# ==========
# 1. 빌드
# ===========
FROM eclipse-temurin:21-jdk-jammy AS builder

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치에 필요한 파일 복사
COPY gradlew .
COPY gradle gradle
COPY build.gradle .
COPY settings.gradle .

# gradlew 실행 권한 부여
RUN chmod +x gradlew

# 의존성 다운로드
RUN ./gradlew dependencies --no-daemon

# 소스 코드, 설정 파일 복사
COPY src src
COPY config ./config

# 애플리케이션 빌드
RUN ./gradlew build -x test --no-daemon

# jar만 골라 app.jar로 이름 변경
RUN find build/libs -name "*.jar" ! -name "*plain.jar" -exec cp {} build/libs/app.jar \;

# ==========
# 2. 실행
# ==========
FROM eclipse-temurin:21-jre-jammy

# 작업 디렉토리 설정
WORKDIR /app

# 비루트 사용자 생성 및 권한 설정
RUN useradd -m user && chown -R user:user /app
USER user

# app.jar 파일 복사
COPY --from=builder /app/build/libs/app.jar app.jar

# 기본 포트 변경
ENV SERVER_PORT=8000

# 컨테이너 포트
EXPOSE 8000

# 컨테이너 실행
ENTRYPOINT ["java", "-Djava.security.egd=file:/dev/./urandom", "-jar", "app.jar"]
