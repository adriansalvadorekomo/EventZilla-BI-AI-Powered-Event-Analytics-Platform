FROM node:20 AS build

WORKDIR /app
COPY package*.json /app/
RUN npm ci --legacy-peer-deps

COPY . /app
RUN npm run build -- --configuration production

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/eventzilla-front/browser /usr/share/nginx/html

EXPOSE 80
