# Web Application Project

This project is a web application developed as part of the software engineering course. It showcases the design and implementation skills in creating a web-based solution using Flask, a popular Python web framework. The application aims to provide a simple yet functional interface for users to interact with.

## Features

- Web interface built with Flask.
- Integration with a database using Flask-SQLAlchemy for data persistence.
- User-friendly interface designed with Jinja2 templates.

## Getting Started

These instructions will guide you through setting up and running the project locally using Docker. Ensure you have Docker installed on your system before proceeding.

### Prerequisites

- Docker
- Git (for cloning the repository)

### Installation

1. **Clone the repository**

   Open a terminal and run:

   ```bash
   git clone https://github.com/ichsandeep/PSEproject.git

### Navigate to the project directory

- Change into the project directory with:

   ```bash
    cd PSEproject

### Running the Application with Docker

- Build the Docker image

- In the project root directory, where the Dockerfile is located, build the Docker image using:

   ```bash
    docker-compose build

### Run the application

- Start the application with Docker Compose:

   ```bash
    docker-compose up

### Access the application

- The web application should now be running and accessible through your web browser at:
    
   ```arduino
    http://localhost:5000

- Adjust the port in the URL if you've configured it differently in your docker-compose.yml or Flask application.

### Contributing

- We welcome contributions to improve the project. Feel free to fork the repository, make changes, and submit pull requests. If you have any suggestions or encounter issues, please open an issue in the GitHub repository.

### License

- This project is licensed under the MIT License - see the LICENSE file in the repository for more details.

### Acknowledgments

- Thanks to the Flask team for creating such a powerful and easy-to-use web framework.
- Special thanks to all contributors and users of this project.


    "This README is now ready to be used. Just ensure that all instructions accurately reflect your project's setup and requirements. If your project uses a different port or has additional setup steps, remember to update those parts accordingly."

