# Healthcare App Backend

A comprehensive Django-based backend for a healthcare application, providing APIs for patients, doctors, clinics, appointments, and more.

## Features

- **User Authentication**: Secure user management with different roles (patient, doctor, admin)
- **Patient Management**: Patient profiles, medical history, medications, etc.
- **Doctor Management**: Doctor profiles, qualifications, specializations, etc.
- **Clinic Management**: Clinic information, business hours, reviews, etc.
- **Appointment Scheduling**: Book, reschedule, and cancel appointments
- **Doctor Scheduling**: Doctor availability, time slots, schedules, exceptions
- **Notifications**: Email, SMS, and push notifications for appointments and more
- **Reviews and Feedback**: Patient reviews and feedback for doctors and clinics
- **Medical Records**: Store and access medical records securely

## Project Structure

The project is organized into several Django apps, each handling a specific aspect of the healthcare system:

- **accounts**: User authentication and user profiles
- **patients**: Patient information and medical history
- **doctors**: Doctor profiles, qualifications, and specializations
- **clinics**: Clinic information, business hours, and reviews
- **appointments**: Appointment management, medical records, and reminders
- **schedules**: Doctor schedules, availability, and time slots
- **api**: API versioning and routing

## Tech Stack

- **Django**: Web framework for building the application
- **Django REST Framework**: For building RESTful APIs
- **PostgreSQL**: Database for storing application data
- **Redis**: For caching and task queue
- **Celery**: For handling asynchronous tasks
- **Daphne/Channels**: For WebSocket support
- **Docker**: For containerization and deployment

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/healthcare-backend.git
   cd healthcare-backend
   ```

2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

3. Update the `.env` file with your settings

4. Start the application with Docker Compose:
   ```bash
   docker-compose up -d
   ```

5. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. Access the application:
   - Admin interface: http://localhost/admin/
   - API documentation: http://localhost/docs/

### Running for Development

For development, use the development environment:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

## API Documentation

The API documentation is available at `/docs/` when the server is running. 

## Testing

Run the tests using:

```bash
docker-compose exec web pytest
```

For coverage:

```bash
docker-compose exec web pytest --cov=.
```

## Deployment

For production deployment, make sure to update the `.env` file with appropriate settings:

1. Set `DEBUG=False`
2. Set a strong `SECRET_KEY`
3. Update `ALLOWED_HOSTS` with your domain
4. Configure secure database credentials
5. Set up proper email settings
6. Configure CORS settings for your frontend domain

Then deploy using:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Database Schema

The application uses a relational database with the following main tables:

- **Users**: Authentication and user information
- **Patients**: Patient-specific data linked to users
- **Doctors**: Doctor-specific data linked to users
- **Clinics**: Information about healthcare facilities
- **Appointments**: Scheduling information for patient-doctor meetings
- **Schedules**: Doctor availability and working hours
- **TimeSlots**: Specific time slots for appointments
- **MedicalRecords**: Patient medical information from appointments

## Development Guidelines

### Code Style

This project follows PEP 8 guidelines for Python code. We use:

- Black for code formatting
- Flake8 for linting
- isort for import sorting

```bash
# Format code
docker-compose exec web black .

# Check linting
docker-compose exec web flake8

# Sort imports
docker-compose exec web isort .
```

### Adding New Features

1. Create a new branch for your feature
2. Implement the feature with appropriate tests
3. Ensure all tests pass
4. Submit a pull request

### Creating a New App

To create a new Django app within the project:

```bash
docker-compose exec web python manage.py startapp appname
```

Then add the app to `INSTALLED_APPS` in settings.py and create necessary models, views, serializers, etc.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- Moataz Kayad Hamdy Noaman - Initial work - [Moataz Noaman](https://github.com/MoatazNoaman2001)

## Acknowledgments

- Django and Django REST Framework documentation
- The open-source community for inspiration and tools