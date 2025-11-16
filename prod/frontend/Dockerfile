# Prod Frontend Dockerfile

# 베이스 이미지
FROM nginx:stable-alpine

# nginx.conf 파일을 이미지의 설정 폴더로 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 애플리케이션 코드를 nginx의 기본 서빙 폴더로 복사
COPY . /usr/share/nginx/html

# 포트 
EXPOSE 80

# 컨테이너 실행
# Fargate는 Scale to Zero를 지원하지 않아서 컨테이너 최소 1개는 가동중이어야 함
CMD ["nginx", "-g", "daemon off;"]