# Use the lightweight Nginx Alpine image
FROM docker.arvancloud.ir/nginx:alpine

# Copy the index.html file to the default Nginx public directory
# Note: Ensure index.html is in the same directory as this Dockerfile
COPY index.html /usr/share/nginx/html/index.html

# Expose port 80 for the web server
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]