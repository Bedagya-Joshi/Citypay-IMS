# CityPay IMS Flask App

## Features

- User and admin authentication
- Item management and requests
- Admin approval workflow
- PostgreSQL backend

## Running with Docker

1. **Clone the repo and set up your `.env` file in `flask-app/`**  
   (see `.env.example` for format)

2. **Build and run with Docker Compose:**
   ```sh
   docker-compose up --build
   ```

3. **Access the app:**  
   [http://localhost:1451](http://localhost:1451)

## Environment Variables

Set these in your `.env` file:
```
SECRET_KEY=your_secret
DB_HOST=db
DB_NAME=citypay_ims
DB_USER=citypay_ims
DB_PASSWORD=C!typ@y123#
```

## Production

- Uses Gunicorn as WSGI server.
- Change `SECRET_KEY` before deploying!

---

## License

MIT