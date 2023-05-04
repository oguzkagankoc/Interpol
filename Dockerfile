# Use the official PostgreSQL image as the base image
FROM postgres:latest

# Set the environment variables POSTGRES_USER, POSTGRES_PW, and POSTGRES_DB
ENV POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=122333 \
    POSTGRES_DB=task

# Copy the SQL script to create the database table into the container's initialization directory
COPY create_table.sql /docker-entrypoint-initdb.d/

# Expose port 5432 to the host machine
EXPOSE 5432

# Set the host name/address to "localhost"
CMD ["postgres", "-h", "localhost"]
