FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ENV NEXT_PUBLIC_API_URL=https://shop-agent-backend-c3lyao3wuq-uc.a.run.app

RUN npm run build

EXPOSE 3000
CMD ["sh", "-c", "npm start -- -p ${PORT:-8080}"]
