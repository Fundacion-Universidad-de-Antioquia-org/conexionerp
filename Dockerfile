# Usar una imagen base de Python
FROM python:3.11.9-alpine3.19

# Ajustar la configuración de Python
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=conexionerp.settings

# 1) Instalar dependencias de compilación y mysqlclient-dev
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      default-libmysqlclient-dev \
      pkg-config \
 && rm -rf /var/lib/apt/lists/*

# Configurar el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apk update && apk add --no-cache gcc musl-dev python3-dev libffi-dev postgresql-dev
RUN pip install --upgrade pip

# Copiar el archivo de requisitos y instalar dependencias de Python
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Gunicorn
RUN pip install gunicorn

# Copiar el resto del proyecto
COPY . .

# Recopilar archivos estáticos
RUN mkdir -p /app/staticfiles
RUN python manage.py collectstatic --noinput


# Exponer el puerto en el que Gunicorn va a correr
EXPOSE 443

# Comando para ejecutar la aplicación usando Gunicorn en el puerto 8000
#CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ]
CMD ["gunicorn", "conexionerp.wsgi:application", "--bind", "0.0.0.0:443", "--workers", "3"]


