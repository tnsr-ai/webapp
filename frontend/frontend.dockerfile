FROM node:21.7-alpine3.19

LABEL maintainer="Amit Bera <amitalokbera@gmail.com>"

COPY . /app

WORKDIR /app 

RUN npm install

RUN npm run build 

EXPOSE 3000

CMD [ "npm", "start" ]