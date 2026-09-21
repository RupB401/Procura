FROM node:20-alpine

WORKDIR /app

# The node modules are volume mounted in docker-compose for dev
# But we should copy package.json for standard builds
COPY package.json ./

RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
