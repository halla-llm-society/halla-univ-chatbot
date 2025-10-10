# Prod Frontend Dockerfile

# 베이스 이미지
FROM nginx:stable-alpine

# 작업 디렉토리 설정
WORKDIR /usr/share/nginx/html

# 애플리케이션 코드 복사
COPY . .

# 포트 
EXPOSE 80

# 컨테이너 실행
# Fargate는 Scale to Zero를 지원하지 않아서 컨테이너 최소 1개는 가동중이어야 함
CMD ["nginx", "-g", "daemon off;"]