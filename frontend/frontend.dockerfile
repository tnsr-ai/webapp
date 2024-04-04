FROM node:lts

LABEL maintainer="Amit Bera <amitalokbera@gmail.com>"

WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the code
COPY . .

# Build the application only if package.json was changed
RUN npm run build

EXPOSE 3000

CMD [ "npm", "run", "start"]
